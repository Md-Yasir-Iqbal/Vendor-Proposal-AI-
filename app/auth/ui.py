"""Presentation layer for login and account creation."""
from __future__ import annotations

import streamlit as st

from app.auth.auth import create_account, verify_credentials
from app.auth.email import send_welcome_email
from app.auth.session import login


_LOGO = '''<svg class="vendorlens-logo" viewBox="0 0 48 48" role="img" aria-label="Vendorlens logo">
    <circle cx="24" cy="24" r="20.5" fill="#102F35" stroke="#42C7BC" stroke-width="2"/>
    <path d="M10.5 13.5h7.2l6.7 20.2 6.1-14.8h7.2L27.5 40h-6.2L10.5 13.5Z" fill="#27B9AD"/>
    <path d="M30.5 14h7v18.3h-14l2.7-6h7.3V14Z" fill="#E9B949"/>
    <circle cx="37.6" cy="34.5" r="3.2" fill="#F5FBF9"/>
</svg>'''


def render_login_page() -> None:
    """Render the public authentication experience without changing auth behavior."""
    st.markdown('<div class="auth-topline"></div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-page-label">VENDORLENS · SECURE WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown('<span class="auth-split-mode" aria-hidden="true"></span>', unsafe_allow_html=True)

    showcase, access = st.columns([1.08, 0.92], gap="large")
    with showcase:
        st.markdown(
            f'''<section class="auth-showcase">
                <div class="auth-brand-lockup">{_LOGO}<div><b>Vendorlens</b><span>PROCUREMENT INTELLIGENCE</span></div></div>
                <div class="auth-overline"><span></span> EVIDENCE-LED PROCUREMENT</div>
                <h1>Every vendor decision, <em>backed by proof.</em></h1>
                <p>Turn complex proposal documents into a clear, traceable decision workspace your team can trust.</p>
                <div class="auth-proof-list">
                    <div><i>01</i><span><b>Extract with context</b>Structure proposal facts without losing the source.</span></div>
                    <div><i>02</i><span><b>Evaluate consistently</b>Apply the same requirements and scoring rules to every vendor.</span></div>
                    <div><i>03</i><span><b>Decide with confidence</b>Inspect risks, evidence, and human-approved corrections.</span></div>
                </div>
                <div class="auth-trust"><span class="auth-trust-dot"></span> Private, user-scoped analysis workspace</div>
            </section>''',
            unsafe_allow_html=True,
        )

    with access:
        st.markdown(
            f'''<section class="auth-access-heading">
                <div class="auth-access-logo">{_LOGO}</div>
                <div><div class="auth-name">Vendorlens</div><div class="auth-kicker">PROCUREMENT INTELLIGENCE</div></div>
                <div class="auth-access-copy"><b>Welcome back.</b><span>Sign in to your secure procurement workspace.</span></div>
            </section>''',
            unsafe_allow_html=True,
        )
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])
        with sign_in_tab:
            _render_sign_in()
        with sign_up_tab:
            _render_sign_up()
        st.markdown(
            '<div class="auth-footnote">Your account and saved analyses are protected in your private workspace.</div>',
            unsafe_allow_html=True,
        )


def _render_sign_in() -> None:
    with st.form("sign_in_form"):
        st.markdown("#### Sign in to your workspace")
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
        st.markdown("#### Create your workspace")
        email = st.text_input("Work email", placeholder="name@company.com", key="sign_up_email")
        password = st.text_input(
            "Password",
            type="password",
            key="sign_up_password",
            help="At least 8 characters, including a letter and a number.",
        )
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
