"""User-scoped SQLite history view; restoration stays in the existing state service."""
from __future__ import annotations

import streamlit as st

from app.persistence.database import list_analysis_history
from app.ui.styles import page_header, section_heading
from app.utils.state import restore_saved_analysis


def render() -> None:
    page_header("Your saved decision workspaces.", "Every snapshot is private to the signed-in account and can be restored into the existing analysis flow.", "ANALYSIS HISTORY")
    user = st.session_state.get("auth_user", "")
    items = list_analysis_history(user, limit=100)
    if not items:
        st.info("No saved analyses yet. Create an analysis and save requirements to create your first workspace.")
        return
    section_heading("Saved analyses")
    for item in items:
        left, right = st.columns([5, 1])
        with left:
            st.markdown(f'''<div class="history-row"><b>{item["project_name"] or "Untitled analysis"}</b><span>Last updated {item["updated_at"].replace("T", " ").split("+")[0]} UTC</span></div>''', unsafe_allow_html=True)
        with right:
            if st.button("Open", key=f'history_{item["project_id"]}', width="stretch"):
                if restore_saved_analysis(user, item["project_id"]):
                    # The sidebar radio owns ``nav`` during this run; defer the
                    # navigation update until the next run via the app's existing
                    # navigation bridge.
                    st.session_state["_nav_target"] = "Analysis Dashboard"
                    st.rerun()
                st.error("This saved analysis could not be restored.")
