"""Domain models for specialist selection and execution planning."""

from __future__ import annotations

from pydantic import Field

from buildwise.domain.common import BuildWiseBaseModel
from buildwise.domain.enums import (
    BudgetDecisionType,
    DependencyType,
    ExecutionMode,
    SpecialistSelectionReason,
    SpecialistType,
)


class SpecialistRecommendation(BuildWiseBaseModel):
    """Recommendation to include a specialist in the consulting process."""

    specialist: SpecialistType = Field(
        description="Specialist recommended for execution."
    )

    required: bool = Field(
        description="Whether the specialist is mandatory."
    )

    reason: SpecialistSelectionReason = Field(
        description="Primary reason for selecting this specialist."
    )

    explanation: str = Field(
        min_length=10,
        description="Human-readable explanation of the recommendation.",
    )

    estimated_effort: str = Field(
        description="Estimated implementation effort (e.g. Low, Medium, High)."
    )


class SpecialistDependency(BuildWiseBaseModel):
    """Execution dependency between two specialists."""

    source: SpecialistType = Field(
        description="Specialist producing the prerequisite output."
    )

    target: SpecialistType = Field(
        description="Specialist depending on the prerequisite."
    )

    dependency: DependencyType = Field(
        description="Nature of the dependency."
    )

    description: str = Field(
        min_length=10,
        description="Explanation of why this dependency exists.",
    )


class SpecialistExecutionGroup(BuildWiseBaseModel):
    """A group of specialists that can execute together."""

    name: str = Field(
        min_length=3,
        description="Execution group name."
    )

    execution_mode: ExecutionMode = Field(
        description="Sequential or parallel execution."
    )

    specialists: list[SpecialistType] = Field(
        default_factory=list,
        description="Specialists included in this execution group.",
    )

    rationale: str = Field(
        min_length=10,
        description="Reason for grouping these specialists together.",
    )


class BudgetDecision(BuildWiseBaseModel):
    """Budget-aware planning decision."""

    decision: BudgetDecisionType = Field(
        description="Planner decision."
    )

    explanation: str = Field(
        min_length=10,
        description="Reason behind the decision.",
    )

    excluded_specialists: list[SpecialistType] = Field(
        default_factory=list,
        description="Specialists omitted because of budget constraints.",
    )

    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations introduced by the decision.",
    )


class SpecialistExecutionPlan(BuildWiseBaseModel):
    """Complete execution plan produced by the Specialist Planner."""

    recommendations: list[SpecialistRecommendation] = Field(
        default_factory=list,
        description="Recommended specialists.",
    )

    execution_groups: list[SpecialistExecutionGroup] = Field(
        default_factory=list,
        description="Ordered execution groups.",
    )

    dependencies: list[SpecialistDependency] = Field(
        default_factory=list,
        description="Execution dependencies.",
    )

    budget: BudgetDecision = Field(
        description="Budget-aware execution decision."
    )

    execution_summary: str = Field(
        min_length=20,
        description="Overall explanation of the execution strategy.",
    )