"""Human-in-the-loop review and correction of extracted vendor facts."""
from __future__ import annotations

import re
from typing import Any

import streamlit as st

from app.pipeline import analyze_vendor
from app.schemas.vendor import VendorProposal
from app.ui.styles import page_header, section_heading
from app.utils.state import (
    get_all_chunks,
    get_groq_client,
    get_original_proposal,
    get_requirements,
    get_review_corrections,
    get_vendor_results,
    record_review_correction,
    set_recommendation,
    set_vendor_result,
)


REVIEW_FIELDS = (
    ("total_cost", "Total cost", "number", ("price", "cost", "budget", "pricing")),
    ("recurring_cost", "Recurring cost", "number", ("recurring", "monthly", "annual", "subscription")),
    ("implementation_timeline_weeks", "Implementation timeline (weeks)", "number", ("implementation", "timeline", "delivery", "weeks")),
    ("support_duration_months", "Support duration (months)", "number", ("support", "maintenance", "months")),
    ("sla", "Service level agreement", "text", ("sla", "service level", "response time")),
    ("api_integration_supported", "API integration supported", "boolean", ("api", "integration", "webhook")),
    ("iso27001_certified", "ISO 27001 certified", "boolean", ("iso 27001", "iso27001", "certification")),
    ("gdpr_compliant", "GDPR compliant", "boolean", ("gdpr", "privacy", "data protection")),
    ("certifications", "Certifications", "list", ("certification", "compliance", "iso", "soc 2")),
    ("exclusions", "Exclusions", "list", ("exclusion", "excluded", "not included", "out of scope")),
)


def render() -> None:
    page_header(
        "Review what the AI extracted.",
        "Validate proposal facts against their source evidence. Approved corrections immediately recalculate the existing evaluation.",
        "HUMAN REVIEW",
    )
    requirements = get_requirements()
    results = get_vendor_results()
    valid_results = {name: result for name, result in results.items() if not result.extraction_failed}
    if requirements is None:
        st.warning("Define requirements first on the **Create Analysis** page.")
        return
    if not valid_results:
        st.info("No successfully analyzed vendors are available for review yet.")
        return

    selected = st.selectbox("Select vendor to review", sorted(valid_results))
    result = valid_results[selected]
    original = get_original_proposal(selected) or result.proposal
    corrections = get_review_corrections(selected)

    st.markdown(
        f'<div class="review-summary"><span>REVIEW STATUS</span><b>{len(corrections)} approved correction(s)</b>'
        '<p>Original extraction is preserved. Your approved values are re-evaluated using the same deterministic rules.</p></div>',
        unsafe_allow_html=True,
    )
    section_heading("Extracted facts and source evidence")

    with st.form(f"review_form_{selected}"):
        values: dict[str, Any] = {}
        for field, label, kind, keywords in REVIEW_FIELDS:
            _render_field(
                selected, field, label, kind, original, result.proposal, keywords,
                result.source_documents, values,
            )
        submitted = st.form_submit_button("Apply approved corrections and recalculate", type="primary", width="stretch")

    if submitted:
        _apply_corrections(selected, result, values)


