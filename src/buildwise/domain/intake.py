from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    LongText,
    MediumText,
    SessionId,
    ShortText,
    Slug,
    SourceMetadata,
    generate_uuid,
    utc_now,
)
from buildwise.domain.enums import ConfidenceLevel

IdeaTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=200,
    ),
]

IdeaDescription = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=20,
        max_length=20_000,
    ),
]

ClarificationQuestionId = ArtifactId

IdeaSubmissionChannel = Literal[
    "api",
    "web",
    "cli",
    "internal",
]

IdeaMaturity = Literal[
    "raw_idea",
    "early_concept",
    "partially_defined",
    "well_defined",
]

TargetPlatform = Literal[
    "web",
    "mobile",
    "desktop",
    "api",
    "browser_extension",
    "messaging_platform",
    "internal_tool",
    "multi_platform",
    "not_decided",
]

DeliveryExpectation = Literal[
    "prototype",
    "mvp",
    "production_v1",
    "modernization",
    "not_decided",
]

ClarificationAnswerValue = str | int | float | bool | list[str] | None


class ProductIdeaRequest(BuildWiseModel):
    """Raw user input that starts a BuildWise consulting session.

    This model represents only the information supplied at intake time. It
    intentionally permits uncertainty and incomplete optional fields because
    completeness is evaluated later by the Discovery stage.
    """

    title: IdeaTitle | None = None
    idea: IdeaDescription

    problem_statement: MediumText | None = None
    target_users: list[ShortText] = Field(default_factory=list)
    desired_outcomes: list[MediumText] = Field(default_factory=list)

    known_features: list[MediumText] = Field(default_factory=list)
    known_constraints: list[MediumText] = Field(default_factory=list)
    existing_assumptions: list[MediumText] = Field(default_factory=list)

    target_platforms: list[TargetPlatform] = Field(default_factory=list)
    delivery_expectation: DeliveryExpectation = "not_decided"
    idea_maturity: IdeaMaturity = "raw_idea"

    preferred_timeline: ShortText | None = None
    estimated_budget: ShortText | None = None

    industry: ShortText | None = None
    target_market: ShortText | None = None
    geographic_scope: list[ShortText] = Field(default_factory=list)

    existing_product: bool = False
    existing_product_description: MediumText | None = None

    requests_ai_capabilities: bool | None = None
    handles_sensitive_data: bool | None = None
    regulated_domain: bool | None = None

    additional_context: LongText | None = None

    submission_channel: IdeaSubmissionChannel = "api"
    submitted_at: datetime = Field(default_factory=utc_now)

    @field_validator("submitted_at")
    @classmethod
    def normalize_submitted_at(cls, value: datetime) -> datetime:
        """Require the intake timestamp to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("submitted_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator(
        "target_users",
        "desired_outcomes",
        "known_features",
        "known_constraints",
        "existing_assumptions",
        "target_platforms",
        "geographic_scope",
    )
    @classmethod
    def reject_duplicate_list_values[T](cls, value: list[T]) -> list[T]:
        """Reject duplicated intake values while preserving user intent."""

        if len(value) != len(set(value)):
            raise ValueError("List values must be unique.")

        return value

    @model_validator(mode="after")
    def validate_existing_product_context(self) -> ProductIdeaRequest:
        """Require details when the request describes an existing product."""

        if self.existing_product and self.existing_product_description is None:
            raise ValueError(
                "existing_product_description is required when existing_product is true."
            )

        if not self.existing_product and self.existing_product_description is not None:
            raise ValueError(
                "existing_product_description cannot be provided when existing_product is false."
            )

        return self


class ValidatedProductIdea(BuildWiseModel):
    """Normalized product idea accepted by deterministic intake validation.

    This is not the Discovery Agent's interpretation of the idea. It is the
    canonical, validated version of the user's submitted intake payload.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId

    title: IdeaTitle
    summary: MediumText
    original_idea: IdeaDescription
    normalized_problem_statement: MediumText

    target_users: list[ShortText] = Field(min_length=1)
    desired_outcomes: list[MediumText] = Field(min_length=1)

    requested_features: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    user_assumptions: list[MediumText] = Field(default_factory=list)

    target_platforms: list[TargetPlatform] = Field(default_factory=list)
    delivery_expectation: DeliveryExpectation = "not_decided"
    idea_maturity: IdeaMaturity

    preferred_timeline: ShortText | None = None
    estimated_budget: ShortText | None = None

    industry: ShortText | None = None
    target_market: ShortText | None = None
    geographic_scope: list[ShortText] = Field(default_factory=list)

    existing_product: bool = False
    existing_product_description: MediumText | None = None

    requests_ai_capabilities: bool | None = None
    handles_sensitive_data: bool | None = None
    regulated_domain: bool | None = None

    additional_context: LongText | None = None

    validation_confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    validation_notes: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    validated_at: datetime = Field(default_factory=utc_now)

    @field_validator("validated_at")
    @classmethod
    def normalize_validated_at(cls, value: datetime) -> datetime:
        """Require the validation timestamp to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("validated_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator(
        "target_users",
        "desired_outcomes",
        "requested_features",
        "constraints",
        "user_assumptions",
        "target_platforms",
        "geographic_scope",
        "validation_notes",
    )
    @classmethod
    def reject_duplicate_validated_values[T](cls, value: list[T]) -> list[T]:
        """Prevent duplicate normalized values in the canonical idea."""

        if len(value) != len(set(value)):
            raise ValueError("Validated list values must be unique.")

        return value

    @model_validator(mode="after")
    def validate_existing_product_details(self) -> ValidatedProductIdea:
        """Keep existing-product fields internally consistent."""

        if self.existing_product and self.existing_product_description is None:
            raise ValueError(
                "existing_product_description is required when existing_product is true."
            )

        if not self.existing_product and self.existing_product_description is not None:
            raise ValueError(
                "existing_product_description cannot be provided when existing_product is false."
            )

        return self


class ClarificationAnswer(BuildWiseModel):
    """A single normalized answer to a Discovery clarification question."""

    question_id: ClarificationQuestionId
    answer: ClarificationAnswerValue

    skipped: bool = False
    skip_reason: MediumText | None = None

    answered_at: datetime = Field(default_factory=utc_now)

    @field_validator("answered_at")
    @classmethod
    def normalize_answered_at(cls, value: datetime) -> datetime:
        """Require answer timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("answered_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("answer")
    @classmethod
    def normalize_answer(
        cls,
        value: ClarificationAnswerValue,
    ) -> ClarificationAnswerValue:
        """Trim textual answers and reject duplicate multi-value answers."""

        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None

        if isinstance(value, list):
            normalized_values = [item.strip() for item in value]

            if any(not item for item in normalized_values):
                raise ValueError("Clarification answer lists cannot contain empty values.")

            if len(normalized_values) != len(set(normalized_values)):
                raise ValueError("Clarification answer lists cannot contain duplicates.")

            return normalized_values

        return value

    @model_validator(mode="after")
    def validate_answer_or_skip(self) -> ClarificationAnswer:
        """Require either a meaningful answer or an explicit skip reason."""

        if self.skipped:
            if self.answer is not None:
                raise ValueError("A skipped clarification answer cannot contain an answer.")

            if self.skip_reason is None:
                raise ValueError("skip_reason is required when a clarification is skipped.")

            return self

        if self.skip_reason is not None:
            raise ValueError("skip_reason cannot be provided when skipped is false.")

        if self.answer is None:
            raise ValueError("answer is required when the clarification is not skipped.")

        if isinstance(self.answer, list) and not self.answer:
            raise ValueError("A clarification answer list cannot be empty.")

        return self


class ClarificationAnswerRequest(BuildWiseModel):
    """User request that resumes a paused session with clarification answers."""

    session_id: SessionId
    clarification_round: int = Field(ge=1)

    answers: list[ClarificationAnswer] = Field(min_length=1)

    submitted_at: datetime = Field(default_factory=utc_now)
    additional_context: LongText | None = None

    @field_validator("submitted_at")
    @classmethod
    def normalize_submitted_at(cls, value: datetime) -> datetime:
        """Require the clarification submission timestamp to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("submitted_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("answers")
    @classmethod
    def ensure_unique_question_answers(
        cls,
        value: list[ClarificationAnswer],
    ) -> list[ClarificationAnswer]:
        """Prevent multiple answers for the same clarification question."""

        question_ids = [answer.question_id for answer in value]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each clarification question may be answered only once per request.")

        return value


class ProductIdeaContext(BuildWiseModel):
    """Canonical intake context supplied to Discovery and downstream stages.

    This context preserves the validated original idea and all clarification
    rounds without embedding Discovery results or downstream specialist output.
    """

    session_id: SessionId
    validated_idea: ValidatedProductIdea

    clarification_answers: list[ClarificationAnswer] = Field(
        default_factory=list,
    )
    clarification_round: int = Field(default=0, ge=0)

    resolved_context: dict[Slug, MediumText] = Field(default_factory=dict)
    unresolved_context_keys: list[Slug] = Field(default_factory=list)

    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    context_version: int = Field(default=1, ge=1)
    assembled_at: datetime = Field(default_factory=utc_now)

    @field_validator("assembled_at")
    @classmethod
    def normalize_assembled_at(cls, value: datetime) -> datetime:
        """Require context assembly timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("assembled_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("clarification_answers")
    @classmethod
    def ensure_unique_context_answers(
        cls,
        value: list[ClarificationAnswer],
    ) -> list[ClarificationAnswer]:
        """Prevent duplicate clarification-question answers in context."""

        question_ids = [answer.question_id for answer in value]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "Product idea context cannot contain duplicate clarification-question answers."
            )

        return value

    @field_validator("unresolved_context_keys")
    @classmethod
    def ensure_unique_unresolved_keys(
        cls,
        value: list[Slug],
    ) -> list[Slug]:
        """Prevent duplicate unresolved context keys."""

        if len(value) != len(set(value)):
            raise ValueError("unresolved_context_keys must contain unique values.")

        return value

    @model_validator(mode="after")
    def validate_context_consistency(self) -> ProductIdeaContext:
        """Ensure the context belongs to one session and one clarification state."""

        if self.validated_idea.session_id != self.session_id:
            raise ValueError("validated_idea.session_id must match context session_id.")

        resolved_keys = set(self.resolved_context)
        unresolved_keys = set(self.unresolved_context_keys)
        overlapping_keys = resolved_keys.intersection(unresolved_keys)

        if overlapping_keys:
            formatted_keys = ", ".join(sorted(overlapping_keys))
            raise ValueError(
                f"Context keys cannot be both resolved and unresolved: {formatted_keys}."
            )

        if self.clarification_round == 0 and self.clarification_answers:
            raise ValueError(
                "clarification_round must be greater than zero when "
                "clarification answers are present."
            )

        if self.clarification_round > 0 and not self.clarification_answers:
            raise ValueError(
                "clarification answers are required when clarification_round is greater than zero."
            )

        return self
