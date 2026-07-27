from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    MediumText,
    RequestId,
    SessionId,
    ShortText,
    Slug,
    WarningMessage,
    generate_uuid,
    utc_now,
)
from buildwise.domain.discovery import (
    ClarificationQuestionSet,
    DiscoveryResult,
)
from buildwise.domain.enums import (
    SessionStage,
    SessionStatus,
    SpecialistType,
)
from buildwise.domain.intake import (
    ClarificationAnswer,
    ProductIdeaContext,
    ProductIdeaRequest,
    ValidatedProductIdea,
)
from buildwise.domain.product import ProductDefinition
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import LeadReview, RevisionRequest
from buildwise.domain.session import SessionError
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.domain.usage import UsageSummary

SpecialistExecutionStatus = Literal[
    "not_selected",
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
]

FlowTransitionReason = Literal[
    "flow_started",
    "stage_completed",
    "clarification_required",
    "clarification_received",
    "specialist_selected",
    "specialist_completed",
    "specialist_failed",
    "revision_requested",
    "budget_exceeded",
    "flow_completed",
    "flow_failed",
    "manual",
]


def _normalize_datetime(
    value: datetime | None,
    *,
    field_name: str,
) -> datetime | None:
    """Require timezone-aware timestamps and normalize them to UTC."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


def _ensure_unique_values[T](
    value: list[T],
    *,
    field_name: str,
) -> list[T]:
    """Return a list after ensuring that every value is unique."""

    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must contain unique values.")

    return value


class FlowStageTransition(BuildWiseModel):
    """An auditable transition between two BuildWise Flow stages."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    from_stage: SessionStage | None = None
    to_stage: SessionStage

    from_status: SessionStatus | None = None
    to_status: SessionStatus

    reason: FlowTransitionReason
    description: MediumText | None = None

    occurred_at: datetime = Field(default_factory=utc_now)

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime) -> datetime:
        """Normalize the transition timestamp to UTC."""

        normalized = _normalize_datetime(
            value,
            field_name="occurred_at",
        )

        if normalized is None:
            raise ValueError("occurred_at cannot be null.")

        return normalized

    @model_validator(mode="after")
    def validate_transition(self) -> FlowStageTransition:
        """Reject transitions that do not change status or stage."""

        if self.from_stage == self.to_stage and self.from_status == self.to_status:
            raise ValueError("A Flow transition must change the stage, status, or both.")

        if (
            self.to_status is SessionStatus.AWAITING_USER_INPUT
            and self.to_stage is not SessionStage.CLARIFICATION
        ):
            raise ValueError(
                "A transition to awaiting_user_input must enter the clarification stage."
            )

        if (
            self.to_status is SessionStatus.REVIEWING
            and self.to_stage is not SessionStage.LEAD_REVIEW
        ):
            raise ValueError("A transition to reviewing must enter the lead_review stage.")

        if (
            self.to_status is SessionStatus.COMPLETED
            and self.to_stage is not SessionStage.COMPLETED
        ):
            raise ValueError("A completed Flow transition must enter the completed stage.")

        if (
            self.to_status is SessionStatus.COMPLETED_WITH_LIMITATIONS
            and self.to_stage is not SessionStage.COMPLETED
        ):
            raise ValueError("A Flow completed with limitations must enter the completed stage.")

        if self.to_status is SessionStatus.FAILED and self.to_stage is not SessionStage.FAILED:
            raise ValueError("A failed Flow transition must enter the failed stage.")

        return self


