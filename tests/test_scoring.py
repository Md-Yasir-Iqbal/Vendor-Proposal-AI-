"""Vendor scoring and ranking tests."""
from app.business_logic.matching import match_requirements
from app.business_logic.risk_rules import detect_rule_based_risks
from app.business_logic.scoring import compute_score, rank_vendors
from app.schemas.requirements import RequirementsConfig, ScoringWeights
from app.schemas.vendor import VendorProposal


def _score(proposal, requirements):
    results = match_requirements(proposal, requirements)
    risks = detect_rule_based_risks(proposal, requirements)
    return compute_score(proposal, results, risks, requirements)


def test_total_score_is_weighted_sum_within_bounds(sample_requirements):
    proposal = VendorProposal(
        total_cost=800_000, implementation_timeline_weeks=6, support_duration_months=18,
        api_integration_supported=True, sla="99.9% uptime guarantee",
        iso27001_certified=True, gdpr_compliant=True,
    )
    score = _score(proposal, sample_requirements)
    assert 0 <= score.total_score <= 100
    assert score.weights_used["technical_fit"] == sample_requirements.scoring_weights.technical_fit


def test_better_vendor_scores_higher(sample_requirements):
    strong = VendorProposal(
        total_cost=700_000, implementation_timeline_weeks=5, support_duration_months=18,
        api_integration_supported=True, sla="99.9% uptime guaranteed",
        iso27001_certified=True, gdpr_compliant=True,
    )
    weak = VendorProposal(
        total_cost=1_400_000, implementation_timeline_weeks=14, support_duration_months=2,
        api_integration_supported=False, sla=None, iso27001_certified=False, gdpr_compliant=False,
    )
    strong_score = _score(strong, sample_requirements)
    weak_score = _score(weak, sample_requirements)
    assert strong_score.total_score > weak_score.total_score


def test_weights_affect_total_score():
    requirements_budget_heavy = RequirementsConfig(
        project_name="Test", max_budget=1_000_000,
        scoring_weights=ScoringWeights(technical_fit=0, budget=100, delivery_timeline=0, support_sla=0, risk=0),
    )
    cheap_but_weak_tech = VendorProposal(total_cost=500_000, api_integration_supported=False)
    score = _score(cheap_but_weak_tech, requirements_budget_heavy)
    # With 100% weight on budget and a comfortable budget fit, total score should be high
    # regardless of technical fit, since technical_fit weight is 0.
    assert score.total_score >= 85


def test_rank_vendors_orders_best_first(sample_requirements):
    a = _score(VendorProposal(total_cost=700_000, implementation_timeline_weeks=5, support_duration_months=18,
                               api_integration_supported=True, sla="99.9% uptime", iso27001_certified=True,
                               gdpr_compliant=True), sample_requirements)
    b = _score(VendorProposal(total_cost=1_500_000, implementation_timeline_weeks=14), sample_requirements)
    ranking = rank_vendors({"A": a, "B": b})
    assert ranking == ["A", "B"]


def test_missing_information_lowers_score_but_not_to_zero(sample_requirements):
    empty_proposal = VendorProposal()
    score = _score(empty_proposal, sample_requirements)
    assert 0 < score.total_score < 60
