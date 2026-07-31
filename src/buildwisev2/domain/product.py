"""Product Definition domain models — output of the Product Planning Crew (Product Manager)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class FeaturePriority(StrEnum):
    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"
    WONT_HAVE = "wont_have"


class ProductDefinitionDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class Persona(BuildWiseModel):
    name: str
    description: str
    goals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class ProductFeature(BuildWiseModel):
    id: str
    name: str
    description: str
    priority: FeaturePriority
    ai_enabled: bool = False


class RoadmapPhase(BuildWiseModel):
    name: str
    description: str
    feature_ids: list[str] = Field(default_factory=list)


class ProductDefinition(BuildWiseModel):
    """Structured output of the Product Manager's Product Definition Task."""

    session_id: UUID
    vision: str
    value_proposition: str
    goals: list[str]
    personas: list[Persona]
    features: list[ProductFeature]
    mvp_feature_ids: list[str]
    exclusions: list[str] = Field(default_factory=list)
    roadmap: list[RoadmapPhase] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: ProductDefinitionDecision

    def feature_ids(self) -> set[str]:
        return {feature.id for feature in self.features}
