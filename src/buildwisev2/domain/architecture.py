"""Solution Architecture domain models — output of the Technical Planning
Crew (Solution Architect).
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class SolutionArchitectureDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class Component(BuildWiseModel):
    id: str
    name: str
    responsibility: str
    technology: str | None = None


class Integration(BuildWiseModel):
    id: str
    name: str
    description: str
    component_ids: list[str] = Field(default_factory=list)


class DataStore(BuildWiseModel):
    id: str
    name: str
    kind: str
    purpose: str


class DeploymentView(BuildWiseModel):
    description: str
    environments: list[str] = Field(default_factory=list)


class ImplementationPhase(BuildWiseModel):
    name: str
    description: str
    component_ids: list[str] = Field(default_factory=list)


class CostEstimate(BuildWiseModel):
    item: str
    estimate: str
    rationale: str


class SolutionArchitecture(BuildWiseModel):
    """Structured output of the Solution Architect's Task."""

    session_id: UUID
    system_context: str
    components: list[Component]
    integrations: list[Integration] = Field(default_factory=list)
    data_stores: list[DataStore] = Field(default_factory=list)
    deployment: DeploymentView
    scalability_strategy: str
    reliability_strategy: str
    observability_strategy: str
    implementation_phases: list[ImplementationPhase] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    cost_estimates: list[CostEstimate] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: SolutionArchitectureDecision

    def component_ids(self) -> set[str]:
        return {component.id for component in self.components}
