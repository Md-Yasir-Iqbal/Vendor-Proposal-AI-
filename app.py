"""
AI-Powered Vendor Proposal Analysis and Decision Support System
Streamlit application entry point.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from app.auth.session import init_auth_state, is_authenticated, logout
from app.auth.ui import render_login_page
from app.ui import account, ask_proposals, comparison, create_analysis, dashboard, evidence, history, home, recommendation, review, risk_analysis, upload, vendor_details
from app.ui.styles import inject_css
from app.utils.config import get_settings
from app.utils.state import get_requirements, get_vendor_results, init_state, reset_everything

st.set_page_config(
    page_title="Vendorlens",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_auth_state()
inject_css()

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
    "Human Review": review,
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
            <div class="sidebar-mark" role="img" aria-label="Vendorlens logo">
                <svg class="sidebar-logo" viewBox="0 0 48 48" aria-hidden="true">
                    <circle cx="24" cy="24" r="20.5" fill="#102F35" stroke="#42C7BC" stroke-width="2"/>
                    <path d="M10.5 13.5h7.2l6.7 20.2 6.1-14.8h7.2L27.5 40h-6.2L10.5 13.5Z" fill="#27B9AD"/>
                    <path d="M30.5 14h7v18.3h-14l2.7-6h7.3V14Z" fill="#E9B949"/>
                    <circle cx="37.6" cy="34.5" r="3.2" fill="#F5FBF9"/>
                </svg>
            </div>
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

toolbar_left, toolbar_right = st.columns([10, 1])
with toolbar_right:
    ask_proposals.render_launcher()

PAGES[page].render()