class SpecialistExecutionState(BuildWiseModel):
    """Runtime state for one selected or skipped specialist."""

    specialist: SpecialistType
    status: SpecialistExecutionStatus = "pending"

    selected_reason: Slug | None = None
    selection_rationale: MediumText | None = None

    artifact_id: ArtifactId | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    attempt_count: int = Field(default=0, ge=0)
    revision_count: int = Field(default=0, ge=0)

    error: SessionError | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def normalize_specialist_timestamp(
        cls,
        value: datetime | None,
        info: object,
    ) -> datetime | None:
        """Normalize specialist execution timestamps to UTC."""

        field_name = getattr(info, "field_name", "timestamp")

        return _normalize_datetime(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_execution_state(self) -> SpecialistExecutionState:
        """Validate specialist execution lifecycle consistency."""

        if self.status == "not_selected":
            if self.selected_reason is not None:
                raise ValueError("A non-selected specialist cannot have selected_reason.")

            if self.selection_rationale is not None:
                raise ValueError("A non-selected specialist cannot have a selection rationale.")

        if self.status in {
            "pending",
            "running",
            "completed",
            "failed",
        }:
            if self.selected_reason is None:
                raise ValueError("A selected specialist requires selected_reason.")

            if self.selection_rationale is None:
                raise ValueError("A selected specialist requires selection_rationale.")

        if self.status == "pending":
            if self.started_at is not None:
                raise ValueError("A pending specialist cannot have started_at.")

            if self.completed_at is not None:
                raise ValueError("A pending specialist cannot have completed_at.")

            if self.artifact_id is not None:
                raise ValueError("A pending specialist cannot have an artifact_id.")

        if self.status == "running":
            if self.started_at is None:
                raise ValueError("A running specialist requires started_at.")

            if self.completed_at is not None:
                raise ValueError("A running specialist cannot have completed_at.")

            if self.attempt_count < 1:
                raise ValueError("A running specialist requires at least one attempt.")

        if self.status == "completed":
            if self.started_at is None:
                raise ValueError("A completed specialist requires started_at.")

            if self.completed_at is None:
                raise ValueError("A completed specialist requires completed_at.")

            if self.artifact_id is None:
                raise ValueError("A completed specialist requires artifact_id.")

            if self.error is not None:
                raise ValueError("A completed specialist cannot retain an active error.")

        if self.status == "failed":
            if self.started_at is None:
                raise ValueError("A failed specialist requires started_at.")

            if self.completed_at is None:
                raise ValueError("A failed specialist requires completed_at.")

            if self.error is None:
                raise ValueError("A failed specialist requires an error.")

        if self.status == "skipped":
            if self.selection_rationale is None:
                raise ValueError("A skipped specialist requires a rationale.")

            if self.started_at is not None:
                raise ValueError("A skipped specialist cannot have started_at.")

            if self.completed_at is not None:
                raise ValueError("A skipped specialist cannot have completed_at.")

            if self.artifact_id is not None:
                raise ValueError("A skipped specialist cannot have artifact_id.")

        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot be earlier than started_at.")

        return self

    @property
    def is_terminal(self) -> bool:
        """Return whether specialist execution has ended."""

        return self.status in {
            "completed",
            "failed",
            "skipped",
            "not_selected",
        }

    def mark_running(
        self,
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark the specialist as running and increment its attempt count."""

        if self.status not in {
            "pending",
            "failed",
        }:
            raise ValueError("Only pending or failed specialists can start execution.")

        started_at = occurred_at or utc_now()
        normalized_started_at = _normalize_datetime(
            started_at,
            field_name="occurred_at",
        )

        if normalized_started_at is None:
            raise ValueError("occurred_at cannot be null.")

        self.apply_updates(
            status="running",
            started_at=normalized_started_at,
            completed_at=None,
            error=None,
            artifact_id=None,
            attempt_count=self.attempt_count + 1,
        )

    def mark_completed(
        self,
        *,
        artifact_id: ArtifactId,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark the specialist as completed with its output artifact."""

        if self.status != "running":
            raise ValueError("Only a running specialist can be completed.")

        completed_at = occurred_at or utc_now()
        normalized_completed_at = _normalize_datetime(
            completed_at,
            field_name="occurred_at",
        )

        if normalized_completed_at is None:
            raise ValueError("occurred_at cannot be null.")

        self.apply_updates(
            status="completed",
            completed_at=normalized_completed_at,
            artifact_id=artifact_id,
            error=None,
        )

    def mark_failed(
        self,
        *,
        error: SessionError,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark the specialist as failed."""

        if self.status != "running":
            raise ValueError("Only a running specialist can fail.")

        completed_at = occurred_at or error.occurred_at
        normalized_completed_at = _normalize_datetime(
            completed_at,
            field_name="occurred_at",
        )

        if normalized_completed_at is None:
            raise ValueError("occurred_at cannot be null.")

        self.apply_updates(
            status="failed",
            completed_at=normalized_completed_at,
            error=error,
            artifact_id=None,
        )

    def prepare_revision(self) -> None:
        """Prepare a completed or failed specialist for targeted revision."""

        if self.status not in {
            "completed",
            "failed",
        }:
            raise ValueError("Only completed or failed specialists can be revised.")

        self.apply_updates(
            status="pending",
            started_at=None,
            completed_at=None,
            artifact_id=None,
            error=None,
            revision_count=self.revision_count + 1,
        )


class FlowRuntimeLimits(BuildWiseModel):
    """Execution limits copied into state when a consultation begins."""

    maximum_session_tokens: int = Field(default=120_000, ge=1_000)
    maximum_estimated_cost_usd: float = Field(default=10.0, ge=0.0)

    maximum_agent_executions: int = Field(default=20, ge=1)
    maximum_tool_calls: int = Field(default=30, ge=0)

    maximum_specialist_revisions: int = Field(default=2, ge=0, le=10)
    maximum_clarification_rounds: int = Field(default=3, ge=1, le=10)

    maximum_execution_seconds: int = Field(
        default=900,
        ge=60,
        le=3_600,
    )


class BuildWiseFlowState(BuildWiseModel):
    """Typed shared state for the BuildWise consulting Flow.

    CrewAI automatically manages the Flow state's own runtime identifier.
    BuildWise keeps a separate session_id because the consulting session is a
    business entity persisted and exposed through the application API.

    The state deliberately stores only data required across Flow stages.
    Temporary Crew execution details remain inside their Crew execution and
    are persisted separately through tracing and usage records.
    """

    session_id: SessionId = Field(default_factory=generate_uuid)
    request_id: RequestId = Field(default_factory=generate_uuid)

    correlation_id: ShortText | None = None

    status: SessionStatus = SessionStatus.CREATED
    stage: SessionStage = SessionStage.INTAKE

    intake_request: ProductIdeaRequest | None = None
    validated_idea: ValidatedProductIdea | None = None
    product_context: ProductIdeaContext | None = None

    discovery_result: DiscoveryResult | None = None
    clarification_question_set: ClarificationQuestionSet | None = None
    clarification_answers: list[ClarificationAnswer] = Field(
        default_factory=list,
    )
    clarification_round: int = Field(default=0, ge=0)

    product_definition: ProductDefinition | None = None
    requirements_specification: RequirementsSpecification | None = None
    solution_architecture: SolutionArchitecture | None = None
    product_planning_result: ProductPlanningResult | None = None
    specialist_execution_plan: SpecialistExecutionPlan | None = None
    technical_planning_result: TechnicalPlanningResult | None = None
    lead_review: LeadReview | None = None
    revision_history: list[RevisionRequest] = Field(default_factory=list)

    specialist_executions: list[SpecialistExecutionState] = Field(
        default_factory=list,
    )

    review_artifact_id: ArtifactId | None = None
    blueprint_artifact_id: ArtifactId | None = None

    revision_count: int = Field(default=0, ge=0)

    usage: UsageSummary = Field(default_factory=UsageSummary)
    limits: FlowRuntimeLimits = Field(default_factory=FlowRuntimeLimits)

    transitions: list[FlowStageTransition] = Field(default_factory=list)
    warnings: list[WarningMessage] = Field(default_factory=list)
    errors: list[SessionError] = Field(default_factory=list)

    last_completed_stage: SessionStage | None = None

    started_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    failed_at: datetime | None = None

    @field_validator(
        "started_at",
        "updated_at",
        "completed_at",
        "failed_at",
    )
    @classmethod
    def normalize_runtime_timestamp(
        cls,
        value: datetime | None,
        info: object,
    ) -> datetime | None:
        """Normalize Flow runtime timestamps to UTC."""

        field_name = getattr(info, "field_name", "timestamp")

        return _normalize_datetime(
            value,
            field_name=field_name,
        )

    @field_validator("clarification_answers")
    @classmethod
    def ensure_unique_clarification_answers(
        cls,
        value: list[ClarificationAnswer],
    ) -> list[ClarificationAnswer]:
        """Prevent duplicate answers for the same question."""

        question_ids = [answer.question_id for answer in value]

        _ensure_unique_values(
            question_ids,
            field_name="clarification answer question IDs",
        )

        return value

    @field_validator("specialist_executions")
    @classmethod
    def ensure_unique_specialist_executions(
        cls,
        value: list[SpecialistExecutionState],
    ) -> list[SpecialistExecutionState]:
        """Prevent duplicate runtime records for one specialist."""

        specialists = [execution.specialist for execution in value]

        _ensure_unique_values(
            specialists,
            field_name="specialist executions",
        )

        return value

    @field_validator("transitions")
    @classmethod
    def ensure_unique_transitions(
        cls,
        value: list[FlowStageTransition],
    ) -> list[FlowStageTransition]:
        """Prevent duplicate transition identifiers."""

        transition_ids = [transition.id for transition in value]

        _ensure_unique_values(
            transition_ids,
            field_name="Flow transition IDs",
        )

        return value

    @field_validator("errors")
    @classmethod
    def ensure_unique_errors(
        cls,
        value: list[SessionError],
    ) -> list[SessionError]:
        """Prevent duplicate session errors."""

        error_ids = [error.id for error in value]

        _ensure_unique_values(
            error_ids,
            field_name="Flow error IDs",
        )

        return value

    @model_validator(mode="after")
    def validate_flow_state(self) -> BuildWiseFlowState:
        """Validate session ownership and terminal lifecycle consistency."""

        self._validate_artifact_session_ownership()
        self._validate_clarification_state()
        self._validate_terminal_state()
        self._validate_runtime_timestamps()
        self._validate_specialist_artifacts()

        return self

    def _validate_artifact_session_ownership(self) -> None:
        """Require every session-owned artifact to belong to this state."""

        session_owned_artifacts: list[tuple[str, object | None]] = [
            ("validated_idea", self.validated_idea),
            ("product_context", self.product_context),
            ("discovery_result", self.discovery_result),
            (
                "clarification_question_set",
                self.clarification_question_set,
            ),
            ("product_definition", self.product_definition),
            (
                "requirements_specification",
                self.requirements_specification,
            ),
            ("solution_architecture", self.solution_architecture),
            ("product_planning_result", self.product_planning_result),
            ("technical_planning_result", self.technical_planning_result),
        ]

        for field_name, artifact in session_owned_artifacts:
            if artifact is None:
                continue

            artifact_session_id = getattr(
                artifact,
                "session_id",
                None,
            )

            if artifact_session_id != self.session_id:
                raise ValueError(f"{field_name}.session_id must match Flow session_id.")

    def _validate_clarification_state(self) -> None:
        """Validate clarification round, questions, answers, and status."""

        if (
            self.clarification_question_set is not None
            and self.clarification_question_set.round_number != self.clarification_round
        ):
            raise ValueError(
                "clarification_question_set.round_number must match clarification_round."
            )

        if self.clarification_round == 0:
            if self.clarification_question_set is not None:
                raise ValueError(
                    "clarification_round must be greater than zero when a question set exists."
                )

            if self.clarification_answers:
                raise ValueError(
                    "clarification_round must be greater than zero when "
                    "clarification answers exist."
                )

        if self.status is SessionStatus.AWAITING_USER_INPUT:
            if self.stage is not SessionStage.CLARIFICATION:
                raise ValueError("A Flow awaiting user input must be in the clarification stage.")

            if self.clarification_question_set is None:
                raise ValueError(
                    "A Flow awaiting user input requires a clarification question set."
                )

        if self.status is SessionStatus.RESUMING:
            if self.stage is not SessionStage.CLARIFICATION:
                raise ValueError("A resuming Flow must resume from the clarification stage.")

            if not self.clarification_answers:
                raise ValueError("A resuming Flow requires clarification answers.")

    def _validate_terminal_state(self) -> None:
        """Validate completed and failed state combinations."""

        completed_statuses = {
            SessionStatus.COMPLETED,
            SessionStatus.COMPLETED_WITH_LIMITATIONS,
        }

        if self.status in completed_statuses:
            if self.stage is not SessionStage.COMPLETED:
                raise ValueError("A completed Flow must use the completed stage.")

            if self.completed_at is None:
                raise ValueError("A completed Flow requires completed_at.")

            if self.failed_at is not None:
                raise ValueError("A completed Flow cannot contain failed_at.")

            if self.blueprint_artifact_id is None:
                raise ValueError("A completed Flow requires blueprint_artifact_id.")

        if self.status is SessionStatus.COMPLETED_WITH_LIMITATIONS and not self.warnings:
            raise ValueError("A Flow completed with limitations requires at least one warning.")

        if self.status is SessionStatus.FAILED:
            if self.stage is not SessionStage.FAILED:
                raise ValueError("A failed Flow must use the failed stage.")

            if self.failed_at is None:
                raise ValueError("A failed Flow requires failed_at.")

            if self.completed_at is not None:
                raise ValueError("A failed Flow cannot contain completed_at.")

            if not self.errors:
                raise ValueError("A failed Flow requires at least one recorded error.")

        if (
            self.status
            not in {
                SessionStatus.COMPLETED,
                SessionStatus.COMPLETED_WITH_LIMITATIONS,
            }
            and self.completed_at is not None
        ):
            raise ValueError("completed_at may only be set for a completed Flow.")

        if self.status is not SessionStatus.FAILED and self.failed_at is not None:
            raise ValueError("failed_at may only be set for a failed Flow.")

    def _validate_runtime_timestamps(self) -> None:
        """Validate Flow timestamp ordering."""

        if self.started_at is not None:
            if self.updated_at < self.started_at:
                raise ValueError("updated_at cannot be earlier than started_at.")

            if self.completed_at is not None and self.completed_at < self.started_at:
                raise ValueError("completed_at cannot be earlier than started_at.")

            if self.failed_at is not None and self.failed_at < self.started_at:
                raise ValueError("failed_at cannot be earlier than started_at.")

    def _validate_specialist_artifacts(self) -> None:
        """Validate known specialist artifacts against execution records."""

        solution_execution = self.get_specialist_execution(SpecialistType.SOLUTION_ARCHITECTURE)

        if self.solution_architecture is not None:
            if solution_execution is None:
                raise ValueError(
                    "solution_architecture requires a solution architecture specialist execution."
                )

            if solution_execution.status != "completed":
                raise ValueError(
                    "solution_architecture requires a completed solution "
                    "architecture specialist execution."
                )

            if solution_execution.artifact_id != self.solution_architecture.id:
                raise ValueError(
                    "The solution architecture specialist artifact_id must "
                    "match SolutionArchitecture.id."
                )

    @property
    def is_terminal(self) -> bool:
        """Return whether the Flow reached a terminal state."""

        return self.status in {
            SessionStatus.COMPLETED,
            SessionStatus.COMPLETED_WITH_LIMITATIONS,
            SessionStatus.FAILED,
        }

    @property
    def selected_specialists(self) -> list[SpecialistType]:
        """Return all specialists selected for execution."""

        return [
            execution.specialist
            for execution in self.specialist_executions
            if execution.status
            not in {
                "not_selected",
                "skipped",
            }
        ]

    @property
    def completed_specialists(self) -> list[SpecialistType]:
        """Return all successfully completed specialists."""

        return [
            execution.specialist
            for execution in self.specialist_executions
            if execution.status == "completed"
        ]

    @property
    def failed_specialists(self) -> list[SpecialistType]:
        """Return all specialists whose latest execution failed."""

        return [
            execution.specialist
            for execution in self.specialist_executions
            if execution.status == "failed"
        ]

    def get_specialist_execution(
        self,
        specialist: SpecialistType,
    ) -> SpecialistExecutionState | None:
        """Return runtime state for a specialist when it exists."""

        return next(
            (
                execution
                for execution in self.specialist_executions
                if execution.specialist is specialist
            ),
            None,
        )

    def start_flow(
        self,
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        """Start a newly created Flow."""

        if self.status is not SessionStatus.CREATED:
            raise ValueError("Only a created Flow can be started.")

        started_at = occurred_at or utc_now()
        normalized_started_at = _normalize_datetime(
            started_at,
            field_name="occurred_at",
        )

        if normalized_started_at is None:
            raise ValueError("occurred_at cannot be null.")

        self.transition_to(
            stage=SessionStage.INTAKE,
            status=SessionStatus.PROCESSING,
            reason="flow_started",
            description="The BuildWise consulting Flow started.",
            occurred_at=normalized_started_at,
            started_at=normalized_started_at,
        )

    def transition_to(
        self,
        *,
        stage: SessionStage,
        status: SessionStatus,
        reason: FlowTransitionReason,
        description: str | None = None,
        occurred_at: datetime | None = None,
        **extra_updates: object,
    ) -> None:
        """Transition the Flow to a new stage and status.

        ``extra_updates`` lets a caller change other fields (for example
        ``completed_at`` or ``blueprint_artifact_id``) atomically together
        with the stage/status transition, so the model is never validated in
        an intermediate state where only part of the change is visible.
        """

        if self.is_terminal:
            raise ValueError("A terminal Flow cannot transition to another stage.")

        transition_time = occurred_at or utc_now()
        normalized_transition_time = _normalize_datetime(
            transition_time,
            field_name="occurred_at",
        )

        if normalized_transition_time is None:
            raise ValueError("occurred_at cannot be null.")

        transition = FlowStageTransition(
            from_stage=self.stage,
            to_stage=stage,
            from_status=self.status,
            to_status=status,
            reason=reason,
            description=description,
            occurred_at=normalized_transition_time,
        )

        updates: dict[str, object] = {
            "stage": stage,
            "status": status,
            "updated_at": normalized_transition_time,
            **extra_updates,
        }

        if stage != self.stage:
            updates["last_completed_stage"] = self.stage

        self.apply_updates(**updates)
        self.transitions.append(transition)

    def request_clarification(
        self,
        *,
        question_set: ClarificationQuestionSet,
        occurred_at: datetime | None = None,
    ) -> None:
        """Pause the Flow for user clarification."""

        if question_set.session_id != self.session_id:
            raise ValueError("Clarification question set session_id must match Flow session_id.")

        if question_set.round_number > self.limits.maximum_clarification_rounds:
            raise ValueError("The maximum number of clarification rounds was exceeded.")

        self.transition_to(
            stage=SessionStage.CLARIFICATION,
            status=SessionStatus.AWAITING_USER_INPUT,
            reason="clarification_required",
            description=question_set.summary,
            occurred_at=occurred_at,
            clarification_round=question_set.round_number,
            clarification_question_set=question_set,
        )

    def receive_clarification_answers(
        self,
        *,
        answers: list[ClarificationAnswer],
        occurred_at: datetime | None = None,
    ) -> None:
        """Store answers and prepare the paused Flow for resumption."""

        if self.status is not SessionStatus.AWAITING_USER_INPUT:
            raise ValueError(
                "Clarification answers can only be submitted while the Flow is awaiting user input."
            )

        if self.clarification_question_set is None:
            raise ValueError("No active clarification question set exists.")

        if not answers:
            raise ValueError("At least one clarification answer is required.")

        active_question_ids = {
            question.id for question in self.clarification_question_set.questions
        }
        submitted_question_ids = {answer.question_id for answer in answers}

        unknown_question_ids = submitted_question_ids.difference(active_question_ids)

        if unknown_question_ids:
            formatted = ", ".join(sorted(str(identifier) for identifier in unknown_question_ids))
            raise ValueError(
                f"Clarification answers reference questions outside the active set: {formatted}."
            )

        existing_question_ids = {answer.question_id for answer in self.clarification_answers}
        duplicate_question_ids = submitted_question_ids.intersection(existing_question_ids)

        if duplicate_question_ids:
            formatted = ", ".join(sorted(str(identifier) for identifier in duplicate_question_ids))
            raise ValueError(f"Clarification questions have already been answered: {formatted}.")

        required_question_ids = {
            question.id
            for question in self.clarification_question_set.questions
            if question.required
        }
        unanswered_required_ids = required_question_ids.difference(submitted_question_ids)

        if unanswered_required_ids:
            formatted = ", ".join(sorted(str(identifier) for identifier in unanswered_required_ids))
            raise ValueError(f"Required clarification questions were not answered: {formatted}.")

        self.clarification_answers.extend(answers)

        self.transition_to(
            stage=SessionStage.CLARIFICATION,
            status=SessionStatus.RESUMING,
            reason="clarification_received",
            description=("Clarification answers were received and the Flow is ready to resume."),
            occurred_at=occurred_at,
        )

    def register_specialist(
        self,
        *,
        specialist: SpecialistType,
        selected: bool,
        reason: str | None,
        rationale: str,
    ) -> None:
        """Register a specialist selection decision."""

        if self.get_specialist_execution(specialist) is not None:
            raise ValueError(f"Specialist '{specialist.value}' is already registered.")

        if selected:
            if reason is None:
                raise ValueError("A selected specialist requires a selection reason.")

            execution = SpecialistExecutionState(
                specialist=specialist,
                status="pending",
                selected_reason=reason,
                selection_rationale=rationale,
            )
        else:
            execution = SpecialistExecutionState(
                specialist=specialist,
                status="not_selected",
                selection_rationale=None,
            )

        self.specialist_executions.append(execution)
        self.updated_at = utc_now()

    def mark_specialist_running(
        self,
        *,
        specialist: SpecialistType,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark a selected specialist as running."""

        execution = self._require_specialist_execution(specialist)
        execution.mark_running(occurred_at=occurred_at)
        self.updated_at = execution.started_at or utc_now()

    def mark_specialist_completed(
        self,
        *,
        specialist: SpecialistType,
        artifact_id: ArtifactId,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark a selected specialist as successfully completed."""

        execution = self._require_specialist_execution(specialist)
        execution.mark_completed(
            artifact_id=artifact_id,
            occurred_at=occurred_at,
        )
        self.updated_at = execution.completed_at or utc_now()

    def mark_specialist_failed(
        self,
        *,
        specialist: SpecialistType,
        error: SessionError,
        occurred_at: datetime | None = None,
    ) -> None:
        """Mark a specialist as failed and retain its normalized error."""

        execution = self._require_specialist_execution(specialist)
        execution.mark_failed(
            error=error,
            occurred_at=occurred_at,
        )
        self.errors.append(error)
        self.updated_at = execution.completed_at or utc_now()

    def prepare_specialist_revision(
        self,
        *,
        specialist: SpecialistType,
    ) -> None:
        """Prepare a specialist for one targeted review revision."""

        if self.revision_count >= self.limits.maximum_specialist_revisions:
            raise ValueError("The maximum number of specialist revisions was exceeded.")

        execution = self._require_specialist_execution(specialist)
        execution.prepare_revision()

        self.revision_count += 1
        self.updated_at = utc_now()

    def set_validated_idea(
        self,
        validated_idea: ValidatedProductIdea,
    ) -> None:
        """Store the deterministically validated intake artifact."""

        self._require_matching_session(
            artifact_name="validated_idea",
            artifact_session_id=validated_idea.session_id,
        )
        self.validated_idea = validated_idea
        self.updated_at = utc_now()

    def set_product_context(
        self,
        product_context: ProductIdeaContext,
    ) -> None:
        """Store the canonical product idea context."""

        self._require_matching_session(
            artifact_name="product_context",
            artifact_session_id=product_context.session_id,
        )
        self.product_context = product_context
        self.updated_at = utc_now()

    def set_discovery_result(
        self,
        discovery_result: DiscoveryResult,
    ) -> None:
        """Store the Discovery Crew output."""

        self._require_matching_session(
            artifact_name="discovery_result",
            artifact_session_id=discovery_result.session_id,
        )
        self.discovery_result = discovery_result
        self.updated_at = utc_now()

    def set_product_definition(
        self,
        product_definition: ProductDefinition,
    ) -> None:
        """Store and validate the Product Definition Crew output."""

        self._require_matching_session(
            artifact_name="product_definition",
            artifact_session_id=product_definition.session_id,
        )

        if self.discovery_result is None:
            raise ValueError("A discovery result is required before product definition.")

        ProductDefinition.validate_discovery_ownership(
            product_definition=product_definition,
            discovery_result=self.discovery_result,
        )

        self.product_definition = product_definition
        self.updated_at = utc_now()

    def set_requirements_specification(
        self,
        requirements_specification: RequirementsSpecification,
    ) -> None:
        """Store and validate the Requirements Crew output."""

        self._require_matching_session(
            artifact_name="requirements_specification",
            artifact_session_id=requirements_specification.session_id,
        )

        if self.product_definition is None:
            raise ValueError("A product definition is required before requirements.")

        RequirementsSpecification.validate_product_ownership(
            requirements_specification=requirements_specification,
            product_definition=self.product_definition,
        )

        self.requirements_specification = requirements_specification
        self.updated_at = utc_now()

    def set_solution_architecture(
        self,
        solution_architecture: SolutionArchitecture,
    ) -> None:
        """Store and validate the Solution Architecture Crew output."""

        self._require_matching_session(
            artifact_name="solution_architecture",
            artifact_session_id=solution_architecture.session_id,
        )

        if self.requirements_specification is None:
            raise ValueError(
                "A requirements specification is required before solution architecture."
            )

        SolutionArchitecture.validate_requirements_ownership(
            solution_architecture=solution_architecture,
            requirements_specification=self.requirements_specification,
        )

        execution = self._require_specialist_execution(SpecialistType.SOLUTION_ARCHITECTURE)

        if execution.status != "completed":
            raise ValueError(
                "The solution architecture specialist must be completed "
                "before storing its artifact."
            )

        if execution.artifact_id != solution_architecture.id:
            raise ValueError("The specialist artifact_id must match SolutionArchitecture.id.")

        self.solution_architecture = solution_architecture
        self.updated_at = utc_now()

    def set_product_planning_result(
        self,
        result: ProductPlanningResult,
    ) -> None:
        """Store the validated aggregate produced by Product Planning."""

        self._require_matching_session(
            artifact_name="product_planning_result",
            artifact_session_id=result.session_id,
        )
        if self.discovery_result is None:
            raise ValueError("A discovery result is required before product planning.")

        ProductDefinition.validate_discovery_ownership(
            product_definition=result.product_definition,
            discovery_result=self.discovery_result,
        )
        self.apply_updates(
            product_planning_result=result,
            product_definition=result.product_definition,
            requirements_specification=result.requirements,
            updated_at=utc_now(),
        )

    def set_specialist_execution_plan(
        self,
        plan: SpecialistExecutionPlan,
    ) -> None:
        """Store the deterministic specialist plan used by the technical Crew."""

        if self.product_planning_result is None:
            raise ValueError("Product planning is required before specialist planning.")
        self.specialist_execution_plan = plan
        self.updated_at = utc_now()

    def set_technical_planning_result(
        self,
        result: TechnicalPlanningResult,
    ) -> None:
        """Store and cross-check the aggregate produced by Technical Planning."""

        self._require_matching_session(
            artifact_name="technical_planning_result",
            artifact_session_id=result.session_id,
        )
        if self.specialist_execution_plan is None:
            raise ValueError("A specialist execution plan is required before technical planning.")

        selected = {
            recommendation.specialist
            for recommendation in self.specialist_execution_plan.recommendations
        }
        result.validate_specialist_selection(
            ai_selected=SpecialistType.AI_ARCHITECTURE in selected,
            security_selected=SpecialistType.SECURITY_ARCHITECTURE in selected,
            qa_selected=SpecialistType.QA_AND_EVALUATION in selected,
        )
        self.apply_updates(
            technical_planning_result=result,
            solution_architecture=result.solution_architecture,
            updated_at=utc_now(),
        )

    def set_lead_review(self, review: LeadReview) -> None:
        """Store the latest Lead Review and append its revision requests."""

        self.lead_review = review
        self.revision_history.extend(review.revision_requests)
        self.updated_at = utc_now()

    def add_warning(self, warning: WarningMessage) -> None:
        """Add a non-fatal Flow warning."""

        self.warnings.append(warning)
        self.updated_at = utc_now()

    def add_error(self, error: SessionError) -> None:
        """Add a normalized Flow error without terminating execution."""

        if any(existing.id == error.id for existing in self.errors):
            raise ValueError("The supplied error is already recorded in Flow state.")

        self.errors.append(error)
        self.updated_at = error.occurred_at

    def mark_completed(
        self,
        *,
        blueprint_artifact_id: ArtifactId,
        review_artifact_id: ArtifactId,
        completed_with_limitations: bool = False,
        occurred_at: datetime | None = None,
    ) -> None:
        """Complete the Flow after review and blueprint assembly."""

        completion_time = occurred_at or utc_now()
        normalized_completion_time = _normalize_datetime(
            completion_time,
            field_name="occurred_at",
        )

        if normalized_completion_time is None:
            raise ValueError("occurred_at cannot be null.")

        if completed_with_limitations and not self.warnings:
            raise ValueError("A Flow cannot complete with limitations without warnings.")

        self.transition_to(
            stage=SessionStage.COMPLETED,
            status=(
                SessionStatus.COMPLETED_WITH_LIMITATIONS
                if completed_with_limitations
                else SessionStatus.COMPLETED
            ),
            reason="flow_completed",
            description="The BuildWise consulting Flow completed.",
            occurred_at=normalized_completion_time,
            review_artifact_id=review_artifact_id,
            blueprint_artifact_id=blueprint_artifact_id,
            completed_at=normalized_completion_time,
            failed_at=None,
        )

    def mark_failed(
        self,
        *,
        error: SessionError,
        occurred_at: datetime | None = None,
    ) -> None:
        """Terminate the Flow with a normalized failure."""

        failure_time = occurred_at or error.occurred_at
        normalized_failure_time = _normalize_datetime(
            failure_time,
            field_name="occurred_at",
        )

        if normalized_failure_time is None:
            raise ValueError("occurred_at cannot be null.")

        if not any(existing.id == error.id for existing in self.errors):
            self.errors.append(error)

        self.transition_to(
            stage=SessionStage.FAILED,
            status=SessionStatus.FAILED,
            reason="flow_failed",
            description=error.message,
            occurred_at=normalized_failure_time,
            failed_at=normalized_failure_time,
            completed_at=None,
        )

    def _require_specialist_execution(
        self,
        specialist: SpecialistType,
    ) -> SpecialistExecutionState:
        """Return a specialist execution or raise a clear error."""

        execution = self.get_specialist_execution(specialist)

        if execution is None:
            raise ValueError(f"Specialist '{specialist.value}' is not registered.")

        return execution

    def _require_matching_session(
        self,
        *,
        artifact_name: str,
        artifact_session_id: SessionId,
    ) -> None:
        """Require an artifact to belong to this Flow session."""

        if artifact_session_id != self.session_id:
            raise ValueError(f"{artifact_name}.session_id must match Flow session_id.")
