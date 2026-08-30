"""Authentication session state, intentionally separate from analysis state."""
from __future__ import annotations

import streamlit as st

from app.persistence.database import initialize_database


def init_auth_state() -> None:
    initialize_database()
    st.session_state.setdefault("auth_authenticated", False)
    st.session_state.setdefault("auth_user", None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_authenticated"))


def login(email: str) -> None:
    st.session_state["auth_authenticated"] = True
    st.session_state["auth_user"] = email.strip().lower()


def logout() -> None:
    """End a login while retaining temporary accounts for this browser session."""
    st.session_state["auth_authenticated"] = False
    st.session_state["auth_user"] = None
