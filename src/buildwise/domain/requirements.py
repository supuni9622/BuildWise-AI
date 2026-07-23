from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    MediumText,
    NormalizedScore,
    SessionId,
    ShortText,
    Slug,
    SourceMetadata,
    generate_uuid,
    utc_now,
)
from buildwise.domain.enums import (
    ConfidenceLevel,
    DependencyType,
    RequirementPriority,
    RequirementStatus,
)


AcceptanceCriterionType = Literal[
    "functional",
    "validation",
    "business_rule",
    "security",
    "performance",
    "accessibility",
    "data",
    "integration",
    "error_handling",
    "observability",
]

VerificationMethod = Literal[
    "automated_test",
    "manual_test",
    "inspection",
    "demonstration",
    "analysis",
    "monitoring",
]

BusinessRuleCategory = Literal[
    "eligibility",
    "validation",
    "authorization",
    "calculation",
    "workflow",
    "decision",
    "retention",
    "compliance",
    "pricing",
    "notification",
    "limit",
    "other",
]

BusinessRuleEnforcementPoint = Literal[
    "client",
    "api",
    "domain_service",
    "workflow",
    "database",
    "external_system",
    "multiple",
]

DataClassification = Literal[
    "public",
    "internal",
    "confidential",
    "restricted",
    "personal",
    "sensitive_personal",
    "regulated",
    "unknown",
]

DataOperation = Literal[
    "create",
    "read",
    "update",
    "delete",
    "search",
    "export",
    "import",
    "archive",
    "restore",
    "process",
]

DataRetentionType = Literal[
    "session",
    "temporary",
    "fixed_period",
    "indefinite",
    "user_controlled",
    "legal_requirement",
    "not_decided",
]

EdgeCaseCategory = Literal[
    "empty_input",
    "invalid_input",
    "duplicate_input",
    "boundary_value",
    "concurrency",
    "timeout",
    "partial_failure",
    "dependency_failure",
    "authorization",
    "data_consistency",
    "state_transition",
    "rate_limit",
    "large_payload",
    "network",
    "user_abandonment",
    "other",
]

EdgeCaseExpectedBehavior = Literal[
    "reject",
    "retry",
    "fallback",
    "degrade_gracefully",
    "pause",
    "request_user_action",
    "continue_with_warning",
    "rollback",
    "queue",
    "ignore",
]

FunctionalRequirementCategory = Literal[
    "intake",
    "discovery",
    "clarification",
    "product_definition",
    "requirements",
    "specialist_routing",
    "architecture",
    "ai",
    "security",
    "qa",
    "market",
    "review",
    "blueprint",
    "session",
    "persistence",
    "notification",
    "administration",
    "reporting",
    "integration",
    "other",
]


def _ensure_unique_values[T](
    value: list[T],
    *,
    field_name: str,
) -> list[T]:
    """Return a list after verifying that it contains no duplicates."""

    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must contain unique values.")

    return value


