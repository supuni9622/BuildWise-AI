"""Typed, task-specific context projections for technical specialists."""

from __future__ import annotations

from pydantic import Field

from buildwise.domain.ai_architecture import (
    AgentWorkflow,
    AIArchitecture,
    AICapability,
    AIEvaluationMetric,
    AIGuardrail,
    AIToolPolicy,
    RAGDesign,
)
from buildwise.domain.architecture import (
    ArchitectureComponent,
    ArchitectureConnection,
    DeploymentUnit,
    SolutionArchitecture,
)
from buildwise.domain.common import ArtifactId, BuildWiseModel, MediumText
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import (
    DataRequirement,
    FunctionalRequirement,
    IntegrationRequirement,
    NonFunctionalRequirement,
    RequirementsSpecification,
    UserJourney,
)
from buildwise.domain.security import (
    SecurityArchitecture,
    SecurityControl,
    SecurityRequirement,
    SecurityValidation,
)


class RequirementsProjection(BuildWiseModel):
    """Requirements fields needed for technical design and traceability."""

    id: ArtifactId
    title: str
    summary: str
    scope: str
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    data_requirements: list[DataRequirement] = Field(default_factory=list)
    integration_requirements: list[IntegrationRequirement] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    limitations: list[MediumText] = Field(default_factory=list)

    @classmethod
    def from_artifact(cls, requirements: RequirementsSpecification) -> RequirementsProjection:
        return cls.model_validate(
            requirements.model_dump(
                include=set(cls.model_fields),
                mode="python",
            )
        )


class SolutionProjection(BuildWiseModel):
    """Solution fields needed by downstream AI, security, and QA specialists."""

    id: ArtifactId
    requirements_specification_id: ArtifactId
    architecture_style: str
    architecture_style_rationale: str
    components: list[ArchitectureComponent] = Field(default_factory=list)
    connections: list[ArchitectureConnection] = Field(default_factory=list)
    deployment_units: list[DeploymentUnit] = Field(default_factory=list)
    data_architecture_summary: str
    integration_architecture_summary: str
    deployment_summary: str
    operational_summary: str
    security_considerations: list[MediumText] = Field(default_factory=list)
    privacy_considerations: list[MediumText] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    limitations: list[MediumText] = Field(default_factory=list)

    @classmethod
    def from_artifact(cls, artifact: SolutionArchitecture) -> SolutionProjection:
        return cls.model_validate(artifact.model_dump(include=set(cls.model_fields), mode="python"))


class AIProjection(BuildWiseModel):
    """AI data flows, controls, and evaluation fields needed downstream."""

    id: ArtifactId
    requirements_specification_id: ArtifactId
    solution_architecture_id: ArtifactId
    capabilities: list[AICapability] = Field(default_factory=list)
    tool_policies: list[AIToolPolicy] = Field(default_factory=list)
    agent_workflows: list[AgentWorkflow] = Field(default_factory=list)
    rag_designs: list[RAGDesign] = Field(default_factory=list)
    guardrails: list[AIGuardrail] = Field(default_factory=list)
    evaluation_metrics: list[AIEvaluationMetric] = Field(default_factory=list)
    human_oversight_strategy: str
    fallback_strategy: str
    privacy_strategy: str
    security_boundary_summary: str
    assumptions: list[MediumText] = Field(default_factory=list)
    limitations: list[MediumText] = Field(default_factory=list)

    @classmethod
    def from_artifact(cls, artifact: AIArchitecture) -> AIProjection:
        return cls.model_validate(artifact.model_dump(include=set(cls.model_fields), mode="python"))


class SecurityProjection(BuildWiseModel):
    """Security controls and validations needed by QA."""

    executive_summary: str
    controls: list[SecurityControl] = Field(default_factory=list)
    security_requirements: list[SecurityRequirement] = Field(default_factory=list)
    validations: list[SecurityValidation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    notes: str | None = None

    @classmethod
    def from_artifact(cls, artifact: SecurityArchitecture) -> SecurityProjection:
        return cls.model_validate(artifact.model_dump(include=set(cls.model_fields), mode="python"))


class SolutionArchitectContext(BuildWiseModel):
    requirements: RequirementsProjection

    @classmethod
    def build(cls, requirements: RequirementsSpecification) -> SolutionArchitectContext:
        return cls(requirements=RequirementsProjection.from_artifact(requirements))


class AIArchitectContext(BuildWiseModel):
    requirements: RequirementsProjection
    solution: SolutionProjection

    @classmethod
    def build(
        cls,
        requirements: RequirementsSpecification,
        solution: SolutionArchitecture,
    ) -> AIArchitectContext:
        return cls(
            requirements=RequirementsProjection.from_artifact(requirements),
            solution=SolutionProjection.from_artifact(solution),
        )


class SecurityArchitectContext(BuildWiseModel):
    requirements: RequirementsProjection
    solution: SolutionProjection
    ai: AIProjection | None = None

    @classmethod
    def build(
        cls,
        requirements: RequirementsSpecification,
        solution: SolutionArchitecture,
        ai: AIArchitecture | None,
    ) -> SecurityArchitectContext:
        return cls(
            requirements=RequirementsProjection.from_artifact(requirements),
            solution=SolutionProjection.from_artifact(solution),
            ai=AIProjection.from_artifact(ai) if ai is not None else None,
        )


class QARequirementsProjection(RequirementsProjection):
    user_journeys: list[UserJourney] = Field(default_factory=list)

    @classmethod
    def from_artifact(cls, requirements: RequirementsSpecification) -> QARequirementsProjection:
        return cls.model_validate(
            requirements.model_dump(include=set(cls.model_fields), mode="python")
        )


class QAArchitectContext(BuildWiseModel):
    requirements: QARequirementsProjection
    solution: SolutionProjection
    ai: AIProjection | None = None
    security: SecurityProjection | None = None

    @classmethod
    def build(
        cls,
        requirements: RequirementsSpecification,
        solution: SolutionArchitecture,
        ai: AIArchitecture | None,
        security: SecurityArchitecture | None,
    ) -> QAArchitectContext:
        return cls(
            requirements=QARequirementsProjection.from_artifact(requirements),
            solution=SolutionProjection.from_artifact(solution),
            ai=AIProjection.from_artifact(ai) if ai is not None else None,
            security=(SecurityProjection.from_artifact(security) if security is not None else None),
        )


def context_size_reduction(
    full_artifacts: list[BuildWiseModel | QAEvaluationPlan],
    projection: BuildWiseModel,
) -> tuple[int, int]:
    """Return full and projected JSON character counts for measurements."""

    full_chars = sum(len(artifact.model_dump_json()) for artifact in full_artifacts)
    return full_chars, len(projection.model_dump_json())
