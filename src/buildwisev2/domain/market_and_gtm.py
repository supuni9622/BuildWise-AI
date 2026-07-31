"""Market & GTM domain models."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class MarketAndGTMDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class MarketSegment(BuildWiseModel):
    name: str
    description: str
    is_primary: bool = False


class Competitor(BuildWiseModel):
    name: str
    description: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    source_url: str | None = None


class PricingHypothesis(BuildWiseModel):
    model: str
    rationale: str
    evidence_confidence: str = "low"


class Channel(BuildWiseModel):
    name: str
    rationale: str
    priority: str = "medium"


class LaunchExperiment(BuildWiseModel):
    name: str
    hypothesis: str
    decision_criteria: str


class EvidenceReference(BuildWiseModel):
    claim: str
    source_url: str | None = None
    confidence: str = "low"


class MarketAndGTMStrategy(BuildWiseModel):
    """Structured output of the Market & GTM Strategist's Task."""

    session_id: UUID
    segments: list[MarketSegment]
    primary_segment: str | None = None
    competitors: list[Competitor] = Field(default_factory=list)
    positioning: str
    messaging_pillars: list[str] = Field(default_factory=list)
    pricing_hypotheses: list[PricingHypothesis] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)
    launch_experiments: list[LaunchExperiment] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    decision: MarketAndGTMDecision
