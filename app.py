"""
AI-Powered Vendor Proposal Analysis and Decision Support System
Streamlit application entry point.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from app.auth.session import init_auth_state, is_authenticated, logout
from app.auth.ui import render_login_page
from app.ui import account, comparison, create_analysis, dashboard, evidence, history, home, recommendation, risk_analysis, upload, vendor_details
from app.ui.styles import inject_css
from app.utils.config import get_settings
from app.utils.state import get_requirements, get_vendor_results, init_state, reset_everything

st.set_page_config(
    page_title="Vendorlens",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_auth_state()

if not is_authenticated():
    render_login_page()
    st.stop()

init_state()

if "auth_notice" in st.session_state:
    st.warning(st.session_state.pop("auth_notice"))

PAGES = {
    "Home": home,
    "Create Analysis": create_analysis,
    "Upload Proposals": upload,
    "Analysis Dashboard": dashboard,
    "Vendor Comparison": comparison,
    "Vendor Details": vendor_details,
    "Risk Analysis": risk_analysis,
    "Evidence": evidence,
    "Recommendation": recommendation,
    "Analysis History": history,
    "Account": account,
}

# Allow other pages to programmatically navigate (e.g. after saving requirements).
if "_nav_target" in st.session_state:
    st.session_state["nav"] = st.session_state.pop("_nav_target")

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-mark">VL</div>
            <div>
                <div class="sidebar-title">Vendorlens</div>
                <div class="sidebar-subtitle">PROCUREMENT INTELLIGENCE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-label">WORKSPACE</div>', unsafe_allow_html=True)

    page = st.radio("Navigate", list(PAGES.keys()), key="nav", label_visibility="collapsed")

    st.markdown('<div class="sidebar-section-label">ANALYSIS STATUS</div>', unsafe_allow_html=True)
    requirements = get_requirements()
    results = get_vendor_results()
    st.caption(f"Project: **{requirements.project_name}**" if requirements else "No project yet")
    st.caption(f"Vendors analyzed: **{len(results)}**")

    settings = get_settings()
    if settings.is_groq_configured():
        st.caption("Groq API: configured")
    else:
        st.caption("Groq API: not configured (.env)")

    st.markdown('<div class="sidebar-section-label">SYSTEM</div>', unsafe_allow_html=True)
    st.caption(f"Signed in as {st.session_state['auth_user']}")
    if st.button("Log out", width="stretch"):
        logout()
        st.rerun()
    if st.button("Start New Analysis", width="stretch"):
        reset_everything()
        st.rerun()

PAGES[page].render()
