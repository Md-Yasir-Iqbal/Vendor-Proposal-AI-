"""Helpers for building/validating the user-configured RequirementsConfig."""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.schemas.requirements import RequirementsConfig, ScoringWeights


class RequirementsConfigError(Exception):
    pass


def build_requirements_config(
    project_name: str,
    max_budget: Optional[float],
    max_timeline_weeks: Optional[float],
    min_support_months: Optional[float],
    api_integration_required: bool,
    sla_required: bool,
    iso27001_required: bool,
    gdpr_required: bool,
    weight_technical: float,
    weight_budget: float,
    weight_delivery: float,
    weight_support: float,
    weight_risk: float,
) -> RequirementsConfig:
    """Validate raw UI inputs into a RequirementsConfig, raising a friendly error on failure."""
    try:
        weights = ScoringWeights(
            technical_fit=weight_technical,
            budget=weight_budget,
            delivery_timeline=weight_delivery,
            support_sla=weight_support,
            risk=weight_risk,
        )
        return RequirementsConfig(
            project_name=project_name,
            max_budget=max_budget if max_budget and max_budget > 0 else None,
            max_timeline_weeks=max_timeline_weeks if max_timeline_weeks and max_timeline_weeks > 0 else None,
            min_support_months=min_support_months if min_support_months and min_support_months > 0 else None,
            api_integration_required=api_integration_required,
            sla_required=sla_required,
            iso27001_required=iso27001_required,
            gdpr_required=gdpr_required,
            scoring_weights=weights,
        )
    except ValidationError as exc:
        raise RequirementsConfigError(_friendly_validation_message(exc)) from exc


def _friendly_validation_message(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"])
        lines.append(f"{field}: {err['msg']}")
    return "Invalid requirement configuration:\n" + "\n".join(lines)
