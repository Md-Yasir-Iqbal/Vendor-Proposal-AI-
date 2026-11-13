"""Regression coverage for graceful recommendation fallback when Groq fails."""
from __future__ import annotations

from app.ai.groq_client import GroqServiceError
from app.ai.recommender import build_recommendation
from app.business_logic.recommendation import select_recommended_vendor
from app.schemas.analysis import ScoreBreakdown, VendorAnalysisResult
from app.schemas.vendor import VendorProposal


class _UnavailableGroqClient:
    """Test double that simulates an unreachable Groq service."""

    def chat_json(self, *_args, **_kwargs):
        raise GroqServiceError("Simulated Groq outage")


def _result(vendor_name: str, score: float) -> VendorAnalysisResult:
    return VendorAnalysisResult(
        vendor_name=vendor_name,
        proposal=VendorProposal(vendor_name=vendor_name),
        score=ScoreBreakdown(total_score=score, budget=90, delivery_timeline=85),
    )


def test_recommendation_uses_deterministic_fallback_when_groq_is_unavailable():
    """Test Case 12: LLM outage must not change deterministic vendor selection."""
    results = [_result("Best Vendor", 92.0), _result("Runner Up", 81.0)]
    selected_vendor, is_forced_choice, ranked = select_recommended_vendor(results)

    recommendation = build_recommendation(
        _UnavailableGroqClient(), selected_vendor, is_forced_choice, ranked, evidence=[]
    )

    assert selected_vendor == "Best Vendor"
    assert recommendation.generated_by == "fallback"
    assert recommendation.recommended_vendor == selected_vendor
    assert "Best Vendor is recommended" in recommendation.summary
