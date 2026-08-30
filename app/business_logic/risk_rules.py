"""
Deterministic, rule-based risk detection.

These checks run in plain Python against the validated VendorProposal and
the RequirementsConfig. They complement (but do not replace) the
AI-assisted ambiguous-language detection in app.ai.risk_analyzer.
"""
from __future__ import annotations

from typing import List

from app.schemas.analysis import RiskItem, RiskSeverity
from app.schemas.requirements import RequirementsConfig
from app.schemas.vendor import VendorProposal
from app.utils.helpers import format_currency, is_unspecified

_UNFAVORABLE_PRICING_KEYWORDS = [
    "subject to change", "additional charges may apply", "excludes", "not included",
    "price increase", "escalation", "may be revised",
]
_UNFAVORABLE_CONTRACT_KEYWORDS = [
    "auto-renew", "automatically renew", "non-refundable", "non refundable",
    "no refund", "early termination fee", "lock-in",
]


def detect_rule_based_risks(proposal: VendorProposal, requirements: RequirementsConfig) -> List[RiskItem]:
    risks: List[RiskItem] = []

    # --- Missing pricing information --------------------------------------------------------
    if is_unspecified(proposal.total_cost):
        risks.append(RiskItem(
            category="Missing Information",
            severity=RiskSeverity.WARNING,
            description="Total project cost is not clearly stated in the proposal.",
            related_field="total_cost",
            source="rule_based",
        ))

    # --- Recurring costs (informational, not necessarily bad) --------------------------------
    if not is_unspecified(proposal.recurring_cost) and proposal.recurring_cost > 0:
        freq = proposal.recurring_cost_frequency or "recurring"
        risks.append(RiskItem(
            category="Recurring Cost",
            severity=RiskSeverity.INFO,
            description=(
                f"A {freq} recurring cost of "
                f"{format_currency(proposal.recurring_cost, requirements.currency_symbol)} applies "
                f"in addition to the total project cost."
            ),
            related_field="recurring_cost",
            source="rule_based",
        ))

    # --- Pricing conditions keyword scan --------------------------------------------------------
    if proposal.pricing_conditions:
        lowered = proposal.pricing_conditions.lower()
        hits = [kw for kw in _UNFAVORABLE_PRICING_KEYWORDS if kw in lowered]
        if hits:
            risks.append(RiskItem(
                category="Pricing Conditions",
                severity=RiskSeverity.REVIEW,
                description=f"Pricing conditions mention potentially variable terms ({', '.join(hits)}).",
                related_field="pricing_conditions",
                source="rule_based",
            ))

    # --- Contract terms keyword scan ------------------------------------------------------------
    if proposal.contract_terms:
        lowered = proposal.contract_terms.lower()
        hits = [kw for kw in _UNFAVORABLE_CONTRACT_KEYWORDS if kw in lowered]
        if hits:
            risks.append(RiskItem(
                category="Contract Terms",
                severity=RiskSeverity.REVIEW,
                description=f"Contract terms include clauses that may be unfavorable ({', '.join(hits)}).",
                related_field="contract_terms",
                source="rule_based",
            ))

    # --- Exclusions present -----------------------------------------------------------------------
    if proposal.exclusions:
        risks.append(RiskItem(
            category="Exclusions",
            severity=RiskSeverity.INFO,
            description=f"The proposal explicitly excludes {len(proposal.exclusions)} item(s) from scope: "
                        f"{', '.join(proposal.exclusions[:4])}"
                        f"{'...' if len(proposal.exclusions) > 4 else ''}.",
            related_field="exclusions",
            source="rule_based",
        ))

    # --- Timeline significantly over requirement ------------------------------------------------
    if (
        requirements.max_timeline_weeks
        and not is_unspecified(proposal.implementation_timeline_weeks)
        and proposal.implementation_timeline_weeks > requirements.max_timeline_weeks * 1.25
    ):
        risks.append(RiskItem(
            category="Implementation Timeline",
            severity=RiskSeverity.WARNING,
            description=(
                f"Proposed timeline ({proposal.implementation_timeline_weeks:g} weeks) significantly exceeds "
                f"the required maximum ({requirements.max_timeline_weeks:g} weeks)."
            ),
            related_field="implementation_timeline_weeks",
            source="rule_based",
        ))

    # --- Support duration below requirement ------------------------------------------------------
    if (
        requirements.min_support_months
        and not is_unspecified(proposal.support_duration_months)
        and proposal.support_duration_months < requirements.min_support_months
    ):
        risks.append(RiskItem(
            category="Support Period",
            severity=RiskSeverity.WARNING,
            description=(
                f"Support period ({proposal.support_duration_months:g} months) is below the minimum "
                f"required ({requirements.min_support_months:g} months)."
            ),
            related_field="support_duration_months",
            source="rule_based",
        ))

    # --- Missing mandatory certifications ---------------------------------------------------------
    if requirements.iso27001_required and proposal.iso27001_certified is not True:
        risks.append(RiskItem(
            category="Compliance Gap",
            severity=RiskSeverity.WARNING if proposal.iso27001_certified is False else RiskSeverity.REVIEW,
            description=(
                "Vendor explicitly does not hold ISO 27001 certification."
                if proposal.iso27001_certified is False
                else "ISO 27001 certification status is not confirmed in the proposal."
            ),
            related_field="iso27001_certified",
            source="rule_based",
        ))

    if requirements.gdpr_required and proposal.gdpr_compliant is not True:
        risks.append(RiskItem(
            category="Compliance Gap",
            severity=RiskSeverity.WARNING if proposal.gdpr_compliant is False else RiskSeverity.REVIEW,
            description=(
                "Vendor explicitly does not confirm GDPR compliance."
                if proposal.gdpr_compliant is False
                else "GDPR compliance status is not confirmed in the proposal."
            ),
            related_field="gdpr_compliant",
            source="rule_based",
        ))

    # --- Ambiguous SLA language --------------------------------------------------------------------
    if requirements.sla_required and proposal.sla:
        lowered = proposal.sla.lower()
        ambiguous_terms = [t for t in ["best effort", "no guarantee", "subject to change", "reasonable effort"] if t in lowered]
        if ambiguous_terms:
            risks.append(RiskItem(
                category="SLA Clarity",
                severity=RiskSeverity.REVIEW,
                description=f"SLA wording includes conditional language ({', '.join(ambiguous_terms)}) that should be clarified.",
                related_field="sla",
                source="rule_based",
            ))

    return risks
