"""Lead Review domain models — output of the Lead Review Crew."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from buildwisev2.domain.common import BuildWiseModel


class RevisionTarget(StrEnum):
    DISCOVERY = "discovery"
    PRODUCT_DEFINITION = "product_definition"
    REQUIREMENTS = "requirements"
    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_EVALUATION = "qa_evaluation"


class RevisionRequest(BuildWiseModel):
    """A single bounded revision instruction routed by the Flow, not the Crew."""

    target: RevisionTarget
    issue: str
    instructions: str


class ReviewFinding(BuildWiseModel):
    area: str
    description: str
    severity: str = "medium"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"


class LeadReview(BuildWiseModel):
    """Structured output of the Lead Reviewer's Task.

    Enforces the decision-consistency contract from the Crew specification:
    approved decisions never carry blocking revisions, revision-required
    decisions always carry at least one revision request, and rejections
    always carry a rationale.
    """

    session_id: UUID
    findings: list[ReviewFinding] = Field(default_factory=list)
    consistency_issues: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    risks_reviewed: list[str] = Field(default_factory=list)
    implementation_readiness_score: float
    decision: ReviewDecision
    approved_for_blueprint: bool
    revision_requests: list[RevisionRequest] = Field(default_factory=list)
    rejection_rationale: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_decision_consistency(self) -> LeadReview:
        if self.decision == ReviewDecision.APPROVED:
            if not self.approved_for_blueprint:
                raise ValueError("APPROVED decision must set approved_for_blueprint=True")
            if self.revision_requests:
                raise ValueError("APPROVED decision must not carry revision requests")
        elif self.decision == ReviewDecision.APPROVED_WITH_LIMITATIONS:
            if not self.approved_for_blueprint:
                raise ValueError(
                    "APPROVED_WITH_LIMITATIONS decision must set approved_for_blueprint=True"
                )
            if not self.limitations:
                raise ValueError("APPROVED_WITH_LIMITATIONS decision must list limitations")
        elif self.decision == ReviewDecision.REVISION_REQUIRED:
            if self.approved_for_blueprint:
                raise ValueError("REVISION_REQUIRED decision must set approved_for_blueprint=False")
            if not self.revision_requests:
                raise ValueError(
                    "REVISION_REQUIRED decision must include at least one revision request"
                )
        elif self.decision == ReviewDecision.REJECTED:
            if self.approved_for_blueprint:
                raise ValueError("REJECTED decision must set approved_for_blueprint=False")
            if not self.rejection_rationale:
                raise ValueError("REJECTED decision must include a rejection_rationale")
        return self