def _render_field(
    vendor: str,
    field: str,
    label: str,
    kind: str,
    original: VendorProposal,
    current: VendorProposal,
    keywords: tuple[str, ...],
    source_documents: list[str],
    values: dict[str, Any],
) -> None:
    original_value = getattr(original, field)
    current_value = getattr(current, field)
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown(f"**{label}**")
        st.caption(f"AI extracted: {_format_value(original_value)}")
        key = f"review_{vendor}_{field}"
        if kind == "number":
            values[field] = st.number_input(
                f"Approved {label}", min_value=0.0,
                value=float(current_value) if current_value is not None else 0.0,
                key=key,
            )
        elif kind == "boolean":
            options = ["Not specified", "Yes", "No"]
            selected = {None: "Not specified", True: "Yes", False: "No"}.get(current_value, "Not specified")
            values[field] = st.selectbox(f"Approved {label}", options, index=options.index(selected), key=key)
        elif kind == "list":
            values[field] = st.text_area(
                f"Approved {label}", value=", ".join(current_value or []), key=key,
                help="Separate items with commas.",
            )
        else:
            values[field] = st.text_area(f"Approved {label}", value=current_value or "", key=key)
    with right:
        st.markdown('<div class="review-evidence-label">SOURCE EVIDENCE</div>', unsafe_allow_html=True)
        evidence = _find_evidence(vendor, source_documents, keywords, original_value)
        if evidence:
            for chunk in evidence:
                st.markdown(
                    f'<div class="review-evidence"><b>Page {chunk.page_number or "?"} · {chunk.section or "General"}</b><br/>'
                    f'“{chunk.text[:260]}”</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No matching source excerpt was found. Review the proposal before approving this value.")
    st.divider()


def _find_evidence(
    vendor: str,
    source_documents: list[str],
    keywords: tuple[str, ...],
    extracted_value: Any,
):
    """Find the strongest available chunks even when extracted/chunk vendor names differ."""
    vendor_key = _normalise(vendor)
    document_keys = {_normalise(document) for document in source_documents}
    candidates = []
    for chunk in get_all_chunks():
        same_vendor = _normalise(chunk.vendor) == vendor_key
        same_document = _normalise(chunk.document) in document_keys
        if same_vendor or same_document:
            candidates.append(chunk)

    # A proposal's vendor can be named differently by the extractor and chunker.
    # If metadata is incomplete, retaining a source excerpt is better than falsely
    # claiming that none of the uploaded document has evidence.
    if not candidates:
        candidates = list(get_all_chunks())

    value_tokens = _value_tokens(extracted_value)

    def relevance(chunk) -> tuple[int, int]:
        text = chunk.text.lower()
        keyword_hits = sum(keyword in text for keyword in keywords)
        value_hits = sum(token in _normalise(text) for token in value_tokens)
        document_bonus = int(_normalise(chunk.document) in document_keys)
        vendor_bonus = int(_normalise(chunk.vendor) == vendor_key)
        return (value_hits * 8 + keyword_hits * 3 + document_bonus * 2 + vendor_bonus, -chunk.chunk_index)

    ranked = sorted(candidates, key=relevance, reverse=True)
    return ranked[:2]


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _value_tokens(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (int, float)):
        number = float(value)
        return tuple({_normalise(str(value)), _normalise(f"{number:.0f}"), _normalise(f"{number:.2f}")})
    return (_normalise(str(value)),)


def _apply_corrections(vendor: str, result, values: dict[str, Any]) -> None:
    update: dict[str, Any] = {}
    for field, _, kind, _ in REVIEW_FIELDS:
        value = values[field]
        if kind == "number":
            update[field] = value if value > 0 else None
        elif kind == "boolean":
            update[field] = {"Yes": True, "No": False, "Not specified": None}[value]
        elif kind == "list":
            update[field] = [item.strip() for item in value.split(",") if item.strip()]
        else:
            update[field] = value.strip() or None

    revised_proposal = result.proposal.model_copy(update=update, deep=True)
    requirements = get_requirements()
    recalculated = analyze_vendor(
        vendor_name=vendor,
        proposal=revised_proposal,
        source_documents=result.source_documents,
        requirements=requirements,
        all_chunks=get_all_chunks(),
        client=get_groq_client(),
    )
    changed = [field for field, value in update.items() if value != getattr(result.proposal, field)]
    set_vendor_result(vendor, recalculated)
    record_review_correction(vendor, changed)
    set_recommendation(None)
    st.success("Corrections applied. Requirement checks, risks, scores, rankings, and recommendation state have been recalculated.")
    st.session_state["_nav_target"] = "Analysis Dashboard"
    st.rerun()


def _format_value(value: Any) -> str:
    if value is None or value == [] or value == "":
        return "Not specified"
    if isinstance(value, list):
        return ", ".join(value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)
