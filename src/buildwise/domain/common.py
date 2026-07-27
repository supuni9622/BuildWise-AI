from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    field_validator,
    model_validator,
)

from buildwise.domain.enums import (
    ConfidenceLevel,
    CostCategory,
    CostFrequency,
    SourceReferenceType,
)

# =============================================================================
# Shared constrained scalar types
# =============================================================================

NonEmptyString = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

ShortText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
    ),
]

MediumText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2_000,
    ),
]

LongText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20_000,
    ),
]

Slug = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$",
        min_length=1,
        max_length=100,
    ),
]

CurrencyCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        pattern=r"^[A-Z]{3}$",
        min_length=3,
        max_length=3,
    ),
]

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]

Percentage = Annotated[float, Field(ge=0.0, le=100.0)]
NormalizedScore = Annotated[float, Field(ge=0.0, le=1.0)]

NonNegativeDecimal = Annotated[
    Decimal,
    Field(
        ge=Decimal("0"),
        max_digits=14,
        decimal_places=4,
    ),
]


# =============================================================================
# Canonical identifiers
# =============================================================================

SessionId = UUID
RequestId = UUID
ArtifactId = UUID
AgentExecutionId = UUID
TaskExecutionId = UUID
ReferenceId = UUID


def generate_uuid() -> UUID:
    """Generate a UUID for a new BuildWise domain entity."""

    return uuid4()


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(UTC)


# =============================================================================
# Base model configuration
# =============================================================================


class BuildWiseModel(BaseModel):
    """Base class for canonical BuildWise domain models.

    All Phase 1 domain contracts should inherit from this model so validation
    and serialization behavior remain consistent across agents, tasks, Crews,
    Flows, persistence boundaries, and API responses.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        use_enum_values=False,
    )

    def apply_updates(self, **updates: object) -> None:
        """Apply multiple field updates to this model atomically.

        ``validate_assignment=True`` re-validates the entire model on every
        single attribute write. A method that must change several
        interdependent fields together (for example a status field and the
        timestamp field its own validator requires) cannot set them one at a
        time: the first assignment would validate an intermediate state that
        is only self-consistent once every field in the group has its new
        value.

        This writes every update directly into the instance without
        triggering validation, then performs one real assignment to trigger
        exactly one validation pass against the fully-updated, self-consistent
        state.

        Do not use this for list/dict fields that declare their own
        ``field_validator`` (for example collections requiring uniqueness):
        bypassing assignment skips that field's own validator, and the
        triggered pass only re-runs model-level validators plus the
        field-level validator of whichever field happens to trigger it.
        Mutate those fields in place (``.append(...)``) as before, outside
        this method.
        """

        if not updates:
            return

        for name, value in updates.items():
            object.__setattr__(self, name, value)

        trigger_name = next(iter(updates))
        setattr(self, trigger_name, getattr(self, trigger_name))


class TimestampedModel(BuildWiseModel):
    """Base model for domain records that require lifecycle timestamps."""

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        """Reject naive timestamps and normalize valid timestamps to UTC."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> TimestampedModel:
        """Ensure the update time is not earlier than the creation time."""

        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at.")

        return self


# =============================================================================
# Source and provenance metadata
# =============================================================================


class MetadataEntry(BuildWiseModel):
    """One deterministic source-metadata key/value pair."""

    key: ShortText
    value: str | int | float | bool | None = None


