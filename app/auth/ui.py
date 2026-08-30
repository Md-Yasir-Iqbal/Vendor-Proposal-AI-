"""The login and registration interface for the temporary auth layer."""
from __future__ import annotations

import streamlit as st

from app.auth.auth import create_account, verify_credentials
from app.auth.email import send_welcome_email
from app.auth.session import login


def render_login_page() -> None:
    """Render the only page visible before a user authenticates."""
    st.markdown('<div class="auth-topline"></div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-page-label">VENDORLENS · SECURE WORKSPACE</div>', unsafe_allow_html=True)
    showcase, access = st.columns([1.18, 0.82], gap="large")
    with showcase:
        st.markdown(
            '''<div class="auth-showcase">
                <div class="auth-overline"><span></span> PROCUREMENT INTELLIGENCE</div>
                <h1>Make every vendor decision <em>defensible.</em></h1>
                <p>Bring proposal evidence, requirement checks, and decision-ready comparisons into one focused workspace.</p>
                <div class="auth-feature-grid">
                    <div><i class="feature-icon feature-evidence">01</i><b>Evidence-led</b><span>Trace every finding to source material.</span></div>
                    <div><i class="feature-icon feature-score">02</i><b>Consistent scoring</b><span>Evaluate every proposal against the same rules.</span></div>
                    <div><i class="feature-icon feature-ready">03</i><b>Decision ready</b><span>Surface risks and trade-offs with clarity.</span></div>
                </div>
                <div class="auth-intelligence-preview">
                    <div class="preview-head"><span>LIVE DECISION BRIEF</span><b>3 vendors evaluated</b></div>
                    <div class="preview-row preview-winner"><span class="preview-rank">01</span><span class="preview-vendor">NimbusDesk <small>Recommended</small></span><strong>91.4</strong><div class="preview-bar"><i style="width:91.4%"></i></div></div>
                    <div class="preview-row"><span class="preview-rank">02</span><span class="preview-vendor">QuickServe</span><strong>84.7</strong><div class="preview-bar"><i style="width:84.7%"></i></div></div>
                    <div class="preview-row"><span class="preview-rank">03</span><span class="preview-vendor">Orbitel</span><strong>78.2</strong><div class="preview-bar"><i style="width:78.2%"></i></div></div>
                </div>
                <div class="auth-trust"><span class="auth-trust-dot"></span> Your analysis workspace is private to your account</div>
            </div>''',
            unsafe_allow_html=True,
        )
    with access:
        st.markdown('''<div class="auth-access-heading"><div class="auth-mark">VL</div><div><div class="auth-name">Welcome to Vendorlens</div><div class="auth-kicker">SECURE ACCOUNT ACCESS</div></div></div><div class="auth-access-copy">Your procurement workspace, ready when you are.</div>''', unsafe_allow_html=True)
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])
        with sign_in_tab:
            _render_sign_in()
        with sign_up_tab:
            _render_sign_up()
        st.markdown('<div class="auth-footnote">Your account and saved analyses are protected in your private workspace.</div>', unsafe_allow_html=True)


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
