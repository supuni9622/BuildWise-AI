"""Aggregate result produced by the BuildWise Technical Planning Crew.

This module groups existing specialist outputs into one typed result.

It does not redefine or flatten the canonical Solution Architecture,
AI Architecture, Security Architecture, or QA and Evaluation artifacts.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator, model_validator

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    SessionId,
    generate_uuid,
    utc_now,
)
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.security import SecurityArchitecture


class TechnicalPlanningResult(BuildWiseModel):
    """Canonical aggregate output of the Technical Planning Crew.

    SolutionArchitecture is required because it provides the general technical
    foundation.

    AIArchitecture, SecurityArchitecture, and QAEvaluationPlan are optional
    because the deterministic Specialist Planner controls whether those
    specialists participate in a consultation.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    session_id: SessionId = Field(
        description=("Consulting session that owns all Technical Planning artifacts."),
    )

    solution_architecture: SolutionArchitecture = Field(
        description="Canonical output produced by the Solution Architect.",
    )

    ai_architecture: AIArchitecture | None = Field(
        default=None,
        description=(
            "Optional AI-specific architecture produced when AI capabilities are selected."
        ),
    )

    security_architecture: SecurityArchitecture | None = Field(
        default=None,
        description=("Optional security architecture produced when security planning is selected."),
    )

    qa_evaluation: QAEvaluationPlan | None = Field(
        default=None,
        description=("Optional QA and evaluation plan produced when quality planning is selected."),
    )

    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at")
    @classmethod
    def normalize_generated_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware timestamp and normalize it to UTC."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_technical_planning_result(
        self,
    ) -> TechnicalPlanningResult:
        """Validate ownership across technical planning artifacts."""

        solution_architecture = self.solution_architecture

        if solution_architecture.session_id != self.session_id:
            raise ValueError(
                "SolutionArchitecture.session_id must match TechnicalPlanningResult.session_id."
            )

        if self.ai_architecture is not None:
            if self.ai_architecture.session_id != self.session_id:
                raise ValueError(
                    "AIArchitecture.session_id must match TechnicalPlanningResult.session_id."
                )

            if self.ai_architecture.solution_architecture_id != solution_architecture.id:
                raise ValueError(
                    "AIArchitecture.solution_architecture_id must match SolutionArchitecture.id."
                )

            if (
                self.ai_architecture.requirements_specification_id
                != solution_architecture.requirements_specification_id
            ):
                raise ValueError(
                    "AIArchitecture and SolutionArchitecture must reference "
                    "the same RequirementsSpecification."
                )

        return self

    def validate_specialist_selection(
        self,
        *,
        ai_selected: bool,
        security_selected: bool,
        qa_selected: bool,
    ) -> None:
        """Validate artifact presence against deterministic planner decisions.

        This method allows the Flow or output validator to compare this result
        with SpecialistExecutionPlan without storing a duplicate copy of the
        plan inside the aggregate.
        """

        if ai_selected and self.ai_architecture is None:
            raise ValueError("AI Architecture was selected, but ai_architecture is missing.")

        if not ai_selected and self.ai_architecture is not None:
            raise ValueError(
                "ai_architecture was produced even though AI Architecture was not selected."
            )

        if security_selected and self.security_architecture is None:
            raise ValueError(
                "Security Architecture was selected, but security_architecture is missing."
            )

        if not security_selected and self.security_architecture is not None:
            raise ValueError(
                "security_architecture was produced even though Security "
                "Architecture was not selected."
            )

        if qa_selected and self.qa_evaluation is None:
            raise ValueError("QA and Evaluation was selected, but qa_evaluation is missing.")

        if not qa_selected and self.qa_evaluation is not None:
            raise ValueError(
                "qa_evaluation was produced even though QA and Evaluation was not selected."
            )
