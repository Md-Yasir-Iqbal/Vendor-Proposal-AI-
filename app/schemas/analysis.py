"""Schemas produced by the analysis pipeline (matching, risk, scoring, recommendation)."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import EvidenceSnippet
from app.schemas.vendor import VendorProposal


class RequirementStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_SPECIFIED = "NOT_SPECIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class RequirementResult(BaseModel):
    key: str  # stable machine key, e.g. "budget"
    label: str  # human-readable label, e.g. "Maximum Budget"
    required: bool = True
    status: RequirementStatus
    requirement_value: Optional[str] = None
    vendor_value: Optional[str] = None
    explanation: str = ""


class RiskSeverity(str, Enum):
    INFO = "Info"
    REVIEW = "Requires Review"
    WARNING = "Potential Risk"


class RiskItem(BaseModel):
    category: str
    severity: RiskSeverity
    description: str
    related_field: Optional[str] = None
    source: str = Field("rule_based", description="rule_based | ai_identified")
    evidence: Optional[EvidenceSnippet] = None


class ScoreBreakdown(BaseModel):
    technical_fit: float = 0.0
    budget: float = 0.0
    delivery_timeline: float = 0.0
    support_sla: float = 0.0
    risk: float = 0.0
    weights_used: Dict[str, float] = Field(default_factory=dict)
    total_score: float = 0.0

    def as_rows(self) -> List[Dict]:
        return [
            {"Category": "Technical Fit", "Weight %": self.weights_used.get("technical_fit", 0), "Sub-score /100": self.technical_fit},
            {"Category": "Budget", "Weight %": self.weights_used.get("budget", 0), "Sub-score /100": self.budget},
            {"Category": "Delivery Timeline", "Weight %": self.weights_used.get("delivery_timeline", 0), "Sub-score /100": self.delivery_timeline},
            {"Category": "Support & SLA", "Weight %": self.weights_used.get("support_sla", 0), "Sub-score /100": self.support_sla},
            {"Category": "Risk", "Weight %": self.weights_used.get("risk", 0), "Sub-score /100": self.risk},
        ]


class VendorAnalysisResult(BaseModel):
    vendor_name: str
    source_documents: List[str] = Field(default_factory=list)
    proposal: VendorProposal
    requirement_results: List[RequirementResult] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    score: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    has_mandatory_failure: bool = False
    extraction_failed: bool = False
    extraction_error: Optional[str] = None

    def pass_count(self) -> int:
        return sum(1 for r in self.requirement_results if r.status == RequirementStatus.PASS)

    def fail_count(self) -> int:
        return sum(1 for r in self.requirement_results if r.status == RequirementStatus.FAIL)


class RecommendationResult(BaseModel):
    recommended_vendor: Optional[str] = None
    is_forced_choice: bool = False
    summary: str = ""
    key_reasons: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    trade_offs: List[str] = Field(default_factory=list)
    review_items: List[str] = Field(default_factory=list)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)
    generated_by: str = Field("fallback", description="ai | fallback")


class AnalysisProject(BaseModel):
    """Top-level container held in session state for the whole analysis."""
    project_id: str
    requirements: Optional[object] = None  # RequirementsConfig, kept loose to avoid circular import churn
    vendor_results: Dict[str, VendorAnalysisResult] = Field(default_factory=dict)
    recommendation: Optional[RecommendationResult] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
