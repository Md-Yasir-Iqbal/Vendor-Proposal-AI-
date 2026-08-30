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
from app.persistence.database import get_analysis_snapshot, save_analysis_snapshot
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
    _persist_current_analysis()


def get_documents_meta() -> List[VendorDocumentMeta]:
    return st.session_state.get("documents_meta", [])


def add_document_meta(meta: VendorDocumentMeta) -> None:
    st.session_state.setdefault("documents_meta", []).append(meta)
    _persist_current_analysis()


def get_all_chunks() -> List[DocumentChunk]:
    return st.session_state.get("all_chunks", [])


def add_chunks(chunks: List[DocumentChunk]) -> None:
    st.session_state.setdefault("all_chunks", []).extend(chunks)
    _persist_current_analysis()


def get_vendor_results() -> Dict[str, VendorAnalysisResult]:
    return st.session_state.get("vendor_results", {})


def set_vendor_result(vendor_name: str, result: VendorAnalysisResult) -> None:
    st.session_state.setdefault("vendor_results", {})[vendor_name] = result
    _persist_current_analysis()


def get_recommendation() -> Optional[RecommendationResult]:
    return st.session_state.get("recommendation")


def set_recommendation(rec: RecommendationResult) -> None:
    st.session_state["recommendation"] = rec
    _persist_current_analysis()


def _persist_current_analysis() -> None:
    """Save a user-owned snapshot without changing the live analysis workflow."""
    user_email = st.session_state.get("auth_user")
    if not user_email:
        return
    requirements = st.session_state.get("requirements")
    snapshot = {
        "requirements": requirements.model_dump(mode="json") if requirements else None,
        "documents_meta": [meta.model_dump(mode="json") for meta in st.session_state.get("documents_meta", [])],
        "all_chunks": [chunk.model_dump(mode="json") for chunk in st.session_state.get("all_chunks", [])],
        "vendor_results": {
            name: result.model_dump(mode="json")
            for name, result in st.session_state.get("vendor_results", {}).items()
        },
        "recommendation": (
            st.session_state["recommendation"].model_dump(mode="json")
            if st.session_state.get("recommendation")
            else None
        ),
    }
    try:
        save_analysis_snapshot(
            user_email=user_email,
            project_id=st.session_state["project_id"],
            project_name=requirements.project_name if requirements else None,
            snapshot=snapshot,
        )
    except Exception:  # noqa: BLE001 - storage must never interrupt an analysis
        pass


def restore_saved_analysis(user_email: str, project_id: str) -> bool:
    """Restore a user's snapshot into the same state used by the existing pages."""
    snapshot = get_analysis_snapshot(user_email, project_id)
    if snapshot is None:
        return False
    try:
        requirements_data = snapshot.get("requirements")
        st.session_state["project_id"] = project_id
        st.session_state["requirements"] = RequirementsConfig.model_validate(requirements_data) if requirements_data else None
        st.session_state["documents_meta"] = [VendorDocumentMeta.model_validate(item) for item in snapshot.get("documents_meta", [])]
        st.session_state["all_chunks"] = [DocumentChunk.model_validate(item) for item in snapshot.get("all_chunks", [])]
        st.session_state["vendor_results"] = {
            name: VendorAnalysisResult.model_validate(result)
            for name, result in snapshot.get("vendor_results", {}).items()
        }
        recommendation_data = snapshot.get("recommendation")
        st.session_state["recommendation"] = RecommendationResult.model_validate(recommendation_data) if recommendation_data else None
        st.session_state["processing_log"] = []
    except Exception:  # noqa: BLE001 - invalid legacy snapshot must not break the app
        return False
    return True


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
    auth_state = {
        key: st.session_state[key]
        for key in ("auth_accounts", "auth_authenticated", "auth_user")
        if key in st.session_state
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.update(auth_state)
    st.session_state["project_id"] = project_id
    init_state()