def _normalize_timezone_aware_datetime(
    value: datetime | None,
    *,
    field_name: str,
) -> datetime | None:
    """Normalize a timezone-aware datetime to UTC."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


class AcceptanceCriterion(BuildWiseModel):
    """A verifiable condition that determines whether a requirement is met.

    Acceptance criteria are written independently from implementation details.
    They describe observable behavior that a reviewer, tester, or automated
    check can verify.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText

    criterion_type: AcceptanceCriterionType = "functional"
    verification_method: VerificationMethod = "automated_test"

    given: MediumText | None = None
    when: MediumText | None = None
    then: MediumText | None = None

    measurable: bool = True
    target: ShortText | None = None

    automated: bool = True
    blocking: bool = True

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate acceptance-criterion source references."""

        return _ensure_unique_values(
            value,
            field_name="source_reference_ids",
        )

    @model_validator(mode="after")
    def validate_acceptance_criterion(self) -> AcceptanceCriterion:
        """Validate behavioral form and verification metadata."""

        scenario_values = (
            self.given,
            self.when,
            self.then,
        )
        populated_scenario_values = [
            value for value in scenario_values if value is not None
        ]

        if populated_scenario_values and len(populated_scenario_values) != 3:
            raise ValueError(
                "Behavioral acceptance criteria must provide given, when, "
                "and then together."
            )

        if not self.description and not populated_scenario_values:
            raise ValueError(
                "An acceptance criterion requires either a description or "
                "a complete given/when/then scenario."
            )

        if self.measurable and self.criterion_type in {
            "performance",
            "accessibility",
        }:
            if self.target is None:
                raise ValueError(
                    "Performance and accessibility criteria require a target "
                    "when measurable is true."
                )

        if not self.measurable and self.target is not None:
            raise ValueError(
                "target cannot be provided when measurable is false."
            )

        if self.automated and self.verification_method not in {
            "automated_test",
            "monitoring",
        }:
            raise ValueError(
                "Automated acceptance criteria must use automated_test or "
                "monitoring as the verification method."
            )

        if (
            not self.automated
            and self.verification_method == "automated_test"
        ):
            raise ValueError(
                "A non-automated acceptance criterion cannot use "
                "automated_test as its verification method."
            )

        return self


class BusinessRule(BuildWiseModel):
    """A deterministic domain rule that constrains product behavior."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    category: BusinessRuleCategory
    condition: MediumText
    outcome: MediumText

    priority: RequirementPriority = RequirementPriority.MUST_HAVE
    status: RequirementStatus = RequirementStatus.PROPOSED

    enforcement_point: BusinessRuleEnforcementPoint = "domain_service"
    deterministic: bool = True

    exception_conditions: list[MediumText] = Field(default_factory=list)
    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    dependent_rule_ids: list[ArtifactId] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)
    rationale: MediumText

    @field_validator(
        "related_feature_ids",
        "dependent_rule_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate business-rule references."""

        return _ensure_unique_values(
            value,
            field_name="Business-rule identifier references",
        )

    @field_validator("exception_conditions")
    @classmethod
    def ensure_unique_exception_conditions(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate rule exceptions."""

        return _ensure_unique_values(
            value,
            field_name="exception_conditions",
        )

    @model_validator(mode="after")
    def validate_business_rule(self) -> BusinessRule:
        """Validate business-rule dependency and execution behavior."""

        if self.id in self.dependent_rule_ids:
            raise ValueError("A business rule cannot depend on itself.")

        if (
            not self.deterministic
            and self.enforcement_point in {"client", "database"}
        ):
            raise ValueError(
                "Non-deterministic business rules cannot be enforced only "
                "at the client or database layer."
            )

        return self


class DataRequirement(BuildWiseModel):
    """A requirement governing data ownership, usage, quality, and lifecycle."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    description: MediumText

    entity_name: ShortText
    data_classification: DataClassification

    operations: list[DataOperation] = Field(min_length=1)
    required_fields: list[Slug] = Field(default_factory=list)
    optional_fields: list[Slug] = Field(default_factory=list)

    owner: ShortText | None = None
    system_of_record: ShortText | None = None

    validation_rules: list[MediumText] = Field(default_factory=list)
    quality_rules: list[MediumText] = Field(default_factory=list)

    retention_type: DataRetentionType = "not_decided"
    retention_period: ShortText | None = None
    deletion_requirement: MediumText | None = None

    encrypted_at_rest: bool | None = None
    encrypted_in_transit: bool | None = None
    audit_required: bool = False

    contains_personal_data: bool = False
    contains_sensitive_data: bool = False
    subject_to_regulation: bool = False

    regulation_names: list[ShortText] = Field(default_factory=list)
    residency_constraints: list[MediumText] = Field(default_factory=list)

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    priority: RequirementPriority = RequirementPriority.MUST_HAVE
    status: RequirementStatus = RequirementStatus.PROPOSED

    @field_validator(
        "operations",
        "required_fields",
        "optional_fields",
        "regulation_names",
        "residency_constraints",
        "validation_rules",
        "quality_rules",
    )
    @classmethod
    def ensure_unique_data_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate values in data requirement collections."""

        return _ensure_unique_values(
            value,
            field_name="Data requirement collections",
        )

    @field_validator(
        "related_feature_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate data-requirement references."""

        return _ensure_unique_values(
            value,
            field_name="Data requirement identifier references",
        )

    @model_validator(mode="after")
    def validate_data_requirement(self) -> DataRequirement:
        """Validate data classification, retention, and protection rules."""

        overlapping_fields = set(self.required_fields).intersection(
            self.optional_fields
        )

        if overlapping_fields:
            formatted_fields = ", ".join(sorted(overlapping_fields))
            raise ValueError(
                "Data fields cannot be both required and optional: "
                f"{formatted_fields}."
            )

        if (
            self.retention_type
            in {
                "fixed_period",
                "legal_requirement",
            }
            and self.retention_period is None
        ):
            raise ValueError(
                "retention_period is required for fixed-period and "
                "legal-requirement retention."
            )

        if (
            self.retention_type
            not in {
                "fixed_period",
                "legal_requirement",
            }
            and self.retention_period is not None
        ):
            raise ValueError(
                "retention_period may only be provided for fixed-period or "
                "legal-requirement retention."
            )

        if self.contains_sensitive_data and not self.contains_personal_data:
            if self.data_classification not in {
                "confidential",
                "restricted",
                "regulated",
            }:
                raise ValueError(
                    "Sensitive non-personal data must be classified as "
                    "confidential, restricted, or regulated."
                )

        if self.contains_personal_data and self.data_classification == "public":
            raise ValueError(
                "Personal data cannot use the public data classification."
            )

        if (
            self.contains_sensitive_data
            and self.data_classification
            not in {
                "sensitive_personal",
                "restricted",
                "regulated",
            }
        ):
            raise ValueError(
                "Sensitive data must use sensitive_personal, restricted, or "
                "regulated classification."
            )

        if self.subject_to_regulation and not self.regulation_names:
            raise ValueError(
                "regulation_names are required when subject_to_regulation "
                "is true."
            )

        if not self.subject_to_regulation and self.regulation_names:
            raise ValueError(
                "regulation_names cannot be provided when "
                "subject_to_regulation is false."
            )

        if self.contains_sensitive_data:
            if self.encrypted_at_rest is not True:
                raise ValueError(
                    "Sensitive data requirements must explicitly require "
                    "encryption at rest."
                )

            if self.encrypted_in_transit is not True:
                raise ValueError(
                    "Sensitive data requirements must explicitly require "
                    "encryption in transit."
                )

        if "delete" in self.operations and self.deletion_requirement is None:
            raise ValueError(
                "deletion_requirement is required when delete is an "
                "allowed operation."
            )

        return self


class EdgeCase(BuildWiseModel):
    """An exceptional or boundary scenario a requirement must handle."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: EdgeCaseCategory

    trigger: MediumText
    expected_behavior: EdgeCaseExpectedBehavior
    expected_result: MediumText

    user_message: MediumText | None = None
    recovery_action: MediumText | None = None

    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE
    blocking: bool = False

    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)
    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "related_requirement_ids",
        "related_feature_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate edge-case references."""

        return _ensure_unique_values(
            value,
            field_name="Edge-case identifier references",
        )

    @model_validator(mode="after")
    def validate_edge_case(self) -> EdgeCase:
        """Validate user communication and recovery behavior."""

        user_action_behaviors = {
            "request_user_action",
            "continue_with_warning",
        }

        recovery_behaviors = {
            "retry",
            "fallback",
            "rollback",
            "queue",
            "request_user_action",
        }

        if (
            self.expected_behavior in user_action_behaviors
            and self.user_message is None
        ):
            raise ValueError(
                "user_message is required when the expected behavior "
                "communicates with the user."
            )

        if (
            self.expected_behavior in recovery_behaviors
            and self.recovery_action is None
        ):
            raise ValueError(
                "recovery_action is required for retry, fallback, rollback, "
                "queue, and user-action behaviors."
            )

        if self.blocking and self.expected_behavior == "ignore":
            raise ValueError(
                "A blocking edge case cannot use ignore as its expected "
                "behavior."
            )

        return self


class FunctionalRequirement(BuildWiseModel):
    """A testable capability the product must provide.

    Functional requirements describe observable product behavior. They trace
    back to product features and forward to acceptance criteria, business
    rules, data requirements, integrations, user stories, and test coverage.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    title: ShortText
    description: MediumText

    category: FunctionalRequirementCategory
    priority: RequirementPriority
    status: RequirementStatus = RequirementStatus.PROPOSED

    actor: ShortText
    trigger: MediumText
    preconditions: list[MediumText] = Field(default_factory=list)

    main_flow: list[MediumText] = Field(min_length=1)
    alternative_flows: list[MediumText] = Field(default_factory=list)
    postconditions: list[MediumText] = Field(min_length=1)

    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)

    feature_ids: list[ArtifactId] = Field(min_length=1)
    persona_ids: list[ArtifactId] = Field(min_length=1)

    business_rule_ids: list[ArtifactId] = Field(default_factory=list)
    data_requirement_ids: list[ArtifactId] = Field(default_factory=list)
    integration_requirement_ids: list[ArtifactId] = Field(default_factory=list)
    non_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    edge_case_ids: list[ArtifactId] = Field(default_factory=list)

    dependency_ids: list[ArtifactId] = Field(default_factory=list)
    dependency_type: DependencyType | None = None

    assumptions: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    rationale: MediumText
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_requirement_timestamp(
        cls,
        value: datetime,
        info: object,
    ) -> datetime:
        """Require functional-requirement timestamps to be timezone-aware."""

        field_name = getattr(info, "field_name", "timestamp")

        normalized = _normalize_timezone_aware_datetime(
            value,
            field_name=field_name,
        )

        if normalized is None:
            raise ValueError(f"{field_name} cannot be null.")

        return normalized

    @field_validator(
        "preconditions",
        "main_flow",
        "alternative_flows",
        "postconditions",
        "assumptions",
        "exclusions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate functional-requirement statements."""

        return _ensure_unique_values(
            value,
            field_name="Functional requirement text collections",
        )

    @field_validator(
        "feature_ids",
        "persona_ids",
        "business_rule_ids",
        "data_requirement_ids",
        "integration_requirement_ids",
        "non_functional_requirement_ids",
        "edge_case_ids",
        "dependency_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate functional-requirement references."""

        return _ensure_unique_values(
            value,
            field_name="Functional requirement identifier references",
        )

    @field_validator("acceptance_criteria")
    @classmethod
    def ensure_unique_acceptance_criteria(
        cls,
        value: list[AcceptanceCriterion],
    ) -> list[AcceptanceCriterion]:
        """Prevent duplicate acceptance criteria and titles."""

        criterion_ids = [criterion.id for criterion in value]
        criterion_titles = [
            criterion.title.casefold() for criterion in value
        ]

        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError(
                "Acceptance criterion IDs must be unique within a "
                "functional requirement."
            )

        if len(criterion_titles) != len(set(criterion_titles)):
            raise ValueError(
                "Acceptance criterion titles must be unique within a "
                "functional requirement."
            )

        return value

    @model_validator(mode="after")
    def validate_functional_requirement(self) -> FunctionalRequirement:
        """Validate dependency, lifecycle, and acceptance behavior."""

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at cannot be earlier than created_at."
            )

        if self.id in self.dependency_ids:
            raise ValueError(
                "A functional requirement cannot depend on itself."
            )

        if self.dependency_ids and self.dependency_type is None:
            raise ValueError(
                "dependency_type is required when dependency_ids are "
                "provided."
            )

        if not self.dependency_ids and self.dependency_type is not None:
            raise ValueError(
                "dependency_type cannot be provided without dependency_ids."
            )

        blocking_criteria = [
            criterion
            for criterion in self.acceptance_criteria
            if criterion.blocking
        ]

        if (
            self.priority is RequirementPriority.MUST_HAVE
            and not blocking_criteria
        ):
            raise ValueError(
                "A must-have functional requirement requires at least one "
                "blocking acceptance criterion."
            )

        return self

class IntegrationRequirement(BuildWiseModel):
    """A requirement defining interaction with an external or internal system."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    system_name: ShortText
    integration_type: Literal[
        "rest_api",
        "graphql",
        "grpc",
        "webhook",
        "message_queue",
        "event_stream",
        "database",
        "file_transfer",
        "email",
        "identity_provider",
        "payment_provider",
        "llm_provider",
        "mcp_server",
        "other",
    ]

    direction: Literal[
        "inbound",
        "outbound",
        "bidirectional",
    ]

    purpose: MediumText
    data_exchanged: list[MediumText] = Field(min_length=1)

    authentication_method: Literal[
        "none",
        "api_key",
        "basic_auth",
        "oauth2",
        "jwt",
        "mutual_tls",
        "signed_request",
        "service_account",
        "managed_identity",
        "not_decided",
    ] = "not_decided"

    synchronous: bool = True
    real_time_required: bool = False

    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    retry_required: bool = True
    maximum_retry_attempts: int | None = Field(default=3, ge=1, le=10)

    idempotency_required: bool = False
    rate_limit_expected: bool = False
    rate_limit_description: MediumText | None = None

    fallback_behavior: MediumText | None = None
    failure_behavior: MediumText

    data_mapping_rules: list[MediumText] = Field(default_factory=list)
    validation_rules: list[MediumText] = Field(default_factory=list)

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    related_data_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    dependency_ids: list[ArtifactId] = Field(default_factory=list)

    priority: RequirementPriority = RequirementPriority.MUST_HAVE
    status: RequirementStatus = RequirementStatus.PROPOSED

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)
    rationale: MediumText

    @field_validator(
        "data_exchanged",
        "data_mapping_rules",
        "validation_rules",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate integration descriptions and rules."""

        return _ensure_unique_values(
            value,
            field_name="Integration requirement text collections",
        )

    @field_validator(
        "related_feature_ids",
        "related_data_requirement_ids",
        "dependency_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate integration references."""

        return _ensure_unique_values(
            value,
            field_name="Integration requirement identifier references",
        )

    @model_validator(mode="after")
    def validate_integration_requirement(
        self,
    ) -> IntegrationRequirement:
        """Validate integration timing, retries, and dependency behavior."""

        if self.id in self.dependency_ids:
            raise ValueError(
                "An integration requirement cannot depend on itself."
            )

        if self.synchronous and self.timeout_seconds is None:
            raise ValueError(
                "Synchronous integrations require timeout_seconds."
            )

        if not self.synchronous and self.timeout_seconds is not None:
            raise ValueError(
                "Asynchronous integrations cannot define synchronous "
                "timeout_seconds."
            )

        if self.retry_required and self.maximum_retry_attempts is None:
            raise ValueError(
                "maximum_retry_attempts is required when retry_required "
                "is true."
            )

        if (
            not self.retry_required
            and self.maximum_retry_attempts is not None
        ):
            raise ValueError(
                "maximum_retry_attempts cannot be provided when "
                "retry_required is false."
            )

        if self.rate_limit_expected and self.rate_limit_description is None:
            raise ValueError(
                "rate_limit_description is required when a rate limit "
                "is expected."
            )

        if (
            not self.rate_limit_expected
            and self.rate_limit_description is not None
        ):
            raise ValueError(
                "rate_limit_description cannot be provided when "
                "rate_limit_expected is false."
            )

        if self.real_time_required and not self.synchronous:
            if self.integration_type not in {
                "webhook",
                "message_queue",
                "event_stream",
            }:
                raise ValueError(
                    "Asynchronous real-time integrations must use webhook, "
                    "message_queue, or event_stream."
                )

        if (
            self.priority is RequirementPriority.MUST_HAVE
            and self.fallback_behavior is None
        ):
            raise ValueError(
                "A must-have integration requires documented "
                "fallback_behavior."
            )

        return self


class NonFunctionalRequirement(BuildWiseModel):
    """A measurable quality attribute or operational constraint."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    title: ShortText
    description: MediumText

    category: Literal[
        "performance",
        "scalability",
        "availability",
        "reliability",
        "security",
        "privacy",
        "accessibility",
        "usability",
        "maintainability",
        "observability",
        "portability",
        "compatibility",
        "recoverability",
        "data_integrity",
        "cost_efficiency",
        "compliance",
        "localization",
        "supportability",
        "other",
    ]

    priority: RequirementPriority
    status: RequirementStatus = RequirementStatus.PROPOSED

    quality_attribute: ShortText
    metric: ShortText
    target: ShortText

    measurement_method: MediumText
    measurement_environment: MediumText | None = None

    scope: MediumText
    rationale: MediumText

    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    related_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    @field_validator(
        "related_feature_ids",
        "related_functional_requirement_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate non-functional requirement references."""

        return _ensure_unique_values(
            value,
            field_name=(
                "Non-functional requirement identifier references"
            ),
        )

    @field_validator(
        "assumptions",
        "constraints",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate non-functional requirement statements."""

        return _ensure_unique_values(
            value,
            field_name="Non-functional requirement text collections",
        )

    @field_validator("acceptance_criteria")
    @classmethod
    def ensure_unique_acceptance_criteria(
        cls,
        value: list[AcceptanceCriterion],
    ) -> list[AcceptanceCriterion]:
        """Prevent duplicate acceptance criteria."""

        criterion_ids = [criterion.id for criterion in value]
        criterion_titles = [
            criterion.title.casefold() for criterion in value
        ]

        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError(
                "Acceptance criterion IDs must be unique within a "
                "non-functional requirement."
            )

        if len(criterion_titles) != len(set(criterion_titles)):
            raise ValueError(
                "Acceptance criterion titles must be unique within a "
                "non-functional requirement."
            )

        return value

    @model_validator(mode="after")
    def validate_non_functional_requirement(
        self,
    ) -> NonFunctionalRequirement:
        """Ensure quality requirements are measurable and testable."""

        if not self.metric.strip():
            raise ValueError(
                "A non-functional requirement requires a metric."
            )

        if not self.target.strip():
            raise ValueError(
                "A non-functional requirement requires a target."
            )

        measurable_criteria = [
            criterion
            for criterion in self.acceptance_criteria
            if criterion.measurable
        ]

        if not measurable_criteria:
            raise ValueError(
                "A non-functional requirement requires at least one "
                "measurable acceptance criterion."
            )

        if (
            self.priority is RequirementPriority.MUST_HAVE
            and not any(
                criterion.blocking
                for criterion in self.acceptance_criteria
            )
        ):
            raise ValueError(
                "A must-have non-functional requirement requires at least "
                "one blocking acceptance criterion."
            )

        return self


class UserJourneyStep(BuildWiseModel):
    """A single observable step within a user journey."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    sequence: int = Field(ge=1)
    title: ShortText
    actor_action: MediumText
    system_response: MediumText

    touchpoint: ShortText | None = None
    user_emotion: Literal[
        "positive",
        "neutral",
        "confused",
        "frustrated",
        "concerned",
        "delighted",
        "unknown",
    ] = "unknown"

    pain_point: MediumText | None = None
    opportunity: MediumText | None = None

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "related_feature_ids",
        "related_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate journey-step references."""

        return _ensure_unique_values(
            value,
            field_name="User journey step references",
        )


class UserJourney(BuildWiseModel):
    """An end-to-end user interaction across multiple product capabilities."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    description: MediumText

    persona_id: ArtifactId
    goal_id: ArtifactId | None = None

    trigger: MediumText
    expected_outcome: MediumText

    preconditions: list[MediumText] = Field(default_factory=list)
    steps: list[UserJourneyStep] = Field(min_length=1)
    postconditions: list[MediumText] = Field(min_length=1)

    alternative_paths: list[MediumText] = Field(default_factory=list)
    failure_paths: list[MediumText] = Field(default_factory=list)

    related_feature_ids: list[ArtifactId] = Field(min_length=1)
    related_requirement_ids: list[ArtifactId] = Field(min_length=1)

    success_metric: MediumText
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "preconditions",
        "postconditions",
        "alternative_paths",
        "failure_paths",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate journey statements."""

        return _ensure_unique_values(
            value,
            field_name="User journey text collections",
        )

    @field_validator(
        "related_feature_ids",
        "related_requirement_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate user journey references."""

        return _ensure_unique_values(
            value,
            field_name="User journey identifier references",
        )

    @field_validator("steps")
    @classmethod
    def validate_steps(
        cls,
        value: list[UserJourneyStep],
    ) -> list[UserJourneyStep]:
        """Require unique, contiguous journey-step ordering."""

        step_ids = [step.id for step in value]
        sequences = [step.sequence for step in value]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError("User journey step IDs must be unique.")

        if len(sequences) != len(set(sequences)):
            raise ValueError(
                "User journey step sequence numbers must be unique."
            )

        expected_sequences = list(range(1, len(value) + 1))

        if sorted(sequences) != expected_sequences:
            raise ValueError(
                "User journey step sequences must be contiguous and start "
                "at one."
            )

        return sorted(value, key=lambda step: step.sequence)


class UserStory(BuildWiseModel):
    """A persona-centered requirement expressed as user value."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    title: ShortText

    persona_id: ArtifactId
    actor: ShortText

    capability: MediumText
    benefit: MediumText

    narrative: MediumText

    priority: RequirementPriority
    status: RequirementStatus = RequirementStatus.PROPOSED

    feature_ids: list[ArtifactId] = Field(min_length=1)
    functional_requirement_ids: list[ArtifactId] = Field(min_length=1)
    non_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    edge_case_ids: list[ArtifactId] = Field(default_factory=list)

    dependencies: list[ArtifactId] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "feature_ids",
        "functional_requirement_ids",
        "non_functional_requirement_ids",
        "edge_case_ids",
        "dependencies",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate user-story references."""

        return _ensure_unique_values(
            value,
            field_name="User story identifier references",
        )

    @field_validator("assumptions")
    @classmethod
    def ensure_unique_assumptions(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate user-story assumptions."""

        return _ensure_unique_values(
            value,
            field_name="User story assumptions",
        )

    @field_validator("acceptance_criteria")
    @classmethod
    def ensure_unique_acceptance_criteria(
        cls,
        value: list[AcceptanceCriterion],
    ) -> list[AcceptanceCriterion]:
        """Prevent duplicate user-story acceptance criteria."""

        criterion_ids = [criterion.id for criterion in value]
        criterion_titles = [
            criterion.title.casefold() for criterion in value
        ]

        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError(
                "User story acceptance criterion IDs must be unique."
            )

        if len(criterion_titles) != len(set(criterion_titles)):
            raise ValueError(
                "User story acceptance criterion titles must be unique."
            )

        return value

    @model_validator(mode="after")
    def validate_user_story(self) -> UserStory:
        """Validate narrative consistency and dependencies."""

        expected_narrative_parts = (
            self.actor.casefold(),
            self.capability.casefold(),
            self.benefit.casefold(),
        )

        normalized_narrative = self.narrative.casefold()

        if not all(
            part in normalized_narrative
            for part in expected_narrative_parts
        ):
            raise ValueError(
                "narrative must contain the actor, capability, and benefit."
            )

        if self.id in self.dependencies:
            raise ValueError("A user story cannot depend on itself.")

        if (
            self.priority is RequirementPriority.MUST_HAVE
            and not any(
                criterion.blocking
                for criterion in self.acceptance_criteria
            )
        ):
            raise ValueError(
                "A must-have user story requires at least one blocking "
                "acceptance criterion."
            )

        return self


class RequirementsSpecification(BuildWiseModel):
    """Canonical structured output produced by the Business Analyst.

    The specification converts ProductDefinition artifacts into testable,
    traceable requirements. It preserves links from personas and features to
    functional requirements, quality requirements, data requirements,
    integrations, user journeys, user stories, rules, and edge cases.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId
    product_definition_id: ArtifactId

    title: ShortText
    summary: MediumText
    scope: MediumText

    functional_requirements: list[FunctionalRequirement] = Field(
        min_length=1,
    )
    non_functional_requirements: list[NonFunctionalRequirement] = Field(
        min_length=1,
    )

    business_rules: list[BusinessRule] = Field(default_factory=list)
    data_requirements: list[DataRequirement] = Field(default_factory=list)
    integration_requirements: list[IntegrationRequirement] = Field(
        default_factory=list,
    )
    edge_cases: list[EdgeCase] = Field(default_factory=list)

    user_journeys: list[UserJourney] = Field(min_length=1)
    user_stories: list[UserStory] = Field(min_length=1)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    open_questions: list[MediumText] = Field(default_factory=list)

    decision: Literal[
        "approved",
        "approved_with_assumptions",
        "requires_clarification",
        "cannot_proceed",
    ]
    decision_rationale: MediumText

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    generated_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at", "updated_at")
    @classmethod
    def normalize_specification_timestamps(
        cls,
        value: datetime,
        info: object,
    ) -> datetime:
        """Require specification timestamps to be timezone-aware."""

        field_name = getattr(info, "field_name", "timestamp")

        normalized = _normalize_timezone_aware_datetime(
            value,
            field_name=field_name,
        )

        if normalized is None:
            raise ValueError(f"{field_name} cannot be null.")

        return normalized

    @field_validator(
        "functional_requirements",
        "non_functional_requirements",
        "business_rules",
        "data_requirements",
        "integration_requirements",
        "edge_cases",
        "user_journeys",
        "user_stories",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate artifact identifiers within collections."""

        artifact_ids = [getattr(item, "id") for item in value]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(
                "RequirementsSpecification artifact IDs must be unique "
                "within each collection."
            )

        return value

    @field_validator(
        "assumptions",
        "constraints",
        "exclusions",
        "open_questions",
        "limitations",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate specification statements."""

        return _ensure_unique_values(
            value,
            field_name="Requirements specification text collections",
        )

    @model_validator(mode="after")
    def validate_requirements_specification(
        self,
    ) -> RequirementsSpecification:
        """Validate traceability and cross-artifact references."""

        if self.updated_at < self.generated_at:
            raise ValueError(
                "updated_at cannot be earlier than generated_at."
            )

        functional_ids = {
            requirement.id
            for requirement in self.functional_requirements
        }
        non_functional_ids = {
            requirement.id
            for requirement in self.non_functional_requirements
        }
        business_rule_ids = {
            rule.id for rule in self.business_rules
        }
        data_requirement_ids = {
            requirement.id
            for requirement in self.data_requirements
        }
        integration_requirement_ids = {
            requirement.id
            for requirement in self.integration_requirements
        }
        edge_case_ids = {
            edge_case.id for edge_case in self.edge_cases
        }
        user_story_ids = {
            story.id for story in self.user_stories
        }

        requirement_keys = [
            requirement.key
            for requirement in self.functional_requirements
        ]
        requirement_keys.extend(
            requirement.key
            for requirement in self.non_functional_requirements
        )
        requirement_keys.extend(
            rule.key for rule in self.business_rules
        )
        requirement_keys.extend(
            requirement.key
            for requirement in self.integration_requirements
        )
        requirement_keys.extend(
            story.key for story in self.user_stories
        )

        if len(requirement_keys) != len(set(requirement_keys)):
            raise ValueError(
                "Requirement and user-story keys must be globally unique "
                "within the specification."
            )

        for requirement in self.functional_requirements:
            missing_business_rules = set(
                requirement.business_rule_ids
            ).difference(business_rule_ids)

            if missing_business_rules:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="business rules",
                    identifiers=missing_business_rules,
                )

            missing_data_requirements = set(
                requirement.data_requirement_ids
            ).difference(data_requirement_ids)

            if missing_data_requirements:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="data requirements",
                    identifiers=missing_data_requirements,
                )

            missing_integrations = set(
                requirement.integration_requirement_ids
            ).difference(integration_requirement_ids)

            if missing_integrations:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="integration requirements",
                    identifiers=missing_integrations,
                )

            missing_non_functional = set(
                requirement.non_functional_requirement_ids
            ).difference(non_functional_ids)

            if missing_non_functional:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="non-functional requirements",
                    identifiers=missing_non_functional,
                )

            missing_edge_cases = set(
                requirement.edge_case_ids
            ).difference(edge_case_ids)

            if missing_edge_cases:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="edge cases",
                    identifiers=missing_edge_cases,
                )

            missing_dependencies = set(
                requirement.dependency_ids
            ).difference(functional_ids)

            if missing_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Functional requirement '{requirement.title}'",
                    reference_type="functional dependencies",
                    identifiers=missing_dependencies,
                )

        for requirement in self.non_functional_requirements:
            missing_functional_requirements = set(
                requirement.related_functional_requirement_ids
            ).difference(functional_ids)

            if missing_functional_requirements:
                self._raise_missing_reference_error(
                    owner=(
                        "Non-functional requirement "
                        f"'{requirement.title}'"
                    ),
                    reference_type="functional requirements",
                    identifiers=missing_functional_requirements,
                )

        for integration in self.integration_requirements:
            missing_data_requirements = set(
                integration.related_data_requirement_ids
            ).difference(data_requirement_ids)

            if missing_data_requirements:
                self._raise_missing_reference_error(
                    owner=f"Integration '{integration.name}'",
                    reference_type="data requirements",
                    identifiers=missing_data_requirements,
                )

            missing_dependencies = set(
                integration.dependency_ids
            ).difference(integration_requirement_ids)

            if missing_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Integration '{integration.name}'",
                    reference_type="integration dependencies",
                    identifiers=missing_dependencies,
                )

        for business_rule in self.business_rules:
            missing_rule_dependencies = set(
                business_rule.dependent_rule_ids
            ).difference(business_rule_ids)

            if missing_rule_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Business rule '{business_rule.name}'",
                    reference_type="business-rule dependencies",
                    identifiers=missing_rule_dependencies,
                )

        for edge_case in self.edge_cases:
            valid_requirement_ids = functional_ids.union(
                non_functional_ids
            )

            missing_requirements = set(
                edge_case.related_requirement_ids
            ).difference(valid_requirement_ids)

            if missing_requirements:
                self._raise_missing_reference_error(
                    owner=f"Edge case '{edge_case.title}'",
                    reference_type="requirements",
                    identifiers=missing_requirements,
                )

        for journey in self.user_journeys:
            missing_requirements = set(
                journey.related_requirement_ids
            ).difference(functional_ids)

            if missing_requirements:
                self._raise_missing_reference_error(
                    owner=f"User journey '{journey.name}'",
                    reference_type="functional requirements",
                    identifiers=missing_requirements,
                )

            for step in journey.steps:
                missing_step_requirements = set(
                    step.related_requirement_ids
                ).difference(functional_ids)

                if missing_step_requirements:
                    self._raise_missing_reference_error(
                        owner=(
                            f"User journey step '{step.title}' "
                            f"in journey '{journey.name}'"
                        ),
                        reference_type="functional requirements",
                        identifiers=missing_step_requirements,
                    )

        for story in self.user_stories:
            missing_functional_requirements = set(
                story.functional_requirement_ids
            ).difference(functional_ids)

            if missing_functional_requirements:
                self._raise_missing_reference_error(
                    owner=f"User story '{story.title}'",
                    reference_type="functional requirements",
                    identifiers=missing_functional_requirements,
                )

            missing_non_functional_requirements = set(
                story.non_functional_requirement_ids
            ).difference(non_functional_ids)

            if missing_non_functional_requirements:
                self._raise_missing_reference_error(
                    owner=f"User story '{story.title}'",
                    reference_type="non-functional requirements",
                    identifiers=missing_non_functional_requirements,
                )

            missing_edge_cases = set(
                story.edge_case_ids
            ).difference(edge_case_ids)

            if missing_edge_cases:
                self._raise_missing_reference_error(
                    owner=f"User story '{story.title}'",
                    reference_type="edge cases",
                    identifiers=missing_edge_cases,
                )

            missing_story_dependencies = set(
                story.dependencies
            ).difference(user_story_ids)

            if missing_story_dependencies:
                self._raise_missing_reference_error(
                    owner=f"User story '{story.title}'",
                    reference_type="user-story dependencies",
                    identifiers=missing_story_dependencies,
                )

        functional_requirements_with_story_coverage = {
            requirement_id
            for story in self.user_stories
            for requirement_id in story.functional_requirement_ids
        }

        must_have_functional_ids = {
            requirement.id
            for requirement in self.functional_requirements
            if requirement.priority is RequirementPriority.MUST_HAVE
        }

        uncovered_must_have_requirements = (
            must_have_functional_ids.difference(
                functional_requirements_with_story_coverage
            )
        )

        if uncovered_must_have_requirements:
            self._raise_missing_reference_error(
                owner="RequirementsSpecification",
                reference_type=(
                    "user-story coverage for must-have functional "
                    "requirements"
                ),
                identifiers=uncovered_must_have_requirements,
            )

        journey_requirement_coverage = {
            requirement_id
            for journey in self.user_journeys
            for requirement_id in journey.related_requirement_ids
        }

        if not must_have_functional_ids.intersection(
            journey_requirement_coverage
        ):
            raise ValueError(
                "At least one must-have functional requirement must be "
                "covered by a user journey."
            )

        if self.decision == "approved" and self.open_questions:
            raise ValueError(
                "An approved requirements specification cannot contain "
                "open questions."
            )

        if (
            self.decision == "approved_with_assumptions"
            and not self.assumptions
        ):
            raise ValueError(
                "approved_with_assumptions requires at least one "
                "assumption."
            )

        if (
            self.decision == "requires_clarification"
            and not self.open_questions
        ):
            raise ValueError(
                "requires_clarification requires at least one open "
                "question."
            )

        if self.decision == "cannot_proceed" and not self.limitations:
            raise ValueError(
                "cannot_proceed requires at least one documented "
                "limitation."
            )

        return self

    @staticmethod
    def _raise_missing_reference_error(
        *,
        owner: str,
        reference_type: str,
        identifiers: set[ArtifactId],
    ) -> None:
        """Raise a consistently formatted missing-reference error."""

        formatted_identifiers = ", ".join(
            sorted(str(identifier) for identifier in identifiers)
        )

        raise ValueError(
            f"{owner} references unknown {reference_type}: "
            f"{formatted_identifiers}."
        )

    @classmethod
    def validate_product_ownership(
        cls,
        *,
        requirements_specification: RequirementsSpecification,
        product_definition: object,
    ) -> None:
        """Validate ownership against a ProductDefinition instance.

        A local import is used to avoid introducing an unnecessary import
        cycle at module-import time.
        """

        from buildwise.domain.product import ProductDefinition

        if not isinstance(product_definition, ProductDefinition):
            raise TypeError(
                "product_definition must be a ProductDefinition instance."
            )

        if (
            requirements_specification.session_id
            != product_definition.session_id
        ):
            raise ValueError(
                "RequirementsSpecification and ProductDefinition session "
                "IDs must match."
            )

        if (
            requirements_specification.product_definition_id
            != product_definition.id
        ):
            raise ValueError(
                "RequirementsSpecification.product_definition_id must "
                "match ProductDefinition.id."
            )

        feature_ids = {
            feature.id for feature in product_definition.features
        }
        persona_ids = {
            persona.id for persona in product_definition.personas
        }
        goal_ids = {
            goal.id for goal in product_definition.goals
        }

        referenced_feature_ids: set[ArtifactId] = set()
        referenced_persona_ids: set[ArtifactId] = set()
        referenced_goal_ids: set[ArtifactId] = set()

        for requirement in (
            requirements_specification.functional_requirements
        ):
            referenced_feature_ids.update(requirement.feature_ids)
            referenced_persona_ids.update(requirement.persona_ids)

        for requirement in requirements_specification.data_requirements:
            referenced_feature_ids.update(
                requirement.related_feature_ids
            )

        for requirement in (
            requirements_specification.integration_requirements
        ):
            referenced_feature_ids.update(
                requirement.related_feature_ids
            )

        for requirement in (
            requirements_specification.non_functional_requirements
        ):
            referenced_feature_ids.update(
                requirement.related_feature_ids
            )

        for rule in requirements_specification.business_rules:
            referenced_feature_ids.update(rule.related_feature_ids)

        for edge_case in requirements_specification.edge_cases:
            referenced_feature_ids.update(edge_case.related_feature_ids)

        for journey in requirements_specification.user_journeys:
            referenced_feature_ids.update(journey.related_feature_ids)
            referenced_persona_ids.add(journey.persona_id)

            if journey.goal_id is not None:
                referenced_goal_ids.add(journey.goal_id)

            for step in journey.steps:
                referenced_feature_ids.update(
                    step.related_feature_ids
                )

        for story in requirements_specification.user_stories:
            referenced_feature_ids.update(story.feature_ids)
            referenced_persona_ids.add(story.persona_id)

        missing_features = referenced_feature_ids.difference(feature_ids)

        if missing_features:
            cls._raise_missing_reference_error(
                owner="RequirementsSpecification",
                reference_type="ProductDefinition features",
                identifiers=missing_features,
            )

        missing_personas = referenced_persona_ids.difference(persona_ids)

        if missing_personas:
            cls._raise_missing_reference_error(
                owner="RequirementsSpecification",
                reference_type="ProductDefinition personas",
                identifiers=missing_personas,
            )

        missing_goals = referenced_goal_ids.difference(goal_ids)

        if missing_goals:
            cls._raise_missing_reference_error(
                owner="RequirementsSpecification",
                reference_type="ProductDefinition goals",
                identifiers=missing_goals,
            )