"""
Generates the human-readable recommendation explanation.

IMPORTANT: the recommended vendor itself is chosen deterministically in
`app.business_logic.recommendation` from the Python-computed scores and
requirement results -- never by the LLM. This module only asks the LLM to
write the narrative explanation, and falls back to a template-based
explanation if the LLM is unavailable or fails.
"""
from __future__ import annotations

import json
from typing import Dict, List

from app.ai.groq_client import GroqClient, GroqClientError, GroqMalformedResponseError, parse_json_response
from app.ai.prompts import RECOMMENDATION_SYSTEM_PROMPT, RECOMMENDATION_USER_TEMPLATE
from app.schemas.analysis import RecommendationResult, VendorAnalysisResult
from app.schemas.evidence import EvidenceSnippet
from app.utils.logging import get_logger

logger = get_logger("recommender")


def _vendor_summary_for_prompt(result: VendorAnalysisResult) -> dict:
    return {
        "vendor_name": result.vendor_name,
        "overall_score": result.score.total_score,
        "score_breakdown": {
            "technical_fit": result.score.technical_fit,
            "budget": result.score.budget,
            "delivery_timeline": result.score.delivery_timeline,
            "support_sla": result.score.support_sla,
            "risk": result.score.risk,
        },
        "requirement_results": [
            {"requirement": r.label, "status": r.status.value, "vendor_value": r.vendor_value}
            for r in result.requirement_results
        ],
        "risks": [
            {"category": r.category, "severity": r.severity.value, "description": r.description}
            for r in result.risks
        ],
        "missing_information": result.missing_information,
        "has_mandatory_failure": result.has_mandatory_failure,
    }


def build_recommendation(
    client: GroqClient,
    recommended_vendor: str,
    is_forced_choice: bool,
    ranked_results: List[VendorAnalysisResult],
    evidence: List[EvidenceSnippet],
) -> RecommendationResult:
    """Produce the final RecommendationResult, preferring an AI-written narrative
    but always falling back to a safe deterministic summary."""

    vendor_data = {r.vendor_name: _vendor_summary_for_prompt(r) for r in ranked_results}

    try:
        prompt = RECOMMENDATION_USER_TEMPLATE.format(
            recommended_vendor=recommended_vendor,
            is_forced_choice=is_forced_choice,
            vendor_data=json.dumps(vendor_data, indent=2, default=str),
        )
        raw = client.chat_json(RECOMMENDATION_SYSTEM_PROMPT, prompt, temperature=0.3, max_tokens=1400)
        data = parse_json_response(raw)

        return RecommendationResult(
            recommended_vendor=recommended_vendor,
            is_forced_choice=is_forced_choice,
            summary=str(data.get("summary", "")).strip(),
            key_reasons=[str(x) for x in data.get("key_reasons", [])][:6],
            strengths=[str(x) for x in data.get("strengths", [])][:6],
            weaknesses=[str(x) for x in data.get("weaknesses", [])][:6],
            trade_offs=[str(x) for x in data.get("trade_offs", [])][:6],
            review_items=[str(x) for x in data.get("review_items", [])][:6],
            evidence=evidence,
            generated_by="ai",
        )
    except (GroqClientError, GroqMalformedResponseError) as exc:
        logger.info("Falling back to deterministic recommendation summary: %s", exc)
        return _fallback_recommendation(recommended_vendor, is_forced_choice, ranked_results, evidence)


def _fallback_recommendation(
    recommended_vendor: str,
    is_forced_choice: bool,
    ranked_results: List[VendorAnalysisResult],
    evidence: List[EvidenceSnippet],
) -> RecommendationResult:
    """Pure-Python, template-based recommendation used when the LLM is
    unavailable (no API key, network error, etc.), so the app remains
    fully usable without the AI provider."""
    by_name = {r.vendor_name: r for r in ranked_results}
    top = by_name.get(recommended_vendor)

    if top is None:
        return RecommendationResult(
            recommended_vendor=None,
            summary="No vendor results are available yet.",
            generated_by="fallback",
        )

    key_reasons = []
    if not top.has_mandatory_failure:
        key_reasons.append("Meets all mandatory requirements defined for this project.")
    else:
        key_reasons.append("Selected as the best-scoring option, though it does not meet every mandatory requirement.")
    key_reasons.append(f"Highest overall evaluation score among evaluated vendors ({top.score.total_score:.1f}/100).")
    if top.score.budget >= 80:
        key_reasons.append("Strong budget fit relative to the defined maximum budget.")
    if top.score.delivery_timeline >= 80:
        key_reasons.append("Implementation timeline fits well within requirements.")

    weaknesses = [f"{r.category}: {r.description}" for r in top.risks][:5]
    missing = list(top.missing_information)[:5]

    trade_offs = []
    others = [r for r in ranked_results if r.vendor_name != recommended_vendor]
    if others:
        runner_up = others[0]
        trade_offs.append(
            f"Compared to {runner_up.vendor_name} (score {runner_up.score.total_score:.1f}), "
            f"{recommended_vendor} scored {top.score.total_score - runner_up.score.total_score:+.1f} points higher overall."
        )

    summary = (
        f"{recommended_vendor} is recommended based on the highest overall weighted score "
        f"({top.score.total_score:.1f}/100) among the evaluated vendors."
    )
    if is_forced_choice:
        summary += " Note: no vendor met every mandatory requirement, so this is the best available option, not a full match."

    return RecommendationResult(
        recommended_vendor=recommended_vendor,
        is_forced_choice=is_forced_choice,
        summary=summary,
        key_reasons=key_reasons,
        strengths=[f"Meets requirement: {r.label}" for r in top.requirement_results if r.status.value == "PASS"][:5],
        weaknesses=weaknesses,
        trade_offs=trade_offs,
        review_items=missing + [f"{r.category}: {r.description}" for r in top.risks if r.severity.value == "Requires Review"],
        evidence=evidence,
        generated_by="fallback",
    )
