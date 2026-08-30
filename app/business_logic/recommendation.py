"""
Deterministic selection of the recommended vendor.

The LLM never decides which vendor wins -- it only explains the decision
made here, in Python, from the computed scores and requirement results.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from app.schemas.analysis import VendorAnalysisResult


def select_recommended_vendor(
    results: List[VendorAnalysisResult],
) -> Tuple[Optional[str], bool, List[VendorAnalysisResult]]:
    """
    Returns (recommended_vendor_name, is_forced_choice, ranked_results).

    Preference order:
    1. Among vendors with no mandatory-requirement failures, pick the
       highest overall score.
    2. If every vendor has at least one mandatory failure, fall back to
       the highest overall score anyway, and flag is_forced_choice=True
       so the UI and recommendation text can warn the user clearly.
    """
    if not results:
        return None, False, []

    ranked_all = sorted(results, key=lambda r: r.score.total_score, reverse=True)
    eligible = [r for r in ranked_all if not r.has_mandatory_failure and not r.extraction_failed]

    if eligible:
        eligible_ranked = sorted(eligible, key=lambda r: r.score.total_score, reverse=True)
        return eligible_ranked[0].vendor_name, False, ranked_all

    usable = [r for r in ranked_all if not r.extraction_failed]
    if usable:
        return usable[0].vendor_name, True, ranked_all

    return None, True, ranked_all
