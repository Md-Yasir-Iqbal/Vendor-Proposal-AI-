"""Page 4 — Analysis Dashboard: overall statistics and vendor ranking."""
from __future__ import annotations

import streamlit as st

from app.business_logic.scoring import rank_vendors
from app.ui.styles import advisory_footer, metric_card, page_header, section_heading
from app.utils.state import get_requirements, get_vendor_results


def render() -> None:
    page_header("Your vendor landscape, at a glance.", "Compare readiness, score, and risk across every analyzed proposal.", "ANALYSIS OVERVIEW")

    requirements = get_requirements()
    results = get_vendor_results()

    if requirements is None:
        st.warning("Define your requirements first on the **Create Analysis** page.")
        return
    if not results:
        st.info("No vendors analyzed yet. Upload proposals on the **Upload Proposals** page.")
        return

    valid_results = {k: v for k, v in results.items() if not v.extraction_failed}
    failed_results = {k: v for k, v in results.items() if v.extraction_failed}

    scores = {k: v.score for k, v in valid_results.items()}
    ranking = rank_vendors(scores) if scores else []
    total_risks = sum(len(v.risks) for v in results.values())
    avg_score = round(sum(s.total_score for s in scores.values()) / len(scores), 1) if scores else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(metric_card("Vendors Analyzed", str(len(results)), f"{len(failed_results)} failed" if failed_results else "All succeeded"), unsafe_allow_html=True)
    c2.markdown(metric_card("Top Vendor", ranking[0] if ranking else "—", f"{scores[ranking[0]].total_score}/100" if ranking else ""), unsafe_allow_html=True)
    c3.markdown(metric_card("Average Score", f"{avg_score}/100"), unsafe_allow_html=True)
    c4.markdown(metric_card("Flagged Risks", str(total_risks)), unsafe_allow_html=True)

    section_heading("Vendor ranking")
    if not ranking:
        st.warning("No vendor could be scored (all documents failed processing). Check the Upload page for details.")
    for i, vendor in enumerate(ranking, start=1):
        result = valid_results[vendor]
        css_class = "rank-card rank-1" if i == 1 else "rank-card"
        mandatory_note = " ⚠ does not meet all mandatory requirements" if result.has_mandatory_failure else ""
        st.markdown(
            f"""
            <div class="{css_class}">
                <b>#{i} — {vendor}</b>{mandatory_note}<br/>
                <span style="color:#6b7280;font-size:0.85rem;">
                    Score: <b>{result.score.total_score}/100</b> ·
                    {result.pass_count()} requirement(s) passed ·
                    {result.fail_count()} failed ·
                    {len(result.risks)} risk(s) flagged
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if failed_results:
        section_heading("Processing failures")
        for vendor, result in failed_results.items():
            st.error(f"**{vendor}**: {result.extraction_error or 'Unknown processing error.'}")

    section_heading("Requirement summary")
    if valid_results:
        req_labels = []
        for r in next(iter(valid_results.values())).requirement_results:
            req_labels.append(r.label)
        if req_labels:
            summary_rows = []
            for label in req_labels:
                row = {"Requirement": label}
                for vendor, result in valid_results.items():
                    match = next((r for r in result.requirement_results if r.label == label), None)
                    row[vendor] = match.status.value if match else "—"
                summary_rows.append(row)
            st.dataframe(summary_rows, width="stretch", hide_index=True)
        else:
            st.caption("No requirements were configured to compare against.")

    advisory_footer()
