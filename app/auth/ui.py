"""The login and registration interface for the temporary auth layer."""
from __future__ import annotations

import streamlit as st

from app.auth.auth import create_account, verify_credentials
from app.auth.email import send_welcome_email
from app.auth.session import login


def render_login_page() -> None:
    """Render the only page visible before a user authenticates."""
    st.markdown('<div class="auth-topline"></div>', unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        st.markdown(
            '''<div class="auth-brand">
                <div class="auth-mark">VP</div>
                <div class="auth-name">Vendor Proposal AI</div>
                <div class="auth-kicker">PROCUREMENT INTELLIGENCE</div>
                <h1>Decide with confidence.</h1>
                <p>Securely access your evidence-grounded vendor analysis workspace.</p>
            </div>''',
            unsafe_allow_html=True,
        )
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])
        with sign_in_tab:
            _render_sign_in()
        with sign_up_tab:
            _render_sign_up()
        st.caption("Accounts and saved analyses are stored locally. Email delivery uses your configured SMTP/Gmail account.")


def _render_sign_in() -> None:
    with st.form("sign_in_form"):
        st.markdown("#### Welcome back")
        email = st.text_input("Email address", placeholder="name@company.com", key="sign_in_email")
        password = st.text_input("Password", type="password", key="sign_in_password")
        submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
    if submitted:
        error = verify_credentials(email, password)
        if error:
            st.error(error)
        else:
            login(email)
            st.rerun()


def _render_sign_up() -> None:
    with st.form("sign_up_form"):
        st.markdown("#### Create your account")
        email = st.text_input("Work email", placeholder="name@company.com", key="sign_up_email")
        password = st.text_input("Password", type="password", key="sign_up_password", help="At least 8 characters, including a letter and a number.")
        confirmation = st.text_input("Confirm password", type="password", key="sign_up_confirmation")
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")
    if submitted:
        if password != confirmation:
            st.error("Passwords do not match.")
            return
        error = create_account(email, password)
        if error:
            st.error(error)
        else:
            email_notice = send_welcome_email(email.strip().lower())
            login(email)
            st.session_state["auth_notice"] = email_notice or "Account created. A welcome email has been sent."
            st.rerun()
