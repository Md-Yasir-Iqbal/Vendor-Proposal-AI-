"""Shared CSS and small UI-rendering helpers so every page looks consistent."""
from __future__ import annotations

import streamlit as st

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');

    :root { --ink: #192d34; --muted: #63767b; --line: #dbe5e2; --cream: #f7f9f6; --teal: #087b71; --teal-dark: #055c56; --mint: #e5f4ee; --gold: #e9b949; }
    html, body { color-scheme: light; }
    .stApp { background: var(--cream); color: var(--ink); font-family: 'DM Sans', sans-serif; }
    .stApp:has(.auth-page-label) { background: radial-gradient(circle at 12% 16%, rgba(92,181,140,.12) 0, rgba(92,181,140,0) 25rem), radial-gradient(circle at 86% 88%, rgba(233,185,73,.13) 0, rgba(233,185,73,0) 24rem), #f7f9f6; }
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
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { color: #192d34 !important; caret-color: #087b71 !important; -webkit-text-fill-color: #192d34 !important; }
    [data-testid="stTextInput"] input::placeholder { color: #7c8e94 !important; opacity: 1 !important; -webkit-text-fill-color: #7c8e94 !important; }
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
    .risk-vendor { margin-bottom: .35rem; color: var(--teal); font-family: 'DM Mono', monospace; font-size: .65rem; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; }
    .risk-meta { display: inline-block; margin-left: .45rem; color: #718287; font-size: .74rem; }
    .risk-card p { margin: .55rem 0 .25rem; color: #53676b; line-height: 1.5; }
    .risk-evidence { margin-top: .65rem; padding: .65rem .75rem; border-radius: .45rem; background: rgba(255,255,255,.66); color: #60757a; font-size: .78rem; font-style: italic; line-height: 1.45; }
    .history-row { min-height: 3.9rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: .65rem; padding: .9rem 1rem; border: 1px solid var(--line); border-radius: 11px; background: #fff; box-shadow: 0 3px 10px rgba(17,49,46,.025); }
    .history-row b { color: var(--ink); font-size: .95rem; }.history-row span { color: var(--muted); font-size: .78rem; }

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
    .auth-topline { position: fixed; inset: 0 0 auto; height: 5px; background: #087b71; z-index: 9999; }
    .auth-page-label { margin: .25rem 0 2.7rem; color: #78908e; font-family: 'DM Mono', monospace; font-size: .63rem; letter-spacing: .1em; }
    .auth-showcase { min-height: 650px; box-sizing: border-box; padding: 3.25rem; border-radius: 22px; color: #eaf5f1; background: #10343a; box-shadow: 0 25px 65px rgba(13,45,48,.16); }
    .auth-overline { display: flex; align-items: center; gap: .55rem; color: #9ed2c4; font-family: 'DM Mono', monospace; font-size: .68rem; letter-spacing: .12em; }
    .auth-overline span { width: 1.65rem; height: 1px; background: #e9b949; }
    .auth-showcase h1 { max-width: 610px; margin: 2.1rem 0 1.15rem; color: #f3f8f6; font-family: 'Newsreader', serif; font-size: clamp(2.6rem, 4vw, 4.1rem) !important; font-weight: 500; line-height: 1.02; }
    .auth-showcase h1 em { color: #e9b949; font-style: italic; }
    .auth-showcase > p { max-width: 530px; margin: 0; color: #bdd0cc; font-size: 1.05rem; line-height: 1.65; }
    .auth-feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; margin-top: 2.45rem; }
    .auth-feature-grid div { min-height: 108px; padding: .9rem; border: 1px solid rgba(217,239,232,.14); border-radius: 10px; background: rgba(255,255,255,.045); }
    .feature-icon { display: inline-grid; place-items: center; width: 1.65rem; height: 1.15rem; margin-bottom: .65rem; border-radius: 3px; color: #e9b949; background: rgba(233,185,73,.11); font-family: 'DM Mono', monospace; font-size: .56rem; font-style: normal; letter-spacing: .05em; }
    .auth-feature-grid b { display: block; margin-bottom: .35rem; color: #eef7f3; font-size: .83rem; }
    .auth-feature-grid span { color: #a8c0ba; font-size: .75rem; line-height: 1.4; }
    .auth-intelligence-preview { margin-top: 1.5rem; padding: 1rem 1.05rem; border: 1px solid rgba(217,239,232,.17); border-radius: 11px; background: #0d2d32; }
    .preview-head { display: flex; justify-content: space-between; margin-bottom: .75rem; color: #8bb1a8; font-family: 'DM Mono', monospace; font-size: .58rem; letter-spacing: .09em; }
    .preview-head b { color: #d8eae5; font-family: 'DM Sans', sans-serif; font-size: .67rem; letter-spacing: 0; }
    .preview-row { display: grid; grid-template-columns: 1.4rem minmax(0,1fr) 2.1rem 4.9rem; align-items: center; gap: .45rem; min-height: 1.75rem; color: #b9d0ca; font-size: .72rem; }
    .preview-rank { color: #719790; font-family: 'DM Mono', monospace; font-size: .6rem; }
    .preview-vendor { color: #dcebe6; font-weight: 600; }
    .preview-vendor small { margin-left: .3rem; color: #e9b949; font-size: .6rem; font-weight: 500; }
    .preview-row strong { color: #eff7f4; font-family: 'DM Mono', monospace; font-size: .65rem; text-align: right; }
    .preview-bar { height: .26rem; overflow: hidden; border-radius: 99px; background: rgba(255,255,255,.1); }
    .preview-bar i { display: block; height: 100%; border-radius: inherit; background: #5cb58c; }
    .preview-winner .preview-bar i { background: #e9b949; }
    .auth-trust { display: flex; align-items: center; gap: .5rem; margin-top: 1.35rem; color: #90afa7; font-size: .77rem; }
    .auth-trust-dot { width: .45rem; height: .45rem; border-radius: 50%; background: #5cb58c; box-shadow: 0 0 0 4px rgba(92,181,140,.13); }
    .auth-access-heading { display: flex; flex-wrap: wrap; align-items: center; column-gap: .85rem; row-gap: .38rem; margin: 3.35rem 0 2.25rem; }
    .auth-access-copy { flex-basis: 100%; margin-left: 3.85rem; color: #71878a; font-size: .86rem; }
    .auth-brand { text-align: center; margin: 10vh 0 1.6rem; }
    .auth-mark { display: grid; flex: 0 0 auto; place-items: center; width: 3rem; height: 3rem; margin: 0; border-radius: .8rem; background: #e9b949; color: #183139; font-family: 'DM Mono', monospace; font-size: .85rem; font-weight: 600; box-shadow: 0 6px 14px rgba(233,185,73,.2); }
    .auth-name { color: var(--ink); font-size: 1.1rem; font-weight: 700; letter-spacing: -.03em; }
    .auth-kicker { margin-top: .2rem; color: var(--teal); font-family: 'DM Mono', monospace; font-size: .62rem; letter-spacing: .12em; }
    .auth-brand h1 { margin: 1.7rem 0 .45rem; font-size: 2.3rem !important; }
    .auth-brand p { margin: 0 auto; max-width: 420px; color: var(--muted); font-size: .95rem; }
    [data-testid="stTabs"] { margin-top: .4rem; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 1.25rem; border-bottom-color: var(--line); }
    [data-testid="stTabs"] button { height: 2.7rem; color: var(--muted); font-weight: 600; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--teal); }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--teal); }
    [data-testid="stTabs"] [data-testid="stForm"] { margin-top: .6rem; }
    [data-testid="stTabs"] [data-testid="stForm"] { padding: 1.5rem; border-radius: 15px; box-shadow: 0 12px 30px rgba(17,49,46,.06); }
    [data-testid="stTabs"] [data-testid="stForm"] h4 { color: var(--ink); font-family: 'DM Sans', sans-serif; font-size: 1.08rem; letter-spacing: -.025em; text-transform: none; }
    [data-testid="stTabs"] [data-testid="stForm"] .stButton button { margin-top: .5rem; }
    [data-testid="stTabs"] button[data-testid="stBaseButton-primary"] { background: #087b71; border-color: #087b71; box-shadow: 0 9px 18px rgba(8,123,113,.18); }
    [data-testid="stTabs"] button[data-testid="stBaseButton-primary"]:hover { background: #055c56; border-color: #055c56; }
    [data-testid="stFormSubmitButton"] button { background: #087b71 !important; border-color: #087b71 !important; box-shadow: 0 9px 18px rgba(8,123,113,.18); }
    [data-testid="stFormSubmitButton"] button:hover { background: #055c56 !important; border-color: #055c56 !important; }
    .auth-footnote { margin: 1rem 0 2rem; color: #78908e; font-size: .76rem; line-height: 1.45; }

    /* Complete authenticated dark theme. Light mode remains defined above. */
    @media (prefers-color-scheme: dark) {
    .stApp:has([data-testid="stSidebar"]) { background: #0b1219; color: #e7eef1; }
    .stApp:has([data-testid="stSidebar"]) .main { background: radial-gradient(circle at 78% -12%, rgba(30,118,119,.18), transparent 28rem), #0b1219; }
    .stApp:has([data-testid="stSidebar"]) .block-container { max-width: 1380px; }
    .stApp:has([data-testid="stSidebar"]) h1,
    .stApp:has([data-testid="stSidebar"]) h2,
    .stApp:has([data-testid="stSidebar"]) h3,
    .stApp:has([data-testid="stSidebar"]) [data-testid="stMarkdownContainer"] { color: #e7eef1; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stMarkdownContainer"] p { color: #adbdc4; }
    .stApp:has([data-testid="stSidebar"]) .page-hero { border-color: #23434b; background: linear-gradient(115deg, #112a31 0%, #101d26 58%, #171b22 100%); box-shadow: 0 15px 38px rgba(0,0,0,.2); }
    .stApp:has([data-testid="stSidebar"]) .page-hero:after { border-color: rgba(105,205,191,.18); box-shadow: 0 0 0 1.7rem rgba(36,130,124,.07), 0 0 0 3.4rem rgba(36,130,124,.04); }
    .stApp:has([data-testid="stSidebar"]) .page-eyebrow { color: #71d6c2; }
    .stApp:has([data-testid="stSidebar"]) .page-title { color: #f2f7f7; }
    .stApp:has([data-testid="stSidebar"]) .page-description { color: #a9c0c3; }
    .stApp:has([data-testid="stSidebar"]) .section-heading { color: #e8f1f1; }
    .stApp:has([data-testid="stSidebar"]) .section-heading:after { background: #243942; }
    .stApp:has([data-testid="stSidebar"]) .metric-card,
    .stApp:has([data-testid="stSidebar"]) .content-panel,
    .stApp:has([data-testid="stSidebar"]) .rank-card,
    .stApp:has([data-testid="stSidebar"]) .evidence-card,
    .stApp:has([data-testid="stSidebar"]) [data-testid="stForm"],
    .stApp:has([data-testid="stSidebar"]) [data-testid="stFileUploader"],
    .stApp:has([data-testid="stSidebar"]) [data-testid="stVerticalBlockBorderWrapper"] { background: #111c25; border-color: #263c46; box-shadow: 0 9px 24px rgba(0,0,0,.16); }
    .stApp:has([data-testid="stSidebar"]) .metric-card { position: relative; overflow: hidden; }
    .stApp:has([data-testid="stSidebar"]) .metric-card:before { content: ''; position: absolute; inset: 0 auto 0 0; width: 3px; background: #3cb99d; }
    .stApp:has([data-testid="stSidebar"]) .metric-label { color: #88a2aa; }
    .stApp:has([data-testid="stSidebar"]) .metric-value { color: #eff7f5; }
    .stApp:has([data-testid="stSidebar"]) .metric-sub,
    .stApp:has([data-testid="stSidebar"]) .evidence-meta { color: #89a0a8; }
    .stApp:has([data-testid="stSidebar"]) .panel-kicker { color: #71d6c2; }
    .stApp:has([data-testid="stSidebar"]) .panel-title { color: #edf5f3; }
    .stApp:has([data-testid="stSidebar"]) .workflow-step { color: #afc1c5; }
    .stApp:has([data-testid="stSidebar"]) .workflow-number { background: #173e43; color: #7bdac5; }
    .stApp:has([data-testid="stSidebar"]) .rank-1 { background: linear-gradient(90deg, #153c3e, #111c25 74%); border-left-color: #55cfaf; }
    .stApp:has([data-testid="stSidebar"]) .risk-card { border-left-color: #48626b; background: #111c25; box-shadow: none; }
    .stApp:has([data-testid="stSidebar"]) .risk-warning { background: #2b171b; border-left-color: #f06c72; }
    .stApp:has([data-testid="stSidebar"]) .risk-review { background: #2b2517; border-left-color: #e6b450; }
    .stApp:has([data-testid="stSidebar"]) .risk-info { background: #14212b; border-left-color: #719aaa; }
    .stApp:has([data-testid="stSidebar"]) .evidence-text { color: #cbd8da; }
    .stApp:has([data-testid="stSidebar"]) .badge-pass { background: #123b35; color: #6ee1c0; }
    .stApp:has([data-testid="stSidebar"]) .badge-fail { background: #421f27; color: #ff9ca2; }
    .stApp:has([data-testid="stSidebar"]) .badge-review { background: #3c311b; color: #f4c968; }
    .stApp:has([data-testid="stSidebar"]) .badge-missing { background: #26333c; color: #adbdc4; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stWidgetLabel"] p { color: #c8d8da; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stTextInput"] input,
    .stApp:has([data-testid="stSidebar"]) [data-testid="stNumberInput"] input,
    .stApp:has([data-testid="stSidebar"]) [data-baseweb="select"] > div { color: #edf5f3 !important; border-color: #304650 !important; background: #0d171f !important; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stTextInput"] input:focus,
    .stApp:has([data-testid="stSidebar"]) [data-testid="stNumberInput"] input:focus { border-color: #49bda4 !important; box-shadow: 0 0 0 1px #49bda4 !important; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stFileUploaderDropzone"] { background: #0d171f !important; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stFileUploaderDropzone"] * { color: #b3c7c8 !important; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stAlert"] { border-color: #294451; background: #14242d; color: #d0e0e0; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stDataFrame"] { border-color: #304650; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stSidebar"] { background: linear-gradient(180deg, #0c171f 0%, #091218 100%); border-right: 1px solid #20333d; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: linear-gradient(90deg, rgba(73,189,164,.18), rgba(73,189,164,.04)); border-left: 2px solid #52c9ae; border-radius: 0 .45rem .45rem 0; }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.06); }
    .stApp:has([data-testid="stSidebar"]) [data-testid="stSidebar"] .stButton button { border-color: #35515b; }
    .stApp:has([data-testid="stSidebar"]) .disclaimer-box { background: #14242d; border-color: #294451; color: #afc1c5; }
    }

    /* Inactive legacy mixed-theme fallback; the complete dark system above owns Dark mode. */
    @media (max-width: 0px) {
        html, body, .stApp { color-scheme: light !important; background: #f7f9f6 !important; }
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #f7f9f6 !important; }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-baseweb="input"] input,
        [data-baseweb="select"] > div { color: #192d34 !important; background: #fcfdfc !important; -webkit-text-fill-color: #192d34 !important; }
        [data-testid="stNumberInput"] button { color: #26383f !important; background: #eef2f4 !important; }
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCheckbox"] label span,
        [data-testid="stMarkdownContainer"] p { color: #29424a !important; }
        [data-testid="stDataFrame"] { background: #fff !important; }
    }
    hr { border-color: var(--line); margin: 1.6rem 0; }
    @media (max-width: 760px) { .block-container { padding: 1.5rem 1rem 3rem; } h1 { font-size: 2rem !important; } .auth-page-label { margin-bottom: 1rem; } .auth-showcase { min-height: auto; padding: 2rem 1.5rem; } .auth-showcase h1 { font-size: 2.65rem !important; } .auth-feature-grid { grid-template-columns: 1fr; margin-top: 2rem; } .auth-access-heading { margin: 2rem 0 1.5rem; } .auth-access-copy { margin-left: 0; } .auth-intelligence-preview { display: none; } }
</style>
"""


DARK_WORKSPACE_CSS = """
<style>
/* Explicit workspace dark mode, independent of Streamlit's built-in menu theme. */
.stApp:has(.workspace-dark) { background: #0b1219 !important; color: #e7eef1; }
.stApp:has(.workspace-dark) .main { background: radial-gradient(circle at 78% -12%, rgba(30,118,119,.18), transparent 28rem), #0b1219; }
.stApp:has(.workspace-dark) h1, .stApp:has(.workspace-dark) h2, .stApp:has(.workspace-dark) h3, .stApp:has(.workspace-dark) [data-testid="stMarkdownContainer"] { color: #e7eef1; }
.stApp:has(.workspace-dark) [data-testid="stMarkdownContainer"] p { color: #adbdc4; }
.stApp:has(.workspace-dark) .page-hero { border-color: #23434b; background: linear-gradient(115deg, #112a31, #101d26 58%, #171b22); }
.stApp:has(.workspace-dark) .page-title { color: #f2f7f7; }.stApp:has(.workspace-dark) .page-description { color: #a9c0c3; }.stApp:has(.workspace-dark) .page-eyebrow,.stApp:has(.workspace-dark) .panel-kicker { color: #71d6c2; }
.stApp:has(.workspace-dark) .section-heading,.stApp:has(.workspace-dark) .panel-title { color: #edf5f3; }.stApp:has(.workspace-dark) .section-heading:after { background: #243942; }
.stApp:has(.workspace-dark) .metric-card,.stApp:has(.workspace-dark) .content-panel,.stApp:has(.workspace-dark) .rank-card,.stApp:has(.workspace-dark) .evidence-card,.stApp:has(.workspace-dark) [data-testid="stForm"],.stApp:has(.workspace-dark) [data-testid="stFileUploader"],.stApp:has(.workspace-dark) [data-testid="stVerticalBlockBorderWrapper"] { background: #111c25; border-color: #263c46; box-shadow: 0 9px 24px rgba(0,0,0,.16); }
.stApp:has(.workspace-dark) .metric-card:before { content:''; position:absolute; inset:0 auto 0 0; width:3px; background:#3cb99d; }.stApp:has(.workspace-dark) .metric-card { position:relative; overflow:hidden; }.stApp:has(.workspace-dark) .metric-label,.stApp:has(.workspace-dark) .metric-sub,.stApp:has(.workspace-dark) .evidence-meta { color:#89a0a8; }.stApp:has(.workspace-dark) .metric-value { color:#eff7f5; }
.stApp:has(.workspace-dark) .rank-1 { background:linear-gradient(90deg,#153c3e,#111c25 74%); border-left-color:#55cfaf; }.stApp:has(.workspace-dark) .risk-card { background:#111c25; border-left-color:#48626b; }.stApp:has(.workspace-dark) .risk-warning { background:#2b171b; border-left-color:#f06c72; }.stApp:has(.workspace-dark) .risk-review { background:#2b2517; border-left-color:#e6b450; }.stApp:has(.workspace-dark) .risk-info { background:#14212b; border-left-color:#719aaa; }.stApp:has(.workspace-dark) .evidence-text { color:#cbd8da; }
.stApp:has(.workspace-dark) .badge-pass { background:#123b35; color:#6ee1c0; }.stApp:has(.workspace-dark) .badge-fail { background:#421f27; color:#ff9ca2; }.stApp:has(.workspace-dark) .badge-review { background:#3c311b; color:#f4c968; }.stApp:has(.workspace-dark) .badge-missing { background:#26333c; color:#adbdc4; }
.stApp:has(.workspace-dark) .history-row { background:#111c25; border-color:#263c46; }.stApp:has(.workspace-dark) .history-row b { color:#e7eef1; }.stApp:has(.workspace-dark) .history-row span,.stApp:has(.workspace-dark) .risk-meta,.stApp:has(.workspace-dark) .risk-card p { color:#adbdc4; }.stApp:has(.workspace-dark) .risk-evidence { background:#0d171f; color:#b7c7c9; }
.stApp:has(.workspace-dark) [data-testid="stWidgetLabel"] p,.stApp:has(.workspace-dark) [data-testid="stCheckbox"] label span { color:#c8d8da !important; }
.stApp:has(.workspace-dark) [data-testid="stTextInput"] input,.stApp:has(.workspace-dark) [data-testid="stNumberInput"] input,.stApp:has(.workspace-dark) [data-baseweb="select"] > div { color:#edf5f3 !important; -webkit-text-fill-color:#edf5f3 !important; border-color:#304650 !important; background:#0d171f !important; caret-color:#70d8c1; }
.stApp:has(.workspace-dark) [data-testid="stNumberInput"] button { color:#c9d8d9 !important; background:#17252f !important; border-color:#304650 !important; }.stApp:has(.workspace-dark) [data-testid="stCheckbox"] input { accent-color:#48bca2; }
.stApp:has(.workspace-dark) [data-testid="stFileUploaderDropzone"] { background:#0d171f !important; }.stApp:has(.workspace-dark) [data-testid="stFileUploaderDropzone"] * { color:#b3c7c8 !important; }.stApp:has(.workspace-dark) [data-testid="stAlert"],.stApp:has(.workspace-dark) .disclaimer-box { background:#14242d; border-color:#294451; color:#d0e0e0; }
.stApp:has(.workspace-dark) [data-testid="stSidebar"] { background:linear-gradient(180deg,#0c171f,#091218); border-right:1px solid #20333d; }.stApp:has(.workspace-dark) [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background:linear-gradient(90deg,rgba(73,189,164,.18),rgba(73,189,164,.04)); border-left:2px solid #52c9ae; }
.stApp:has(.workspace-dark) [data-testid="stFormSubmitButton"] button,.stApp:has(.workspace-dark) .stButton button[kind="primary"] { color:#061316; background:#5fd0b4; border-color:#5fd0b4; }.stApp:has(.workspace-dark) [data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#36a98f,#70d8c1) !important; }
</style>
"""


def inject_css(dark_workspace: bool = False) -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(DARK_WORKSPACE_CSS, unsafe_allow_html=True)
    if dark_workspace:
        st.markdown('<div class="workspace-dark"></div>', unsafe_allow_html=True)


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
