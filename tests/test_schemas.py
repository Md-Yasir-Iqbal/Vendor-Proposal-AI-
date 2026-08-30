"""Pydantic schema validation tests."""
import pytest
from pydantic import ValidationError

from app.schemas.requirements import RequirementsConfig, ScoringWeights
from app.schemas.vendor import VendorProposal


def test_valid_vendor_proposal_parses():
    data = {
        "vendor_name": "Vendor A",
        "total_cost": "8,00,000",  # deliberately messy, like a raw model output
        "implementation_timeline_weeks": "6",
        "features": ["Ticketing", "Live chat"],
        "api_integration_supported": True,
    }
    proposal = VendorProposal.model_validate(data)
    assert proposal.vendor_name == "Vendor A"
    assert proposal.total_cost == 800000.0
    assert proposal.implementation_timeline_weeks == 6.0
    assert proposal.api_integration_supported is True


def test_missing_fields_default_to_none_or_empty():
    proposal = VendorProposal.model_validate({})
    assert proposal.vendor_name is None
    assert proposal.total_cost is None
    assert proposal.features == []
    assert proposal.api_integration_supported is None


def test_not_specified_string_treated_as_none():
    proposal = VendorProposal.model_validate({"total_cost": "Not specified", "support_duration_months": "n/a"})
    assert proposal.total_cost is None
    assert proposal.support_duration_months is None


def test_malformed_numeric_field_does_not_crash():
    proposal = VendorProposal.model_validate({"total_cost": "please contact sales for pricing"})
    assert proposal.total_cost is None


def test_scoring_weights_normalize_to_100():
    weights = ScoringWeights(technical_fit=60, budget=60, delivery_timeline=0, support_sla=0, risk=0)
    total = weights.technical_fit + weights.budget + weights.delivery_timeline + weights.support_sla + weights.risk
    assert abs(total - 100.0) < 0.01
    assert weights.technical_fit == 50.0
    assert weights.budget == 50.0


def test_scoring_weights_all_zero_rejected():
    with pytest.raises(ValidationError):
        ScoringWeights(technical_fit=0, budget=0, delivery_timeline=0, support_sla=0, risk=0)


def test_requirements_config_requires_project_name():
    with pytest.raises(ValidationError):
        RequirementsConfig(project_name="")


def test_requirements_config_valid():
    config = RequirementsConfig(project_name="Test Project", max_budget=500000)
    assert config.project_name == "Test Project"
    assert config.max_budget == 500000
    assert config.max_timeline_weeks is None
