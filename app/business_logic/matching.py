"""
Deterministic requirement matching.

Every comparison here is a plain Python numeric/boolean/string check --
no LLM is involved in deciding PASS/FAIL/NOT_SPECIFIED/REQUIRES_REVIEW.
"""
from __future__ import annotations

from typing import List, Optional

from app.schemas.analysis import RequirementResult, RequirementStatus
from app.schemas.requirements import RequirementsConfig
from app.schemas.vendor import VendorProposal
from app.utils.helpers import format_currency, is_unspecified

# Keywords that suggest SLA/contract language is vague or conditional,
# used only to flag REQUIRES_REVIEW -- never to fabricate detail.
_AMBIGUOUS_SLA_KEYWORDS = [
    "best effort", "no guarantee", "subject to change", "reasonable effort",
    "where possible", "as needed", "may vary",
]


def _tri_state_bool_result(
    key: str, label: str, required: bool, value: Optional[bool]
) -> RequirementResult:
    if not required:
        status = RequirementStatus.PASS if value else (
            RequirementStatus.NOT_SPECIFIED if value is None else RequirementStatus.NOT_SPECIFIED
        )
        return RequirementResult(
            key=key, label=label, required=False, status=RequirementStatus.NOT_SPECIFIED if value is None else (
                RequirementStatus.PASS if value else RequirementStatus.FAIL
            ),
            requirement_value="Not required", vendor_value=_bool_to_text(value),
            explanation="This requirement was marked optional.",
        )
    if value is None:
        return RequirementResult(
            key=key, label=label, required=True, status=RequirementStatus.NOT_SPECIFIED,
            requirement_value="Required", vendor_value="Not specified",
            explanation="The proposal does not explicitly state this.",
        )
    if value is True:
        return RequirementResult(
            key=key, label=label, required=True, status=RequirementStatus.PASS,
            requirement_value="Required", vendor_value="Yes",
            explanation="Explicitly confirmed in the proposal.",
        )
    return RequirementResult(
        key=key, label=label, required=True, status=RequirementStatus.FAIL,
        requirement_value="Required", vendor_value="No",
        explanation="The proposal explicitly states this is not supported/available.",
    )


def _bool_to_text(value: Optional[bool]) -> str:
    if value is None:
        return "Not specified"
    return "Yes" if value else "No"


