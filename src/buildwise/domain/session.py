from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    MediumText,
    RequestId,
    SessionId,
    ShortText,
    Slug,
    TimestampedModel,
    WarningMessage,
    generate_uuid,
    utc_now,
)
from buildwise.domain.enums import SessionStage, SessionStatus


class SessionMetadata(BuildWiseModel):
    """Operational and request metadata associated with a consulting session.

    This model contains request-level context and tracing information. It must
    not contain product discovery results, requirements, specialist outputs,
    or other business artifacts.
    """

    request_id: RequestId = Field(default_factory=generate_uuid)
    user_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    organization_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    source_channel: Slug = "api"
    locale: str = Field(
        default="en-US",
        min_length=2,
        max_length=20,
    )
    timezone: str = Field(
        default="UTC",
        min_length=1,
        max_length=100,
    )

    client_name: ShortText | None = None
    client_version: ShortText | None = None

    correlation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    trace_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    tags: list[Slug] = Field(default_factory=list)

    attributes: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
    )

    @field_validator("user_id", "organization_id", "correlation_id", "trace_id")
    @classmethod
    def normalize_optional_identifier(cls, value: str | None) -> str | None:
        """Trim optional identifiers and reject whitespace-only values."""

        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError("Identifier cannot contain only whitespace.")

        return normalized

    @field_validator("tags")
    @classmethod
    def ensure_unique_tags(cls, value: list[Slug]) -> list[Slug]:
        """Reject duplicate session tags while preserving their order."""

        if len(value) != len(set(value)):
            raise ValueError("Session metadata tags must be unique.")

        return value


