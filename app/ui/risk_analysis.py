"""Presentation-only risk register for already calculated vendor risks."""
from __future__ import annotations

import streamlit as st

from app.ui.styles import page_header, section_heading, severity_class
from app.utils.state import get_vendor_results


def render() -> None:
    page_header("Review exceptions before approval.", "A single, traceable register of the risks the existing evaluation pipeline identified.", "RISK REGISTER")
    results = get_vendor_results()
    risks = [(vendor, risk) for vendor, result in results.items() for risk in result.risks]
    if not risks:
        st.info("No risks are available yet. Analyze one or more vendor proposals to populate this register.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Total findings", len(risks))
    c2.metric("Potential risks", sum(risk.severity.value == "Potential Risk" for _, risk in risks))
    c3.metric("Requires review", sum(risk.severity.value == "Requires Review" for _, risk in risks))
    section_heading("Open findings")
    for vendor, risk in risks:
        source = "AI-identified" if risk.source == "ai_identified" else "Rule-based"
        evidence = ""
        if risk.evidence:
            evidence = f'<div class="risk-evidence">Source · Page {risk.evidence.page_number or "—"} · {risk.evidence.section or "General"}<br/>{risk.evidence.source_text[:300]}</div>'
        st.markdown(f'''<article class="risk-card {severity_class(risk.severity.value)}">
            <div class="risk-vendor">{vendor}</div><b>{risk.category}</b>
            <span class="risk-meta">{risk.severity.value} · {source}</span><p>{risk.description}</p>{evidence}</article>''', unsafe_allow_html=True)
