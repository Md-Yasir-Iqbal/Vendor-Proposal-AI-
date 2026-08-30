"""Shared CSS and small UI-rendering helpers so every page looks consistent."""
from __future__ import annotations

import streamlit as st

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');

    :root { --ink: #192d34; --muted: #63767b; --line: #dbe5e2; --cream: #f7f9f6; --teal: #087b71; --teal-dark: #055c56; --mint: #e5f4ee; --gold: #e9b949; }
    .stApp { background: var(--cream); color: var(--ink); font-family: 'DM Sans', sans-serif; }
    .block-container { padding: 2.5rem 3rem 4rem; max-width: 1280px; }
    h1, h2, h3 { color: var(--ink); font-weight: 700; letter-spacing: -0.035em; }
    h1 { font-family: 'Newsreader', serif; font-size: 2.45rem !important; line-height: 1.05; }
    h2 { font-family: 'Newsreader', serif; font-size: 1.65rem !important; margin-top: 1.8rem !important; }
    h3 { font-size: 1.12rem !important; margin-top: 1.4rem !important; }
    [data-testid="stMarkdownContainer"] p { line-height: 1.6; }

    .app-subtitle { color: var(--muted); font-size: 1.02rem; line-height: 1.55; max-width: 780px; margin-top: -0.45rem; margin-bottom: 1.7rem; }
    .page-hero { position: relative; overflow: hidden; padding: 2rem 2.15rem; margin: -.65rem 0 1.7rem; border: 1px solid #d6e5df; border-radius: 18px; background: linear-gradient(115deg, #e4f3ed 0%, #f8fbf8 62%, #f2eee5 100%); }
    .page-hero:after { content: ''; position: absolute; right: -3.5rem; top: -4.6rem; width: 15rem; height: 15rem; border: 1px solid rgba(8,123,113,.14); border-radius: 50%; box-shadow: 0 0 0 1.7rem rgba(8,123,113,.045), 0 0 0 3.4rem rgba(8,123,113,.025); }
    .page-eyebrow { position: relative; z-index: 1; color: var(--teal); font-family: 'DM Mono', monospace; font-size: .67rem; font-weight: 500; letter-spacing: .12em; }
    .page-title { position: relative; z-index: 1; max-width: 780px; margin: .35rem 0 .4rem; color: var(--ink); font-family: 'Newsreader', serif; font-size: 2.5rem; font-weight: 600; line-height: 1.06; letter-spacing: -.04em; }
    .page-description { position: relative; z-index: 1; max-width: 720px; margin: 0; color: #5e7375; font-size: 1rem; line-height: 1.55; }
    .content-panel { height: 100%; box-sizing: border-box; padding: 1.35rem 1.45rem; border: 1px solid var(--line); border-radius: 14px; background: #fff; box-shadow: 0 7px 20px rgba(17,49,46,.04); }
    .panel-kicker { margin-bottom: .35rem; color: var(--teal); font-family: 'DM Mono', monospace; font-size: .65rem; letter-spacing: .09em; }
    .panel-title { margin: 0 0 .55rem; color: var(--ink); font-size: 1.1rem; font-weight: 700; letter-spacing: -.025em; }
    .workflow-list { display: grid; gap: .68rem; margin-top: .85rem; }
    .workflow-step { display: flex; align-items: flex-start; gap: .7rem; color: #52676b; font-size: .9rem; line-height: 1.42; }
    .workflow-number { flex: 0 0 1.35rem; display: grid; place-items: center; width: 1.35rem; height: 1.35rem; border-radius: 50%; background: var(--mint); color: var(--teal); font-family: 'DM Mono', monospace; font-size: .65rem; font-weight: 500; }
    .section-heading { display: flex; align-items: center; gap: .65rem; margin: 2rem 0 .85rem; color: var(--ink); font-size: 1.1rem; font-weight: 700; letter-spacing: -.025em; }
    .section-heading:after { content: ''; flex: 1; height: 1px; background: var(--line); }

    [data-testid="stSidebar"] { background: linear-gradient(175deg, #102f35 0%, #0c252b 100%); }
    [data-testid="stSidebar"] * { color: #eaf4f1; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #bdd0cc; }
    [data-testid="stSidebar"] .stButton button { background: transparent; border-color: rgba(231,244,240,.24); color: #f3faf8; }
    [data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.45); }
    .sidebar-brand { display: flex; align-items: center; gap: .75rem; padding: .45rem .15rem 1.8rem; }
    .sidebar-mark { display: grid; place-items: center; width: 2.35rem; height: 2.35rem; border-radius: .7rem; background: var(--gold); color: #183139 !important; font-family: 'DM Mono', monospace; font-size: .75rem; font-weight: 600; }
    .sidebar-title { font-size: 1rem; font-weight: 700; letter-spacing: -.02em; }
    .sidebar-subtitle, .sidebar-section-label { color: #8fb0aa !important; font-family: 'DM Mono', monospace; font-size: .62rem; letter-spacing: .1em; }
    .sidebar-section-label { margin: 1.4rem 0 .55rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .35rem .45rem; border-radius: .45rem; transition: background .15s ease; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.08); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: rgba(229,244,238,.12); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size: .88rem; color: #dcebe7 !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color: var(--gold); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child { display: none; }

    .metric-card {
        background: #fff; border: 1px solid var(--line); border-radius: 14px;
        padding: 1.05rem 1.15rem; min-height: 105px; box-shadow: 0 7px 20px rgba(17,49,46,.045);
    }
    .metric-label { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .65rem; text-transform: uppercase; letter-spacing: .075em; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: var(--ink); margin-top: .35rem; letter-spacing: -.04em; overflow-wrap: anywhere; }
    .metric-sub { color: #829397; font-size: .76rem; margin-top: .18rem; }

    .stButton button { border-radius: .55rem; font-weight: 600; min-height: 2.55rem; transition: transform .15s ease, box-shadow .15s ease; }
    .stButton button[kind="primary"] { background: var(--teal); border-color: var(--teal); box-shadow: 0 5px 12px rgba(8,123,113,.18); }
    .stButton button[kind="primary"]:hover { background: var(--teal-dark); border-color: var(--teal-dark); transform: translateY(-1px); }
    [data-testid="stForm"] { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 1.35rem 1.45rem 1.45rem; box-shadow: 0 7px 20px rgba(17,49,46,.04); }
    [data-testid="stForm"] h4 { margin: 1.35rem 0 .85rem; padding-top: 1rem; border-top: 1px solid #e7eeeb; color: var(--teal); font-family: 'DM Mono', monospace; font-size: .7rem; font-weight: 500; letter-spacing: .08em; text-transform: uppercase; }
    [data-testid="stForm"] h4:first-child { margin-top: 0; padding-top: 0; border-top: 0; }
    [data-testid="stWidgetLabel"] p { color: #3e565a; font-size: .84rem; font-weight: 600; }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-baseweb="select"] > div { border-radius: .5rem !important; border-color: #cddbd7 !important; background: #fcfdfc !important; }
    [data-testid="stFileUploader"] { background: #fff; border: 1px dashed #a7c8bf; border-radius: 14px; padding: .7rem; }
    [data-testid="stFileUploaderDropzone"] { min-height: 180px; border: 0 !important; background: linear-gradient(135deg, #f4fbf8, #fbfdfc) !important; border-radius: 10px; }
    [data-testid="stFileUploaderDropzone"] small { color: var(--muted) !important; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    [data-testid="stAlert"] { border-radius: 11px; border-width: 1px; }

    .badge {
        display: inline-block; padding: .19rem .6rem; border-radius: 999px;
        font-family: 'DM Mono', monospace; font-size: .66rem; font-weight: 500; letter-spacing: .025em;
    }
    .badge-pass { background: #ecfdf5; color: #047857; }
    .badge-fail { background: #fef2f2; color: #b91c1c; }
    .badge-review { background: #fffbeb; color: #b45309; }
    .badge-missing { background: #f3f4f6; color: #6b7280; }

    .risk-card {
        border-left: 4px solid #d1d5db; background: #fff; border-radius: 8px;
        padding: .85rem 1rem; margin-bottom: .65rem; box-shadow: 0 2px 7px rgba(17,49,46,.03);
    }
    .risk-warning { border-left-color: #dc2626; background: #fef2f2; }
    .risk-review { border-left-color: #d97706; background: #fffbeb; }
    .risk-info { border-left-color: #6b7280; background: #f9fafb; }

    .evidence-card {
        border: 1px solid var(--line); border-radius: 10px; padding: .85rem 1rem;
        margin-bottom: .65rem; background: #fff;
    }
    .evidence-meta { color: #6b7280; font-size: 0.78rem; margin-bottom: 0.25rem; }
    .evidence-text { color: #1f2937; font-size: 0.92rem; font-style: italic; }

    .rank-1 { background: linear-gradient(90deg, #e5f4ee 0%, #ffffff 74%); border-left: 4px solid var(--teal); }
    .rank-card {
        border: 1px solid var(--line); border-radius: 11px; padding: 1rem 1.15rem; margin-bottom: .65rem;
        box-shadow: 0 3px 10px rgba(17,49,46,.025);
    }

    .disclaimer-box {
        background: #edf3f0; border-radius: 10px; padding: .85rem 1.05rem; color: #51656a;
        font-size: .82rem; margin-top: 1.5rem; border: 1px solid #d9e5e0;
    }
    div[data-testid="stSidebarNav"] { display: none; }
    .app-subtitle { display: none !important; }
    hr { border-color: var(--line); margin: 1.6rem 0; }
    @media (max-width: 760px) { .block-container { padding: 1.5rem 1rem 3rem; } h1 { font-size: 2rem !important; } }
</style>
"""


def inject_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def metric_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """


def page_header(title: str, description: str, eyebrow: str = "VENDOR INTELLIGENCE") -> None:
    """Render a consistent visual header without affecting page behaviour."""
    st.markdown(
        f'''<div class="page-hero">
            <div class="page-eyebrow">{eyebrow}</div>
            <div class="page-title">{title}</div>
            <p class="page-description">{description}</p>
        </div>''',
        unsafe_allow_html=True,
    )


def section_heading(title: str) -> None:
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    mapping = {
        "PASS": ("badge-pass", "Pass"),
        "FAIL": ("badge-fail", "Fail"),
        "REQUIRES_REVIEW": ("badge-review", "Review"),
        "NOT_SPECIFIED": ("badge-missing", "Not specified"),
    }
    cls, label = mapping.get(status, ("badge-missing", status))
    return f'<span class="badge {cls}">{label}</span>'


def severity_class(severity: str) -> str:
    return {
        "Potential Risk": "risk-warning",
        "Requires Review": "risk-review",
        "Info": "risk-info",
    }.get(severity, "risk-info")


def advisory_footer() -> None:
    st.markdown(
        """
        <div class="disclaimer-box">
        This analysis is AI-assisted decision support, not an autonomous procurement
        decision. Scores and requirement checks are computed deterministically in Python;
        the AI is used only to read unstructured text, extract structured fields, and explain
        findings. Final vendor selection should be reviewed and confirmed by your team.
        </div>
        """,
        unsafe_allow_html=True,
    )
