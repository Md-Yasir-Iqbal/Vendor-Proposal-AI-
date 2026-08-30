"""Requirement matching tests: PASS / FAIL / NOT_SPECIFIED / REQUIRES_REVIEW."""
from app.business_logic.matching import has_mandatory_failure, match_requirements
from app.schemas.analysis import RequirementStatus
from app.schemas.vendor import VendorProposal


def _status_for(results, key):
    return next(r for r in results if r.key == key).status


def test_budget_pass(sample_requirements):
    proposal = VendorProposal(total_cost=800_000)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "budget") == RequirementStatus.PASS


def test_budget_fail(sample_requirements):
    proposal = VendorProposal(total_cost=1_500_000)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "budget") == RequirementStatus.FAIL


def test_budget_not_specified(sample_requirements):
    proposal = VendorProposal(total_cost=None)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "budget") == RequirementStatus.NOT_SPECIFIED


def test_timeline_fail(sample_requirements):
    proposal = VendorProposal(implementation_timeline_weeks=12)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "timeline") == RequirementStatus.FAIL


def test_support_duration_pass(sample_requirements):
    proposal = VendorProposal(support_duration_months=18)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "support_duration") == RequirementStatus.PASS


def test_api_integration_tri_state(sample_requirements):
    passed = match_requirements(VendorProposal(api_integration_supported=True), sample_requirements)
    failed = match_requirements(VendorProposal(api_integration_supported=False), sample_requirements)
    unknown = match_requirements(VendorProposal(api_integration_supported=None), sample_requirements)
    assert _status_for(passed, "api_integration") == RequirementStatus.PASS
    assert _status_for(failed, "api_integration") == RequirementStatus.FAIL
    assert _status_for(unknown, "api_integration") == RequirementStatus.NOT_SPECIFIED


def test_sla_requires_review_on_ambiguous_language(sample_requirements):
    proposal = VendorProposal(sla="We make a best effort to respond, no guarantee of resolution time.")
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "sla") == RequirementStatus.REQUIRES_REVIEW


def test_sla_pass_on_clear_commitment(sample_requirements):
    proposal = VendorProposal(sla="99.9% uptime guarantee with 4 hour response time for critical issues.")
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "sla") == RequirementStatus.PASS


def test_compliance_fail_when_explicitly_false(sample_requirements):
    proposal = VendorProposal(iso27001_certified=False, gdpr_compliant=False)
    results = match_requirements(proposal, sample_requirements)
    assert _status_for(results, "iso27001") == RequirementStatus.FAIL
    assert _status_for(results, "gdpr") == RequirementStatus.FAIL


def test_has_mandatory_failure_true_when_any_required_fails(sample_requirements):
    proposal = VendorProposal(total_cost=2_000_000)  # over budget -> FAIL, budget is required by default
    results = match_requirements(proposal, sample_requirements)
    assert has_mandatory_failure(results) is True


def test_has_mandatory_failure_false_when_all_pass_or_not_specified(sample_requirements):
    proposal = VendorProposal(total_cost=500_000, implementation_timeline_weeks=6, support_duration_months=12,
                               api_integration_supported=True, sla="99.9% uptime SLA",
                               iso27001_certified=True, gdpr_compliant=True)
    results = match_requirements(proposal, sample_requirements)
    assert has_mandatory_failure(results) is False