class SessionError(BuildWiseModel):
    """A normalized error captured during the consulting-session lifecycle."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    code: Slug
    message: MediumText
    stage: SessionStage

    recoverable: bool = False
    retryable: bool = False
    retry_count: int = Field(default=0, ge=0)

    agent_name: ShortText | None = None
    task_name: ShortText | None = None
    tool_name: ShortText | None = None

    exception_type: ShortText | None = None

    details: dict[str, Any] = Field(default_factory=dict)

    occurred_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None
    resolution: MediumText | None = None

    @field_validator("occurred_at", "resolved_at")
    @classmethod
    def normalize_error_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require all error timestamps to be timezone-aware."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Session error timestamps must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_resolution(self) -> SessionError:
        """Ensure error resolution metadata is internally consistent."""

        if self.resolved_at is not None and self.resolved_at < self.occurred_at:
            raise ValueError("resolved_at cannot be earlier than occurred_at.")

        if self.resolved_at is None and self.resolution is not None:
            raise ValueError("resolution cannot be provided when resolved_at is not set.")

        if self.resolved_at is not None and self.resolution is None:
            raise ValueError("resolution is required when resolved_at is provided.")

        if self.retry_count > 0 and not self.retryable:
            raise ValueError("retry_count cannot be greater than zero when retryable is false.")

        return self

    @property
    def is_resolved(self) -> bool:
        """Return whether this error has been resolved."""

        return self.resolved_at is not None


class ConsultingSession(TimestampedModel):
    """Canonical lifecycle record for a BuildWise consultation.

    This model owns session identity and lifecycle state. Detailed consulting
    artifacts such as discovery results, product definitions, requirements,
    specialist reports, reviews, and blueprints belong to the canonical Flow
    state and their respective domain models.
    """

    id: SessionId = Field(default_factory=generate_uuid)

    status: SessionStatus = SessionStatus.CREATED
    stage: SessionStage = SessionStage.INTAKE

    metadata: SessionMetadata = Field(default_factory=SessionMetadata)

    errors: list[SessionError] = Field(default_factory=list)
    warnings: list[WarningMessage] = Field(default_factory=list)

    session_version: int = Field(default=1, ge=1)
    state_revision: int = Field(default=0, ge=0)

    clarification_round: int = Field(default=0, ge=0)
    refinement_round: int = Field(default=0, ge=0)

    last_activity_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    failed_at: datetime | None = None

    completion_summary: MediumText | None = None

    @field_validator(
        "last_activity_at",
        "completed_at",
        "failed_at",
    )
    @classmethod
    def normalize_session_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require lifecycle timestamps to be timezone-aware."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Session lifecycle timestamps must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_lifecycle_state(self) -> ConsultingSession:
        """Validate consistency between status, stage, and terminal timestamps."""

        terminal_statuses = {
            SessionStatus.COMPLETED,
            SessionStatus.COMPLETED_WITH_LIMITATIONS,
            SessionStatus.FAILED,
        }

        completed_statuses = {
            SessionStatus.COMPLETED,
            SessionStatus.COMPLETED_WITH_LIMITATIONS,
        }

        if self.last_activity_at < self.created_at:
            raise ValueError("last_activity_at cannot be earlier than created_at.")

        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at cannot be earlier than created_at.")

        if self.failed_at is not None and self.failed_at < self.created_at:
            raise ValueError("failed_at cannot be earlier than created_at.")

        if self.status in completed_statuses:
            if self.stage is not SessionStage.COMPLETED:
                raise ValueError("A completed session must use the completed session stage.")

            if self.completed_at is None:
                raise ValueError("completed_at is required for a completed session.")

            if self.failed_at is not None:
                raise ValueError("A completed session cannot contain failed_at.")

        if self.status is SessionStatus.FAILED:
            if self.stage is not SessionStage.FAILED:
                raise ValueError("A failed session must use the failed session stage.")

            if self.failed_at is None:
                raise ValueError("failed_at is required for a failed session.")

            if self.completed_at is not None:
                raise ValueError("A failed session cannot contain completed_at.")

        if self.status not in terminal_statuses:
            if self.completed_at is not None:
                raise ValueError("completed_at can only be set for a completed session.")

            if self.failed_at is not None:
                raise ValueError("failed_at can only be set for a failed session.")

        if (
            self.status is SessionStatus.AWAITING_USER_INPUT
            and self.stage is not SessionStage.CLARIFICATION
        ):
            raise ValueError("A session awaiting user input must be in the clarification stage.")

        if self.status is SessionStatus.REVIEWING and self.stage is not SessionStage.LEAD_REVIEW:
            raise ValueError("A reviewing session must be in the lead-review stage.")

        if self.status is SessionStatus.RESUMING and self.stage is not SessionStage.CLARIFICATION:
            raise ValueError("A resuming session must resume from the clarification stage.")

        if self.status is SessionStatus.COMPLETED_WITH_LIMITATIONS and not self.warnings:
            raise ValueError(
                "A session completed with limitations must contain at least one warning."
            )

        return self

    @property
    def is_terminal(self) -> bool:
        """Return whether the session has reached a terminal status."""

        return self.status in {
            SessionStatus.COMPLETED,
            SessionStatus.COMPLETED_WITH_LIMITATIONS,
            SessionStatus.FAILED,
        }

    @property
    def has_unresolved_errors(self) -> bool:
        """Return whether at least one captured error remains unresolved."""

        return any(not error.is_resolved for error in self.errors)

    def record_activity(self, *, occurred_at: datetime | None = None) -> None:
        """Update the session's last-activity timestamp and state revision."""

        activity_time = occurred_at or utc_now()

        if activity_time.tzinfo is None or activity_time.utcoffset() is None:
            raise ValueError("Activity timestamp must be timezone-aware.")

        normalized_time = activity_time.astimezone(UTC)

        if normalized_time < self.created_at:
            raise ValueError("Activity timestamp cannot be earlier than session creation.")

        self.apply_updates(
            last_activity_at=normalized_time,
            updated_at=normalized_time,
            state_revision=self.state_revision + 1,
        )

    def add_error(self, error: SessionError) -> None:
        """Append an error and record a session-state revision."""

        self.errors.append(error)
        self.record_activity(occurred_at=error.occurred_at)

    def add_warning(self, warning: WarningMessage) -> None:
        """Append a warning and record a session-state revision."""

        self.warnings.append(warning)
        self.record_activity()

    def mark_completed(
        self,
        *,
        completed_with_limitations: bool = False,
        summary: str | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        """Transition the session to a completed terminal state."""

        completion_time = occurred_at or utc_now()

        if completion_time.tzinfo is None or completion_time.utcoffset() is None:
            raise ValueError("Completion timestamp must be timezone-aware.")

        normalized_time = completion_time.astimezone(UTC)

        if completed_with_limitations and not self.warnings:
            raise ValueError("Cannot complete with limitations without at least one warning.")

        self.apply_updates(
            status=(
                SessionStatus.COMPLETED_WITH_LIMITATIONS
                if completed_with_limitations
                else SessionStatus.COMPLETED
            ),
            stage=SessionStage.COMPLETED,
            completed_at=normalized_time,
            failed_at=None,
            completion_summary=summary,
            last_activity_at=normalized_time,
            updated_at=normalized_time,
            state_revision=self.state_revision + 1,
        )

    def mark_failed(
        self,
        *,
        error: SessionError,
        occurred_at: datetime | None = None,
    ) -> None:
        """Transition the session to a failed terminal state."""

        failure_time = occurred_at or error.occurred_at

        if failure_time.tzinfo is None or failure_time.utcoffset() is None:
            raise ValueError("Failure timestamp must be timezone-aware.")

        normalized_time = failure_time.astimezone(UTC)

        self.errors.append(error)

        self.apply_updates(
            status=SessionStatus.FAILED,
            stage=SessionStage.FAILED,
            failed_at=normalized_time,
            completed_at=None,
            last_activity_at=normalized_time,
            updated_at=normalized_time,
            state_revision=self.state_revision + 1,
        )
