"""Page 1 — Home / product landing + current analysis summary."""
from __future__ import annotations

import streamlit as st

from app.ui.styles import metric_card, page_header, section_heading
from app.utils.state import get_documents_meta, get_recommendation, get_requirements, get_vendor_results


def render() -> None:
    page_header("Make every vendor decision defensible.", "A single, evidence-grounded workspace for requirements, proposals, scores, and transparent recommendations.", "PROCUREMENT DECISION SUPPORT")
    st.markdown(
        '<div class="app-subtitle">'
        "Structured, evidence-grounded vendor comparison for procurement teams — "
        "upload proposals, define requirements, and get a transparent, explainable recommendation."
        "</div>",
        unsafe_allow_html=True,
    )

    requirements = get_requirements()
    results = get_vendor_results()
    docs = get_documents_meta()
    recommendation = get_recommendation()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### Get started")
        st.write(
            "Create an analysis project, define your requirements and scoring weights, "
            "then upload vendor proposal PDFs to compare."
        )
        if st.button("+ Create / Edit Analysis", type="primary", width="stretch"):
            st.session_state["_nav_target"] = "Create Analysis"
            st.rerun()
        if st.button("Upload Proposals", width="stretch", disabled=requirements is None):
            st.session_state["_nav_target"] = "Upload Proposals"
            st.rerun()
        if requirements is None:
            st.caption("Define requirements first to unlock proposal upload.")

    with col2:
        st.markdown("#### How it works")
        st.markdown(
            "1. **Define requirements** — budget, timeline, support, compliance, and scoring weights.\n"
            "2. **Upload proposals** — PDFs are parsed, cleaned, chunked, and embedded.\n"
            "3. **AI extracts structured data** — validated with Pydantic; nothing is invented.\n"
            "4. **Python matches & scores** — deterministic PASS/FAIL checks and weighted scoring.\n"
            "5. **Evidence-grounded recommendation** — backed by retrieved source excerpts."
        )

    section_heading("Current Analysis")

    if requirements is None:
        st.info("No analysis project has been created yet. Click **Create / Edit Analysis** to begin.")
        return

    processed = [d for d in docs if d.status == "processed"]
    failed = [d for d in docs if d.status == "failed"]
    total_risks = sum(len(r.risks) for r in results.values())

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric_card("Project", requirements.project_name), unsafe_allow_html=True)
    c2.markdown(metric_card("Vendors Analyzed", str(len(results))), unsafe_allow_html=True)
    c3.markdown(metric_card("Documents Uploaded", f"{len(docs)}", f"{len(failed)} failed" if failed else "All processed"), unsafe_allow_html=True)
    c4.markdown(metric_card("Flagged Risks", str(total_risks)), unsafe_allow_html=True)

    st.write("")
    if recommendation and recommendation.recommended_vendor:
        st.success(f"**Recommended vendor:** {recommendation.recommended_vendor}")
    elif results:
        st.warning("Vendors have been analyzed. Visit the Recommendation page to generate the AI-assisted recommendation.")
    else:
        st.info("Requirements are configured. Upload vendor proposals to begin the analysis.")