class SourceMetadata(BuildWiseModel):
    """Reusable provenance metadata for facts, artifacts, and recommendations.

    This is intentionally smaller than the later SourceReference reporting
    model. It records where an individual domain value originated while the
    reporting model will represent formal citations in the final blueprint.
    """

    id: ReferenceId = Field(default_factory=generate_uuid)
    reference_type: SourceReferenceType
    source_key: ShortText
    title: ShortText | None = None
    description: MediumText | None = None
    # Keep the schema-visible type as ``str`` because OpenAI strict structured
    # outputs rejects Pydantic's ``format: "uri"`` JSON Schema annotation.
    # The validator below preserves the domain's HTTP(S)-URL validation.
    uri: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    retrieved_at: datetime | None = None
    metadata: list[MetadataEntry] = Field(default_factory=list)

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value: str | None) -> str | None:
        """Validate source URIs without emitting an unsupported schema format."""

        if value is None:
            return None
        return str(TypeAdapter(AnyHttpUrl).validate_python(value))

    @field_validator("retrieved_at")
    @classmethod
    def normalize_retrieved_at(cls, value: datetime | None) -> datetime | None:
        """Require source retrieval timestamps to include timezone data."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware.")

        return value.astimezone(UTC)


# =============================================================================
# Money and distributed cost estimation
# =============================================================================


class MoneyAmount(BuildWiseModel):
    """A non-negative monetary amount represented with decimal precision."""

    amount: NonNegativeDecimal
    currency: CurrencyCode = "USD"


class CostRange(BuildWiseModel):
    """Minimum, expected, and maximum values for an estimated cost."""

    minimum: MoneyAmount
    expected: MoneyAmount
    maximum: MoneyAmount

    @model_validator(mode="after")
    def validate_range(self) -> CostRange:
        """Ensure all amounts share a currency and form a valid range."""

        currencies = {
            self.minimum.currency,
            self.expected.currency,
            self.maximum.currency,
        }

        if len(currencies) != 1:
            raise ValueError("minimum, expected, and maximum must use the same currency.")

        if self.minimum.amount > self.expected.amount:
            raise ValueError("minimum amount cannot exceed expected amount.")

        if self.expected.amount > self.maximum.amount:
            raise ValueError("expected amount cannot exceed maximum amount.")

        return self


class CostEstimate(BuildWiseModel):
    """A cost estimate contributed by a BuildWise product area.

    Cost estimates remain distributed across Product, Architecture, AI,
    Security, QA, and GTM outputs. The later CostSummary model will aggregate
    these estimates without replacing their original ownership.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    category: CostCategory
    name: ShortText
    description: MediumText
    frequency: CostFrequency
    range: CostRange
    assumptions: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    source_reference_ids: list[ReferenceId] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# =============================================================================
# Token and execution measurements
# =============================================================================


class TokenCounts(BuildWiseModel):
    """Reusable token counts for a single model interaction."""

    input_tokens: NonNegativeInt = 0
    output_tokens: NonNegativeInt = 0
    cached_input_tokens: NonNegativeInt = 0
    reasoning_tokens: NonNegativeInt = 0
    total_tokens: NonNegativeInt = 0

    @model_validator(mode="after")
    def validate_total_tokens(self) -> TokenCounts:
        """Validate the provider-reported token total when one is supplied."""

        calculated_total = self.input_tokens + self.output_tokens

        if self.total_tokens == 0:
            self.total_tokens = calculated_total
            return self

        if self.total_tokens < calculated_total:
            raise ValueError("total_tokens cannot be lower than input_tokens plus output_tokens.")

        return self


class ExecutionMetrics(BuildWiseModel):
    """Reusable timing, retry, and usage metrics for one execution."""

    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: NonNegativeInt = 0
    retry_count: NonNegativeInt = 0
    token_counts: TokenCounts = Field(default_factory=TokenCounts)
    estimated_cost: MoneyAmount = Field(
        default_factory=lambda: MoneyAmount(
            amount=Decimal("0"),
            currency="USD",
        )
    )

    @field_validator("started_at", "completed_at")
    @classmethod
    def normalize_execution_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require execution timestamps to be timezone-aware."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Execution timestamps must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_execution_window(self) -> ExecutionMetrics:
        """Ensure completed executions do not finish before they start."""

        if self.completed_at is None:
            return self

        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be earlier than started_at.")

        return self


# =============================================================================
# General validation and limitation metadata
# =============================================================================


class ValidationIssue(BuildWiseModel):
    """A normalized validation issue produced by deterministic validation."""

    code: Slug
    message: MediumText
    field_path: ShortText | None = None
    recoverable: bool = True
    suggested_action: MediumText | None = None


class WarningMessage(BuildWiseModel):
    """A non-fatal warning retained in Flow state and final reporting."""

    code: Slug
    message: MediumText
    stage: ShortText | None = None
    source: ShortText | None = None


class Limitation(BuildWiseModel):
    """A known constraint or limitation attached to an output."""

    id: ArtifactId = Field(default_factory=generate_uuid)
    title: ShortText
    description: MediumText
    impact: MediumText
    mitigation: MediumText | None = None
    source_reference_ids: list[ReferenceId] = Field(default_factory=list)
