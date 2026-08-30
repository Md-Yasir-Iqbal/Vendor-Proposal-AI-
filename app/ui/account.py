"""Presentation-only secure workspace account view."""
from __future__ import annotations

import streamlit as st

from app.persistence.database import list_analysis_history
from app.ui.styles import page_header, section_heading


def render() -> None:
    page_header("Your secure workspace.", "Account credentials continue to be managed by the existing authentication and SQLite services.", "ACCOUNT")
    email = st.session_state.get("auth_user", "")
    analyses = list_analysis_history(email, limit=100)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'''<div class="content-panel"><div class="panel-kicker">SIGNED-IN ACCOUNT</div><div class="panel-title">{email}</div><p>Your analyses are saved only to this account.</p></div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''<div class="content-panel"><div class="panel-kicker">WORKSPACES</div><div class="metric-value">{len(analyses)}</div><p>Saved analyses</p></div>''', unsafe_allow_html=True)
    section_heading("Privacy & access")
    st.info("Your login, sessions, and history remain handled by the existing Streamlit and SQLite authentication flow. Use Log out in the sidebar to end this session.")
