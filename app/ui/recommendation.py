"""Page 7 — Evidence-grounded AI recommendation."""
from __future__ import annotations

import streamlit as st

from app.ai.recommender import build_recommendation
from app.business_logic.recommendation import select_recommended_vendor
from app.retrieval.retriever import get_recommendation_evidence
from app.ui.styles import advisory_footer
from app.utils.state import (
    get_chroma_store,
    get_groq_client,
    get_recommendation,
    get_vendor_results,
    set_recommendation,
)


def render() -> None:
    st.markdown("## Recommendation")

    results = get_vendor_results()
    valid_results = [v for v in results.values() if not v.extraction_failed]

    if not valid_results:
        st.info("No successfully analyzed vendors yet. Upload proposals to generate a recommendation.")
        return

    recommendation = get_recommendation()

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Generate / Refresh Recommendation", type="primary", width="stretch"):
            with st.spinner("Retrieving evidence and building the recommendation..."):
                _generate(valid_results)
            st.rerun()

    recommendation = get_recommendation()
    if recommendation is None:
        st.info("Click **Generate / Refresh Recommendation** to produce the AI-assisted recommendation.")
        return

    badge = "🤖 AI-generated explanation" if recommendation.generated_by == "ai" else "⚙ Deterministic fallback explanation (Groq unavailable)"
    st.caption(badge)

    if recommendation.recommended_vendor is None:
        st.error("No vendor could be recommended (all documents failed processing).")
        return

    st.markdown(f"### Recommended Vendor: {recommendation.recommended_vendor}")
    if recommendation.is_forced_choice:
        st.warning("No vendor meets every mandatory requirement. This is the strongest available option, not a full match.")

    st.write(recommendation.summary)

    if recommendation.key_reasons:
        st.markdown("**Why**")
        for reason in recommendation.key_reasons:
            st.markdown(f"- {reason}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Strengths**")
        if recommendation.strengths:
            for s in recommendation.strengths:
                st.markdown(f"- {s}")
        else:
            st.caption("None listed.")
    with c2:
        st.markdown("**Weaknesses / Gaps**")
        if recommendation.weaknesses:
            for w in recommendation.weaknesses:
                st.markdown(f"- {w}")
        else:
            st.caption("None listed.")

    if recommendation.trade_offs:
        st.markdown("**Trade-offs vs. other vendors**")
        for t in recommendation.trade_offs:
            st.markdown(f"- {t}")

    if recommendation.review_items:
        st.markdown("**Important review items**")
        for item in recommendation.review_items:
            st.markdown(f"- ⚠ {item}")

    st.markdown("### Evidence")
    if not recommendation.evidence:
        st.caption("No specific evidence snippets were retrieved for this vendor.")
    for ev in recommendation.evidence:
        st.markdown(
            f"""<div class="evidence-card">
                <div class="evidence-meta">{ev.vendor} · {ev.document or 'document'} · Page {ev.page_number or '?'} · {ev.section or 'General'}</div>
                <div class="evidence-text">"{ev.source_text[:400]}"</div>
            </div>""",
            unsafe_allow_html=True,
        )

    advisory_footer()


def _generate(valid_results) -> None:
    recommended_vendor, is_forced_choice, ranked = select_recommended_vendor(valid_results)
    if recommended_vendor is None:
        set_recommendation_none()
        return

    store = get_chroma_store(st.session_state["project_id"])
    try:
        evidence = get_recommendation_evidence(store, recommended_vendor, top_k=4)
    except Exception:  # noqa: BLE001
        evidence = []

    client = get_groq_client()
    if client is None:
        from app.ai.recommender import _fallback_recommendation

        rec = _fallback_recommendation(recommended_vendor, is_forced_choice, ranked, evidence)
    else:
        rec = build_recommendation(client, recommended_vendor, is_forced_choice, ranked, evidence)

    set_recommendation(rec)


def set_recommendation_none() -> None:
    from app.schemas.analysis import RecommendationResult

    set_recommendation(RecommendationResult(recommended_vendor=None, summary="No vendor could be evaluated."))
