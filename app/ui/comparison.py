"""Page 5 — Professional side-by-side vendor comparison table."""
from __future__ import annotations

import streamlit as st

from app.business_logic.scoring import rank_vendors
from app.ui.styles import page_header, section_heading, status_badge
from app.utils.helpers import status_icon
from app.utils.state import get_vendor_results


def render() -> None:
    page_header("Compare every requirement, side by side.", "See how each vendor performs before you move to a final recommendation.", "VENDOR COMPARISON")

    results = get_vendor_results()
    valid_results = {k: v for k, v in results.items() if not v.extraction_failed}

    if not valid_results:
        st.info("No successfully analyzed vendors yet. Upload proposals to compare them here.")
        return

    ranking = rank_vendors({k: v.score for k, v in valid_results.items()})

    # Build the requirement x vendor matrix.
    all_labels = []
    for v in valid_results.values():
        for r in v.requirement_results:
            if r.label not in all_labels:
                all_labels.append(r.label)

    section_heading("Requirement matrix")
    header_cols = st.columns([2.2] + [1] * len(ranking))
    header_cols[0].markdown("**Requirement**")
    for i, vendor in enumerate(ranking, start=1):
        header_cols[i].markdown(f"**{vendor}**")

    for label in all_labels:
        row_cols = st.columns([2.2] + [1] * len(ranking))
        row_cols[0].markdown(label)
        for i, vendor in enumerate(ranking, start=1):
            match = next((r for r in valid_results[vendor].requirement_results if r.label == label), None)
            if match:
                row_cols[i].markdown(status_badge(match.status.value), unsafe_allow_html=True)
            else:
                row_cols[i].markdown("—")

    section_heading("Overall score")
    score_cols = st.columns([2.2] + [1] * len(ranking))
    score_cols[0].markdown("**Overall Score**")
    for i, vendor in enumerate(ranking, start=1):
        score = valid_results[vendor].score.total_score
        score_cols[i].markdown(f"**{score}** / 100")

    section_heading("Score breakdown")
    breakdown_rows = []
    for category, key in [
        ("Technical Fit", "technical_fit"),
        ("Budget", "budget"),
        ("Delivery Timeline", "delivery_timeline"),
        ("Support & SLA", "support_sla"),
        ("Risk", "risk"),
    ]:
        row = {"Category": category}
        for vendor in ranking:
            row[vendor] = getattr(valid_results[vendor].score, key)
        breakdown_rows.append(row)
    st.dataframe(breakdown_rows, width="stretch", hide_index=True)

    st.caption(
        "✓ Pass · ✗ Fail · ⚠ Requires Review · — Not specified in the proposal. "
        "Scores are computed deterministically by weighted Python logic, not by the AI model."
    )
