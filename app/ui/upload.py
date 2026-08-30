"""Page 3 — Upload vendor proposal PDFs and run the extraction pipeline."""
from __future__ import annotations

import streamlit as st

from app.pipeline import analyze_vendor, build_failed_vendor_result, process_uploaded_pdf
from app.ui.styles import page_header, section_heading
from app.utils.config import get_settings
from app.utils.state import (
    add_chunks,
    add_document_meta,
    get_all_chunks,
    get_chroma_store,
    get_documents_meta,
    get_groq_client,
    get_requirements,
    get_vendor_results,
    set_vendor_result,
)

STATUS_LABELS = {
    "processed": ("Processed", "success"),
    "scanned_warning": ("Processed (limited text)", "warning"),
    "failed": ("Failed", "error"),
    "pending": ("Pending", "info"),
}


def render() -> None:
    page_header("Bring proposals into focus.", "", "DOCUMENT INTAKE")
    st.markdown(
        '<div class="app-subtitle">Upload one PDF per vendor. Each document is parsed, '
        "cleaned, chunked, embedded for retrieval, and analyzed with the LLM.</div>",
        unsafe_allow_html=True,
    )

    requirements = get_requirements()
    if requirements is None:
        st.warning("Define your requirements first on the **Create Analysis** page.")
        return

    settings = get_settings()
    client = get_groq_client()
    if client is None:
        st.warning(
            "⚠ GROQ_API_KEY / GROQ_MODEL are not configured. Documents will still be parsed, "
            "cleaned, chunked, and stored for retrieval, but structured extraction (and therefore "
            "matching/scoring) requires a working Groq API configuration. Add your key to `.env` and restart."
        )

    section_heading("Proposal documents")
    uploaded_files = st.file_uploader(
        "Upload vendor proposal PDFs", type=["pdf"], accept_multiple_files=True
    )

    already_processed_names = {m.filename for m in get_documents_meta()}

    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in already_processed_names]
        if new_files:
            store = get_chroma_store(st.session_state["project_id"])
            progress = st.progress(0.0, text="Starting...")
            for i, file in enumerate(new_files):
                progress.progress((i) / len(new_files), text=f"Processing {file.name}...")
                file_bytes = file.read()
                processed = process_uploaded_pdf(file_bytes, file.name, store, client)
                add_document_meta(processed.meta)
                if processed.chunks:
                    add_chunks(processed.chunks)

                if processed.proposal is not None:
                    vendor_name = processed.proposal.vendor_name or processed.meta.detected_vendor_name or file.name
                    try:
                        result = analyze_vendor(
                            vendor_name=vendor_name,
                            proposal=processed.proposal,
                            source_documents=[file.name],
                            requirements=requirements,
                            all_chunks=get_all_chunks(),
                            client=client,
                        )
                        set_vendor_result(vendor_name, result)
                    except Exception as exc:  # noqa: BLE001 — isolate failures per vendor
                        set_vendor_result(
                            vendor_name, build_failed_vendor_result(vendor_name, file.name, str(exc))
                        )
                elif processed.meta.status == "failed":
                    vendor_name = processed.meta.detected_vendor_name or file.name
                    set_vendor_result(
                        vendor_name,
                        build_failed_vendor_result(vendor_name, file.name, processed.meta.error_message or "Unknown error"),
                    )
            progress.progress(1.0, text="Done.")
            st.rerun()

    docs = get_documents_meta()
    if not docs:
        st.info("No documents uploaded yet. Use the uploader above to add vendor proposal PDFs.")
        return

    section_heading("Processing status")
    for meta in docs:
        label, kind = STATUS_LABELS.get(meta.status, ("Unknown", "info"))
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{meta.filename}**")
            c2.markdown(f"Vendor: {meta.detected_vendor_name or '—'}")
            getattr(c3, kind)(label)
            if meta.warnings:
                for w in meta.warnings:
                    st.caption(f"⚠ {w}")
            if meta.error_message:
                st.caption(f"Error: {meta.error_message}")
            if meta.status != "failed":
                st.caption(f"{meta.num_pages} page(s) · {meta.num_chunks} chunk(s) stored for retrieval")

    results = get_vendor_results()
    if results:
        section_heading("Vendors ready for analysis")
        st.write(", ".join(sorted(results.keys())))
        if st.button("Go to Analysis Dashboard →", type="primary"):
            st.session_state["_nav_target"] = "Analysis Dashboard"
            st.rerun()
