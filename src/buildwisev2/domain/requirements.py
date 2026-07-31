"""Requirements domain models — output of the Product Planning Crew (Business Analyst)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class RequirementsDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class NFRCategory(StrEnum):
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    RECOVERABILITY = "recoverability"
    DATA_INTEGRITY = "data_integrity"
    COMPLIANCE = "compliance"
    SCALABILITY = "scalability"
    USABILITY = "usability"
    OTHER = "other"


class RequirementPriority(StrEnum):
    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"


class FunctionalRequirement(BuildWiseModel):
    id: str
    description: str
    category: str = "functional"
    """Free-form category, e.g. "functional" or "ai" — the planner treats
    an "ai" category as an AI-capability signal."""
    related_feature_ids: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class NonFunctionalRequirement(BuildWiseModel):
    id: str
    category: NFRCategory
    description: str
    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE


class BusinessRule(BuildWiseModel):
    id: str
    description: str


class DataRequirement(BuildWiseModel):
    id: str
    entity: str
    description: str


class IntegrationRequirement(BuildWiseModel):
    id: str
    name: str
    description: str
    provider: str | None = None
    uses_llm_provider: bool = False
    is_privileged: bool = False


class UserJourney(BuildWiseModel):
    id: str
    persona: str
    steps: list[str]


class EdgeCase(BuildWiseModel):
    id: str
    description: str
    blocking: bool = False


class RequirementsSpecification(BuildWiseModel):
    """Structured output of the Business Analyst's Requirements Task."""

    session_id: UUID
    functional_requirements: list[FunctionalRequirement]
    non_functional_requirements: list[NonFunctionalRequirement]
    business_rules: list[BusinessRule] = Field(default_factory=list)
    data_requirements: list[DataRequirement] = Field(default_factory=list)
    integration_requirements: list[IntegrationRequirement] = Field(default_factory=list)
    user_journeys: list[UserJourney] = Field(default_factory=list)
    edge_cases: list[EdgeCase] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: RequirementsDecision
