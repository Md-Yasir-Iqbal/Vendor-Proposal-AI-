"""
Schemas for structured vendor information extracted from a proposal PDF.

Every field is optional/nullable by design: the LLM must never invent a
value that is not present in the source document. When information is not
found, fields are left as None (or empty lists), and the UI displays
"Not specified" rather than a guessed value.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class VendorProposal(BaseModel):
    """Structured representation of a single vendor's proposal."""

    vendor_name: Optional[str] = Field(None, description="Vendor / company name as stated in the proposal.")

    # --- Commercial -----------------------------------------------------------------
    total_cost: Optional[float] = Field(None, description="Total one-time project cost, numeric, in the proposal's currency.")
    recurring_cost: Optional[float] = Field(None, description="Recurring cost (e.g. monthly/annual), numeric.")
    recurring_cost_frequency: Optional[str] = Field(None, description="e.g. 'monthly', 'annual'.")
    currency: Optional[str] = Field(None, description="Currency mentioned, e.g. INR, USD.")
    payment_terms: Optional[str] = Field(None)
    pricing_conditions: Optional[str] = Field(None, description="Any conditions, escalation clauses, or notes about pricing.")

    # --- Delivery ---------------------------------------------------------------------
    implementation_timeline_weeks: Optional[float] = Field(None, description="Total implementation time, converted to weeks.")
    implementation_timeline_raw: Optional[str] = Field(None, description="Original text describing the timeline.")

    # --- Support ------------------------------------------------------------------------
    support_duration_months: Optional[float] = Field(None, description="Post-launch support duration, in months.")
    sla: Optional[str] = Field(None, description="Description of the SLA offered, if any.")
    warranty: Optional[str] = Field(None)

    # --- Technical ----------------------------------------------------------------------
    features: List[str] = Field(default_factory=list)
    technical_capabilities: List[str] = Field(default_factory=list)
    api_integration_supported: Optional[bool] = Field(
        None, description="True/False only if explicitly stated; null if not mentioned."
    )

    # --- Compliance & security ------------------------------------------------------------
    certifications: List[str] = Field(default_factory=list, description="e.g. ISO 27001, SOC 2.")
    iso27001_certified: Optional[bool] = Field(None)
    gdpr_compliant: Optional[bool] = Field(None)
    security_information: Optional[str] = Field(None)

    # --- Contract -------------------------------------------------------------------------
    contract_terms: Optional[str] = Field(None)
    exclusions: List[str] = Field(default_factory=list)
    other_clauses: List[str] = Field(default_factory=list)

    @field_validator("total_cost", "recurring_cost", "implementation_timeline_weeks", "support_duration_months", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "" or v.lower() in {"not specified", "n/a", "na", "unknown"}:
                return None
            # Strip thousands separators / currency symbols if the model left them in.
            cleaned = "".join(ch for ch in v if ch.isdigit() or ch in ".-")
            try:
                return float(cleaned) if cleaned not in {"", "-", "."} else None
            except ValueError:
                return None
        return v

    @field_validator("features", "technical_capabilities", "certifications", "exclusions", "other_clauses", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() and v.strip().lower() != "not specified" else []
        return v


class VendorDocumentMeta(BaseModel):
    """Metadata about a single uploaded PDF and its processing outcome."""

    filename: str
    detected_vendor_name: Optional[str] = None
    num_pages: int = 0
    num_chunks: int = 0
    status: str = Field("pending", description="pending | processed | failed | scanned_warning")
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
