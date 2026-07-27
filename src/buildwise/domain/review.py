from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.common import (
    ConfidenceLevel,
    CostCategory,
    CostFrequency,
)
from buildwise.domain.enums import (
    ReviewDecision,
    RevisionTarget,
)

# =============================================================================
# Review Findings
# =============================================================================


class ReviewFinding(BaseModel):
    """
    A finding identified during the Lead Review.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(
        description="Unique finding identifier.",
        examples=["F-001"],
    )

    title: str

    description: str

    affected_sections: list[str] = Field(
        default_factory=list,
        description="Sections impacted by this finding.",
    )

    recommendation: str

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Consistency Check
# =============================================================================


class ConsistencyCheck(BaseModel):
    """
    Cross-specialist consistency verification.
    """

    model_config = ConfigDict(extra="forbid")

    name: str

    description: str

    passed: bool

    notes: str | None = None


# =============================================================================
# Revision Request
# =============================================================================


class RevisionRequest(BaseModel):
    """
    A bounded revision requested by the Lead Reviewer.
    """

    model_config = ConfigDict(extra="forbid")

    target: RevisionTarget

    reason: str

    requested_changes: list[str] = Field(
        default_factory=list,
    )

    blocking: bool = True

    maximum_revision_round: int = Field(
        default=1,
        ge=1,
    )


# =============================================================================
# Review Cost Estimate
# =============================================================================


class ReviewCostEstimate(BaseModel):
    """
    Estimated review-related cost.
    """

    model_config = ConfigDict(extra="forbid")

    category: CostCategory = CostCategory.OPERATIONS

    item: str

    estimated_cost: float = Field(
        ge=0,
    )

    frequency: CostFrequency

    justification: str


# =============================================================================
# Lead Review
# =============================================================================


class LeadReview(BaseModel):
    """
    Final review produced by the Lead Reviewer.
    """

    model_config = ConfigDict(extra="forbid")

    executive_summary: str

    decision: ReviewDecision

    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    findings: list[ReviewFinding] = Field(
        default_factory=list,
    )

    consistency_checks: list[ConsistencyCheck] = Field(
        default_factory=list,
    )

    strengths: list[str] = Field(
        default_factory=list,
    )

    weaknesses: list[str] = Field(
        default_factory=list,
    )

    missing_items: list[str] = Field(
        default_factory=list,
    )

    contradictions: list[str] = Field(
        default_factory=list,
    )

    revision_requests: list[RevisionRequest] = Field(
        default_factory=list,
    )

    implementation_readiness_score: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Estimated implementation readiness percentage.",
    )

    estimated_review_costs: list[ReviewCostEstimate] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    approved_for_blueprint: bool = Field(
        default=False,
        description="Whether blueprint assembly may proceed.",
    )

    notes: str | None = None

    def validate_decision_consistency(self) -> None:
        """Validate whether the decision permits blueprint assembly."""

        blocking = [request for request in self.revision_requests if request.blocking]

        if self.decision is ReviewDecision.REVISION_REQUIRED and not self.revision_requests:
            raise ValueError("A revision_required decision requires revision_requests.")

        if self.decision in {
            ReviewDecision.APPROVED,
            ReviewDecision.APPROVED_WITH_LIMITATIONS,
        } and blocking:
            raise ValueError("An approved decision cannot contain a blocking revision request.")

        if (
            self.decision is ReviewDecision.REJECTED
            and not self.weaknesses
            and not self.contradictions
        ):
            raise ValueError(
                "A rejected decision requires documented weaknesses or contradictions."
            )

        expected_approval = self.decision in {
            ReviewDecision.APPROVED,
            ReviewDecision.APPROVED_WITH_LIMITATIONS,
        }
        if self.approved_for_blueprint != expected_approval:
            raise ValueError(
                "approved_for_blueprint must be true only for an approved decision."
            )
