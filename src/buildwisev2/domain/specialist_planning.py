"""Specialist planning domain models — the canonical output of the deterministic planner.

These models are consumed by ``buildwisev2.planning`` (which builds them)
and ``buildwisev2.crews.technical_planning`` (which reads them). No LLM
ever produces this model; see ``05_specialist_planner.md``.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel, SpecialistType


class SpecialistSelectionReason(StrEnum):
    MANDATORY = "mandatory"
    AI_CAPABILITY = "ai_capability"
    SENSITIVE_DATA = "sensitive_data"
    REGULATED_DOMAIN = "regulated_domain"
    EXTERNAL_INTEGRATIONS = "external_integrations"
    HIGH_RISK = "high_risk"
    EXPLICIT_USER_REQUEST = "explicit_user_request"
    PRODUCT_COMPLEXITY = "product_complexity"
    QUALITY_REQUIREMENT = "quality_requirement"
    COMMERCIAL_LAUNCH = "commercial_launch"
    MARKET_UNCERTAINTY = "market_uncertainty"


class DependencyType(StrEnum):
    REQUIRES_OUTPUT = "requires_output"
    PROVIDES_CONTEXT = "provides_context"
    REQUIRES_APPROVAL = "requires_approval"


class ExecutionMode(StrEnum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class BudgetDecisionType(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITS = "approved_with_limits"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class EffortLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SpecialistRecommendation(BuildWiseModel):
    specialist: SpecialistType
    required: bool
    reason: SpecialistSelectionReason
    explanation: str
    estimated_effort: EffortLevel


class SpecialistDependency(BuildWiseModel):
    source: SpecialistType
    target: SpecialistType
    dependency: DependencyType
    description: str


class SpecialistExecutionGroup(BuildWiseModel):
    name: str
    execution_mode: ExecutionMode
    specialists: list[SpecialistType]
    rationale: str


class BudgetDecision(BuildWiseModel):
    decision: BudgetDecisionType
    explanation: str
    excluded_specialists: list[SpecialistType] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SpecialistExecutionPlan(BuildWiseModel):
    """The single canonical routing-plan model for BuildWise v2."""

    recommendations: list[SpecialistRecommendation]
    execution_groups: list[SpecialistExecutionGroup]
    dependencies: list[SpecialistDependency]
    budget: BudgetDecision
    execution_summary: str

    def selected_specialists(self) -> set[SpecialistType]:
        excluded = set(self.budget.excluded_specialists)
        return {r.specialist for r in self.recommendations} - excluded

    def includes(self, specialist: SpecialistType) -> bool:
        return specialist in self.selected_specialists()
