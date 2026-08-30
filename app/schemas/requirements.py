"""Schemas describing the user-configured requirements for an analysis project."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CustomRequirement(BaseModel):
    """An extra free-form requirement defined by the user."""
    name: str
    description: Optional[str] = None
    required: bool = True


class ScoringWeights(BaseModel):
    """
    Weights (as percentages) used to combine sub-scores into the overall
    vendor score. Values are normalized to sum to 100 at validation time,
    so users can enter approximate values and still get a sane result.
    """
    technical_fit: float = Field(30, ge=0, le=100)
    budget: float = Field(25, ge=0, le=100)
    delivery_timeline: float = Field(20, ge=0, le=100)
    support_sla: float = Field(15, ge=0, le=100)
    risk: float = Field(10, ge=0, le=100)

    @model_validator(mode="after")
    def _normalize(self) -> "ScoringWeights":
        total = (
            self.technical_fit
            + self.budget
            + self.delivery_timeline
            + self.support_sla
            + self.risk
        )
        if total <= 0:
            raise ValueError("At least one scoring weight must be greater than zero.")
        if abs(total - 100.0) > 0.01:
            factor = 100.0 / total
            object.__setattr__(self, "technical_fit", round(self.technical_fit * factor, 2))
            object.__setattr__(self, "budget", round(self.budget * factor, 2))
            object.__setattr__(self, "delivery_timeline", round(self.delivery_timeline * factor, 2))
            object.__setattr__(self, "support_sla", round(self.support_sla * factor, 2))
            object.__setattr__(self, "risk", round(self.risk * factor, 2))
        return self

    def as_dict(self) -> dict:
        return {
            "technical_fit": self.technical_fit,
            "budget": self.budget,
            "delivery_timeline": self.delivery_timeline,
            "support_sla": self.support_sla,
            "risk": self.risk,
        }


class RequirementsConfig(BaseModel):
    """Everything the procurement team defines before uploading proposals."""

    project_name: str = Field(..., min_length=1)

    max_budget: Optional[float] = Field(None, gt=0, description="Maximum acceptable total cost.")
    max_timeline_weeks: Optional[float] = Field(None, gt=0, description="Maximum acceptable implementation time (weeks).")
    min_support_months: Optional[float] = Field(None, gt=0, description="Minimum acceptable post-launch support (months).")

    api_integration_required: bool = False
    sla_required: bool = False
    iso27001_required: bool = False
    gdpr_required: bool = False

    custom_requirements: List[CustomRequirement] = Field(default_factory=list)

    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)

    currency_symbol: str = "\u20b9"

    @field_validator("project_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty.")
        return v

    def mandatory_flags(self) -> dict:
        """Which boolean/compliance requirements are mandatory."""
        return {
            "api_integration": self.api_integration_required,
            "sla": self.sla_required,
            "iso27001": self.iso27001_required,
            "gdpr": self.gdpr_required,
        }