def match_requirements(proposal: VendorProposal, requirements: RequirementsConfig) -> List[RequirementResult]:
    results: List[RequirementResult] = []

    # --- Budget --------------------------------------------------------------------
    if requirements.max_budget is not None:
        if is_unspecified(proposal.total_cost):
            results.append(RequirementResult(
                key="budget", label="Maximum Budget", required=True, status=RequirementStatus.NOT_SPECIFIED,
                requirement_value=format_currency(requirements.max_budget, requirements.currency_symbol),
                vendor_value="Not specified",
                explanation="Total cost was not found in the proposal.",
            ))
        else:
            passed = proposal.total_cost <= requirements.max_budget
            results.append(RequirementResult(
                key="budget", label="Maximum Budget", required=True,
                status=RequirementStatus.PASS if passed else RequirementStatus.FAIL,
                requirement_value=format_currency(requirements.max_budget, requirements.currency_symbol),
                vendor_value=format_currency(proposal.total_cost, requirements.currency_symbol),
                explanation=(
                    f"Vendor cost is {'within' if passed else 'over'} the maximum budget "
                    f"by {format_currency(abs(requirements.max_budget - proposal.total_cost), requirements.currency_symbol)}."
                ),
            ))

    # --- Timeline --------------------------------------------------------------------
    if requirements.max_timeline_weeks is not None:
        if is_unspecified(proposal.implementation_timeline_weeks):
            results.append(RequirementResult(
                key="timeline", label="Maximum Implementation Time", required=True,
                status=RequirementStatus.NOT_SPECIFIED,
                requirement_value=f"{requirements.max_timeline_weeks:g} weeks",
                vendor_value="Not specified",
                explanation="Implementation timeline was not found in the proposal.",
            ))
        else:
            passed = proposal.implementation_timeline_weeks <= requirements.max_timeline_weeks
            results.append(RequirementResult(
                key="timeline", label="Maximum Implementation Time", required=True,
                status=RequirementStatus.PASS if passed else RequirementStatus.FAIL,
                requirement_value=f"{requirements.max_timeline_weeks:g} weeks",
                vendor_value=f"{proposal.implementation_timeline_weeks:g} weeks",
                explanation=f"Vendor timeline is {'within' if passed else 'over'} the maximum allowed.",
            ))

    # --- Support duration ---------------------------------------------------------------
    if requirements.min_support_months is not None:
        if is_unspecified(proposal.support_duration_months):
            results.append(RequirementResult(
                key="support_duration", label="Minimum Support Period", required=True,
                status=RequirementStatus.NOT_SPECIFIED,
                requirement_value=f"{requirements.min_support_months:g} months",
                vendor_value="Not specified",
                explanation="Support duration was not found in the proposal.",
            ))
        else:
            passed = proposal.support_duration_months >= requirements.min_support_months
            results.append(RequirementResult(
                key="support_duration", label="Minimum Support Period", required=True,
                status=RequirementStatus.PASS if passed else RequirementStatus.FAIL,
                requirement_value=f"{requirements.min_support_months:g} months",
                vendor_value=f"{proposal.support_duration_months:g} months",
                explanation=f"Vendor support period {'meets' if passed else 'is below'} the minimum required.",
            ))

    # --- API integration (tri-state boolean) ---------------------------------------------
    if requirements.api_integration_required:
        results.append(_tri_state_bool_result(
            "api_integration", "API Integration", True, proposal.api_integration_supported
        ))

    # --- SLA (existence + ambiguity heuristic) -------------------------------------------
    if requirements.sla_required:
        if is_unspecified(proposal.sla):
            results.append(RequirementResult(
                key="sla", label="Service Level Agreement (SLA)", required=True,
                status=RequirementStatus.NOT_SPECIFIED,
                requirement_value="Required", vendor_value="Not specified",
                explanation="No SLA information was found in the proposal.",
            ))
        else:
            sla_lower = proposal.sla.lower()
            ambiguous = any(kw in sla_lower for kw in _AMBIGUOUS_SLA_KEYWORDS)
            results.append(RequirementResult(
                key="sla", label="Service Level Agreement (SLA)", required=True,
                status=RequirementStatus.REQUIRES_REVIEW if ambiguous else RequirementStatus.PASS,
                requirement_value="Required", vendor_value=proposal.sla,
                explanation=(
                    "SLA language contains conditional/vague wording and should be reviewed."
                    if ambiguous else "An SLA is stated in the proposal."
                ),
            ))

    # --- Compliance: ISO 27001 -------------------------------------------------------------
    if requirements.iso27001_required:
        results.append(_tri_state_bool_result(
            "iso27001", "ISO 27001 Certification", True, proposal.iso27001_certified
        ))

    # --- Compliance: GDPR -------------------------------------------------------------------
    if requirements.gdpr_required:
        results.append(_tri_state_bool_result(
            "gdpr", "GDPR Compliance", True, proposal.gdpr_compliant
        ))

    # --- Custom requirements (presence-based check against free text fields) ---------------
    for custom in requirements.custom_requirements:
        haystack = " ".join(filter(None, [
            proposal.contract_terms, proposal.security_information, proposal.pricing_conditions,
            " ".join(proposal.features), " ".join(proposal.technical_capabilities),
            " ".join(proposal.other_clauses),
        ])).lower()
        mentioned = bool(custom.name.lower() in haystack)
        results.append(RequirementResult(
            key=f"custom::{custom.name}", label=custom.name, required=custom.required,
            status=(RequirementStatus.REQUIRES_REVIEW if mentioned else (
                RequirementStatus.NOT_SPECIFIED if not custom.required else RequirementStatus.FAIL
            )) if custom.required else (RequirementStatus.PASS if mentioned else RequirementStatus.NOT_SPECIFIED),
            requirement_value=custom.description or "See requirement name",
            vendor_value="Mentioned in proposal" if mentioned else "Not found",
            explanation=(
                "Keyword found in the proposal text; manual review recommended to confirm it meets the need."
                if mentioned else "No matching text was found for this custom requirement."
            ),
        ))

    return results


def has_mandatory_failure(results: List[RequirementResult]) -> bool:
    return any(r.required and r.status == RequirementStatus.FAIL for r in results)


def missing_information_summary(results: List[RequirementResult], proposal: VendorProposal) -> List[str]:
    missing = [f"{r.label} was not specified in the proposal." for r in results if r.status == RequirementStatus.NOT_SPECIFIED]
    if is_unspecified(proposal.vendor_name):
        missing.insert(0, "Vendor name could not be confidently identified.")
    return missing
