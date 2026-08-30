"""
Centralized session-state management for the Streamlit app.

There is no database in this project (by design -- see README). All
analysis state lives in `st.session_state` for the duration of the
browser session, plus the Chroma vector store, which persists to disk in
data/chroma/ across runs.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from app.ai.groq_client import GroqClient
from app.retrieval.chroma_store import ChromaStore
from app.schemas.analysis import RecommendationResult, VendorAnalysisResult
from app.schemas.evidence import DocumentChunk
from app.schemas.requirements import RequirementsConfig
from app.schemas.vendor import VendorDocumentMeta
from app.utils.config import get_settings
from app.utils.helpers import generate_id


def init_state() -> None:
    defaults = {
        "project_id": generate_id("proj"),
        "requirements": None,  # RequirementsConfig
        "documents_meta": [],  # List[VendorDocumentMeta]
        "all_chunks": [],  # List[DocumentChunk]
        "vendor_results": {},  # Dict[str, VendorAnalysisResult]
        "recommendation": None,  # RecommendationResult
        "processing_log": [],  # List[str]
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def get_chroma_store(project_id: str) -> ChromaStore:
    """One Chroma collection per project_id, cached for the session's lifetime."""
    settings = get_settings()
    return ChromaStore(collection_name=f"{settings.chroma_collection_name}_{project_id}")


def get_groq_client() -> Optional[GroqClient]:
    settings = get_settings()
    if not settings.is_groq_configured():
        return None
    if "_groq_client" not in st.session_state:
        st.session_state["_groq_client"] = GroqClient(settings)
    return st.session_state["_groq_client"]


# --- typed accessors -----------------------------------------------------------------------

def get_requirements() -> Optional[RequirementsConfig]:
    return st.session_state.get("requirements")


def set_requirements(requirements: RequirementsConfig) -> None:
    st.session_state["requirements"] = requirements


def get_documents_meta() -> List[VendorDocumentMeta]:
    return st.session_state.get("documents_meta", [])


def add_document_meta(meta: VendorDocumentMeta) -> None:
    st.session_state.setdefault("documents_meta", []).append(meta)


def get_all_chunks() -> List[DocumentChunk]:
    return st.session_state.get("all_chunks", [])


def add_chunks(chunks: List[DocumentChunk]) -> None:
    st.session_state.setdefault("all_chunks", []).extend(chunks)


def get_vendor_results() -> Dict[str, VendorAnalysisResult]:
    return st.session_state.get("vendor_results", {})


def set_vendor_result(vendor_name: str, result: VendorAnalysisResult) -> None:
    st.session_state.setdefault("vendor_results", {})[vendor_name] = result


def get_recommendation() -> Optional[RecommendationResult]:
    return st.session_state.get("recommendation")


def set_recommendation(rec: RecommendationResult) -> None:
    st.session_state["recommendation"] = rec


def reset_analysis() -> None:
    """Clear uploaded documents / results but keep requirements config."""
    st.session_state["documents_meta"] = []
    st.session_state["all_chunks"] = []
    st.session_state["vendor_results"] = {}
    st.session_state["recommendation"] = None
    try:
        get_chroma_store(st.session_state["project_id"]).reset_project()
    except Exception:  # noqa: BLE001
        pass


def reset_everything() -> None:
    project_id = generate_id("proj")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["project_id"] = project_id
    init_state()
