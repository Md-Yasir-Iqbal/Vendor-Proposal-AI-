"""
Deterministic, transparent vendor scoring.

Every sub-score is computed with plain Python arithmetic from the
already-validated requirement-matching results and risk list. The LLM is
never involved in computing these numbers. This is a decision-support
score, not a prediction, probability, or ML-derived rating.
"""
from __future__ import annotations

from typing import List

from app.schemas.analysis import RequirementResult, RequirementStatus, RiskItem, RiskSeverity, ScoreBreakdown
from app.schemas.requirements import RequirementsConfig
from app.schemas.vendor import VendorProposal
from app.utils.helpers import clamp

_STATUS_POINTS = {
    RequirementStatus.PASS: 100.0,
    RequirementStatus.REQUIRES_REVIEW: 60.0,
    RequirementStatus.NOT_SPECIFIED: 30.0,
    RequirementStatus.FAIL: 0.0,
}

_SEVERITY_PENALTY = {
    RiskSeverity.INFO: 3.0,
    RiskSeverity.REVIEW: 8.0,
    RiskSeverity.WARNING: 15.0,
}

_TECHNICAL_KEYS = {"api_integration"}
_COMPLIANCE_KEYS = {"iso27001", "gdpr"}  # folded into technical fit as capability signals


def _budget_subscore(proposal: VendorProposal, requirements: RequirementsConfig) -> float:
    if requirements.max_budget is None:
        return 70.0  # no budget constraint defined; neutral-positive default
    if proposal.total_cost is None:
        return 30.0  # unspecified cost is a meaningful gap, but not an automatic zero
    if proposal.total_cost <= requirements.max_budget:
        # Reward being comfortably under budget, but don't over-reward trivial savings.
        headroom = (requirements.max_budget - proposal.total_cost) / requirements.max_budget
        return clamp(90.0 + min(headroom, 0.10) * 100.0)  # up to 100
    overage_ratio = (proposal.total_cost - requirements.max_budget) / requirements.max_budget
    return clamp(100.0 - overage_ratio * 200.0, 0.0, 100.0)


def _delivery_subscore(proposal: VendorProposal, requirements: RequirementsConfig) -> float:
    if requirements.max_timeline_weeks is None:
        return 70.0
    if proposal.implementation_timeline_weeks is None:
        return 30.0
    if proposal.implementation_timeline_weeks <= requirements.max_timeline_weeks:
        headroom = (requirements.max_timeline_weeks - proposal.implementation_timeline_weeks) / requirements.max_timeline_weeks
        return clamp(90.0 + min(headroom, 0.10) * 100.0)
    overage_ratio = (proposal.implementation_timeline_weeks - requirements.max_timeline_weeks) / requirements.max_timeline_weeks
    return clamp(100.0 - overage_ratio * 200.0, 0.0, 100.0)


def _support_subscore(proposal: VendorProposal, requirements: RequirementsConfig, results: List[RequirementResult]) -> float:
    points = []
    if requirements.min_support_months is not None:
        if proposal.support_duration_months is None:
            points.append(30.0)
        elif proposal.support_duration_months >= requirements.min_support_months:
            points.append(100.0)
        else:
            ratio = proposal.support_duration_months / requirements.min_support_months
            points.append(clamp(ratio * 100.0))
    if requirements.sla_required:
        sla_result = next((r for r in results if r.key == "sla"), None)
        if sla_result:
            points.append(_STATUS_POINTS[sla_result.status])
    if not points:
        return 70.0
    return sum(points) / len(points)


def _technical_fit_subscore(results: List[RequirementResult]) -> float:
    keys = _TECHNICAL_KEYS | _COMPLIANCE_KEYS
    relevant = [r for r in results if r.key in keys]
    custom = [r for r in results if r.key.startswith("custom::")]
    relevant = relevant + custom
    if not relevant:
        return 75.0  # no explicit technical/compliance requirements configured
    return sum(_STATUS_POINTS[r.status] for r in relevant) / len(relevant)


def _risk_subscore(risks: List[RiskItem]) -> float:
    penalty = sum(_SEVERITY_PENALTY[r.severity] for r in risks)
    return clamp(100.0 - penalty, 0.0, 100.0)


def compute_score(
    proposal: VendorProposal,
    requirement_results: List[RequirementResult],
    risks: List[RiskItem],
    requirements: RequirementsConfig,
) -> ScoreBreakdown:
    weights = requirements.scoring_weights

    technical_fit = round(_technical_fit_subscore(requirement_results), 1)
    budget = round(_budget_subscore(proposal, requirements), 1)
    delivery = round(_delivery_subscore(proposal, requirements), 1)
    support = round(_support_subscore(proposal, requirements, requirement_results), 1)
    risk = round(_risk_subscore(risks), 1)

    total = (
        technical_fit * weights.technical_fit
        + budget * weights.budget
        + delivery * weights.delivery_timeline
        + support * weights.support_sla
        + risk * weights.risk
    ) / 100.0

    return ScoreBreakdown(
        technical_fit=technical_fit,
        budget=budget,
        delivery_timeline=delivery,
        support_sla=support,
        risk=risk,
        weights_used=weights.as_dict(),
        total_score=round(total, 1),
    )


def rank_vendors(vendor_scores: dict) -> list:
    """vendor_scores: {vendor_name: ScoreBreakdown}. Returns names sorted best-first."""
    return sorted(vendor_scores.keys(), key=lambda v: vendor_scores[v].total_score, reverse=True)
