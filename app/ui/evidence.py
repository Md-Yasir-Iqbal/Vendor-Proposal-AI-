"""Presentation-only evidence browser using the existing session chunks and results."""
from __future__ import annotations

import streamlit as st

from app.ui.styles import page_header, section_heading
from app.utils.state import get_all_chunks, get_vendor_results


def render() -> None:
    page_header("Inspect the source behind the signal.", "Review page-aware proposal excerpts already stored by the existing retrieval pipeline.", "EVIDENCE LIBRARY")
    chunks = get_all_chunks()
    if not chunks:
        st.info("No source evidence is available yet. Upload proposals to build the evidence library.")
        return
    vendors = sorted({chunk.vendor for chunk in chunks})
    selected = st.selectbox("Vendor", ["All vendors", *vendors], label_visibility="collapsed")
    query = st.text_input("Filter source text", placeholder="Search a clause, capability, or commercial term")
    filtered = [chunk for chunk in chunks if (selected == "All vendors" or chunk.vendor == selected) and (not query or query.lower() in chunk.text.lower())]
    st.caption(f"{len(filtered)} evidence excerpt(s) shown · sourced from the proposal PDFs")
    section_heading("Source excerpts")
    for chunk in filtered[:75]:
        st.markdown(f'''<article class="evidence-card"><div class="evidence-meta"><b>{chunk.vendor}</b> · {chunk.document} · Page {chunk.page_number or "—"} · {chunk.section or "General"}</div><div class="evidence-text">{chunk.text}</div></article>''', unsafe_allow_html=True)
    if len(filtered) > 75:
        st.caption("Showing the first 75 matching excerpts. Refine the filter to narrow the review.")
