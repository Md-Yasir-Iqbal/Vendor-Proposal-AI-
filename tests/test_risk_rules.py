"""Rule-based risk detection tests."""
from app.business_logic.risk_rules import detect_rule_based_risks
from app.schemas.analysis import RiskSeverity
from app.schemas.vendor import VendorProposal


def test_missing_total_cost_flagged_as_risk(sample_requirements):
    proposal = VendorProposal(total_cost=None)
    risks = detect_rule_based_risks(proposal, sample_requirements)
    categories = [r.category for r in risks]
    assert "Missing Information" in categories


def test_recurring_cost_flagged_as_info(sample_requirements):
    proposal = VendorProposal(total_cost=500_000, recurring_cost=20_000, recurring_cost_frequency="monthly")
    risks = detect_rule_based_risks(proposal, sample_requirements)
    recurring = [r for r in risks if r.category == "Recurring Cost"]
    assert len(recurring) == 1
    assert recurring[0].severity == RiskSeverity.INFO


def test_unfavorable_pricing_language_flagged(sample_requirements):
    proposal = VendorProposal(total_cost=500_000, pricing_conditions="Additional charges may apply, subject to change.")
    risks = detect_rule_based_risks(proposal, sample_requirements)
    assert any(r.category == "Pricing Conditions" for r in risks)


def test_missing_certification_flagged_as_warning_when_explicitly_false(sample_requirements):
    proposal = VendorProposal(total_cost=500_000, iso27001_certified=False)
    risks = detect_rule_based_risks(proposal, sample_requirements)
    cert_risks = [r for r in risks if r.related_field == "iso27001_certified"]
    assert len(cert_risks) == 1
    assert cert_risks[0].severity == RiskSeverity.WARNING


def test_every_risk_item_has_required_fields(sample_requirements):
    proposal = VendorProposal(
        total_cost=None, recurring_cost=1000, recurring_cost_frequency="monthly",
        pricing_conditions="subject to change", contract_terms="auto-renew, non-refundable",
        exclusions=["mobile app"], implementation_timeline_weeks=20, support_duration_months=1,
        iso27001_certified=False, gdpr_compliant=False, sla="best effort, no guarantee",
    )
    risks = detect_rule_based_risks(proposal, sample_requirements)
    assert len(risks) > 0
    for r in risks:
        assert r.category
        assert r.severity in (RiskSeverity.INFO, RiskSeverity.REVIEW, RiskSeverity.WARNING)
        assert r.description
        assert r.source == "rule_based"


def test_no_risks_for_a_clean_strong_proposal(sample_requirements):
    proposal = VendorProposal(
        total_cost=700_000, implementation_timeline_weeks=6, support_duration_months=18,
        sla="99.9% uptime guarantee with clear response time commitments",
        iso27001_certified=True, gdpr_compliant=True,
    )
    risks = detect_rule_based_risks(proposal, sample_requirements)
    assert risks == []
