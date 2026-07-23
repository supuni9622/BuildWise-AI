from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    CostEstimate,
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
    RequirementPriority,
    RiskLikelihood,
    RiskSeverity,
)


class _HasArtifactId(Protocol):
    """Structural type for architecture artifacts identified by ArtifactId."""

    id: ArtifactId


ArchitectureStyle = Literal[
    "modular_monolith",
    "layered_monolith",
    "microservices",
    "service_oriented",
    "event_driven",
    "serverless",
    "client_server",
    "pipeline",
    "hybrid",
]

ArchitectureComponentType = Literal[
    "web_application",
    "mobile_application",
    "api_gateway",
    "backend_service",
    "workflow_orchestrator",
    "background_worker",
    "scheduler",
    "message_broker",
    "event_bus",
    "relational_database",
    "document_database",
    "vector_database",
    "cache",
    "object_storage",
    "search_engine",
    "identity_provider",
    "notification_service",
    "analytics_service",
    "observability_service",
    "external_service",
    "llm_gateway",
    "ai_service",
    "mcp_server",
    "other",
]

ComponentLayer = Literal[
    "client",
    "edge",
    "api",
    "application",
    "domain",
    "workflow",
    "ai",
    "integration",
    "data",
    "infrastructure",
    "observability",
    "external",
]

ComponentResponsibilityType = Literal[
    "presentation",
    "request_handling",
    "authentication",
    "authorization",
    "business_logic",
    "workflow_orchestration",
    "background_processing",
    "data_persistence",
    "data_retrieval",
    "caching",
    "search",
    "messaging",
    "file_storage",
    "ai_inference",
    "tool_execution",
    "integration",
    "monitoring",
    "notification",
    "other",
]

ConnectionType = Literal[
    "http",
    "https",
    "rest",
    "graphql",
    "grpc",
    "websocket",
    "server_sent_events",
    "message_queue",
    "event_stream",
    "database_connection",
    "cache_connection",
    "object_storage",
    "file_transfer",
    "mcp",
    "internal_call",
    "other",
]

CommunicationMode = Literal[
    "synchronous",
    "asynchronous",
    "streaming",
    "batch",
]

DataFlowDirection = Literal[
    "unidirectional",
    "bidirectional",
]

TrustBoundary = Literal[
    "same_process",
    "same_private_network",
    "cross_service",
    "public_network",
    "third_party",
]

TechnologyCategory = Literal[
    "programming_language",
    "frontend_framework",
    "backend_framework",
    "database",
    "cache",
    "message_broker",
    "workflow_engine",
    "cloud_provider",
    "container_runtime",
    "orchestration",
    "identity",
    "storage",
    "search",
    "observability",
    "ci_cd",
    "testing",
    "ai_framework",
    "ai_provider",
    "infrastructure_as_code",
    "other",
]

TechnologyDecisionStatus = Literal[
    "proposed",
    "selected",
    "approved",
    "rejected",
    "deferred",
]

DeploymentUnitType = Literal[
    "static_site",
    "web_application",
    "api_service",
    "worker",
    "scheduled_job",
    "database",
    "cache",
    "message_broker",
    "object_storage",
    "managed_service",
    "serverless_function",
    "container_service",
    "external_dependency",
    "other",
]

DeploymentEnvironment = Literal[
    "local",
    "development",
    "test",
    "staging",
    "production",
    "shared",
]

ScalingStrategy = Literal[
    "none",
    "vertical",
    "horizontal",
    "auto_scaling",
    "serverless",
    "partitioning",
    "read_replicas",
    "queue_based",
    "hybrid",
]

AvailabilityTarget = Literal[
    "best_effort",
    "99_percent",
    "99_5_percent",
    "99_9_percent",
    "99_95_percent",
    "99_99_percent",
    "custom",
]

ArchitectureDecisionStatus = Literal[
    "proposed",
    "accepted",
    "rejected",
    "superseded",
    "deprecated",
]

ArchitectureRiskCategory = Literal[
    "complexity",
    "scalability",
    "availability",
    "reliability",
    "performance",
    "security",
    "privacy",
    "compliance",
    "data",
    "integration",
    "vendor_lock_in",
    "operability",
    "maintainability",
    "delivery",
    "cost",
    "technical_debt",
    "other",
]

ScalabilityDimension = Literal[
    "users",
    "requests",
    "data_volume",
    "storage",
    "background_jobs",
    "events",
    "integrations",
    "ai_inference",
    "geographic_distribution",
]

ObservabilitySignal = Literal[
    "logs",
    "metrics",
    "traces",
    "events",
    "audit_logs",
    "health_checks",
    "synthetic_checks",
]

ObservabilityCategory = Literal[
    "availability",
    "performance",
    "reliability",
    "security",
    "business",
    "cost",
    "workflow",
    "integration",
    "data",
    "ai",
]

SolutionArchitectureDecision = Literal[
    "approved",
    "approved_with_assumptions",
    "requires_clarification",
    "cannot_proceed",
]


def _ensure_unique_values[T](
    value: list[T],
    *,
    field_name: str,
) -> list[T]:
    """Return a list after validating that it contains unique values."""

    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must contain unique values.")

    return value


def _normalize_datetime(
    value: datetime,
    *,
    field_name: str,
) -> datetime:
    """Require a timezone-aware datetime and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


class ArchitectureComponent(BuildWiseModel):
    """A logical component within the proposed solution architecture."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    component_type: ArchitectureComponentType
    layer: ComponentLayer

    responsibilities: list[ComponentResponsibilityType] = Field(
        min_length=1,
    )
    responsibility_details: list[MediumText] = Field(min_length=1)

    owns_data: bool = False
    owned_data_entities: list[ShortText] = Field(default_factory=list)

    stateful: bool = False
    externally_accessible: bool = False
    internet_facing: bool = False

    critical: bool = False
    single_point_of_failure: bool = False

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    related_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    related_non_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    dependency_component_ids: list[ArtifactId] = Field(default_factory=list)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "responsibilities",
        "responsibility_details",
        "owned_data_entities",
        "assumptions",
        "constraints",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate component responsibilities and metadata."""

        return _ensure_unique_values(
            value,
            field_name="Architecture component collections",
        )

    @field_validator(
        "related_feature_ids",
        "related_functional_requirement_ids",
        "related_non_functional_requirement_ids",
        "dependency_component_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate component references."""

        return _ensure_unique_values(
            value,
            field_name="Architecture component identifier references",
        )

    @model_validator(mode="after")
    def validate_component(self) -> ArchitectureComponent:
        """Validate data ownership and dependency consistency."""

        if self.id in self.dependency_component_ids:
            raise ValueError("An architecture component cannot depend on itself.")

        if self.owns_data and not self.owned_data_entities:
            raise ValueError("owned_data_entities are required when owns_data is true.")

        if not self.owns_data and self.owned_data_entities:
            raise ValueError("owned_data_entities cannot be provided when owns_data is false.")

        if self.internet_facing and not self.externally_accessible:
            raise ValueError("An internet-facing component must be externally accessible.")

        if self.single_point_of_failure and not self.critical:
            raise ValueError("A single point of failure must be marked as critical.")

        return self


class ArchitectureConnection(BuildWiseModel):
    """A communication path or data flow between architecture components."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    source_component_id: ArtifactId
    target_component_id: ArtifactId

    name: ShortText
    description: MediumText

    connection_type: ConnectionType
    communication_mode: CommunicationMode
    direction: DataFlowDirection = "unidirectional"
    trust_boundary: TrustBoundary

    protocol: ShortText | None = None
    payload_description: MediumText | None = None

    authenticated: bool = True
    encrypted: bool = True

    timeout_seconds: int | None = Field(default=None, ge=1, le=600)
    retries_enabled: bool = False
    maximum_retry_attempts: int | None = Field(default=None, ge=1, le=10)

    idempotency_required: bool = False
    rate_limit_required: bool = False

    failure_behavior: MediumText
    fallback_behavior: MediumText | None = None

    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "related_requirement_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate connection references."""

        return _ensure_unique_values(
            value,
            field_name="Architecture connection identifier references",
        )

    @model_validator(mode="after")
    def validate_connection(self) -> ArchitectureConnection:
        """Validate endpoints, timing, retries, and trust boundaries."""

        if self.source_component_id == self.target_component_id:
            raise ValueError("An architecture connection cannot connect a component to itself.")

        synchronous_modes = {
            "synchronous",
            "streaming",
        }

        if self.communication_mode in synchronous_modes and self.timeout_seconds is None:
            raise ValueError("Synchronous and streaming connections require timeout_seconds.")

        if self.communication_mode not in synchronous_modes and self.timeout_seconds is not None:
            raise ValueError(
                "Batch and asynchronous connections cannot define a synchronous timeout."
            )

        if self.retries_enabled and self.maximum_retry_attempts is None:
            raise ValueError("maximum_retry_attempts is required when retries are enabled.")

        if not self.retries_enabled and self.maximum_retry_attempts is not None:
            raise ValueError("maximum_retry_attempts cannot be provided when retries are disabled.")

        if self.trust_boundary in {"public_network", "third_party"}:
            if not self.authenticated:
                raise ValueError(
                    "Public-network and third-party connections must be authenticated."
                )

            if not self.encrypted:
                raise ValueError("Public-network and third-party connections must be encrypted.")

        if self.communication_mode == "asynchronous" and self.connection_type not in {
            "message_queue",
            "event_stream",
            "webhook",
            "internal_call",
            "other",
        }:
            raise ValueError(
                "Asynchronous communication should use a queue, event "
                "stream, webhook, internal asynchronous call, or an "
                "explicitly documented custom mechanism."
            )

        return self


class TechnologyChoice(BuildWiseModel):
    """A selected or evaluated technology and its architectural rationale."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    category: TechnologyCategory
    technology: ShortText
    version_constraint: ShortText | None = None

    status: TechnologyDecisionStatus = "selected"

    purpose: MediumText
    rationale: MediumText

    advantages: list[MediumText] = Field(min_length=1)
    disadvantages: list[MediumText] = Field(default_factory=list)
    alternatives_considered: list[ShortText] = Field(default_factory=list)

    operational_considerations: list[MediumText] = Field(
        default_factory=list,
    )
    licensing_considerations: MediumText | None = None
    vendor_lock_in_risk: MediumText | None = None

    estimated_costs: list[CostEstimate] = Field(default_factory=list)

    related_component_ids: list[ArtifactId] = Field(default_factory=list)
    related_decision_ids: list[ArtifactId] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    @field_validator(
        "advantages",
        "disadvantages",
        "alternatives_considered",
        "operational_considerations",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate technology-choice statements."""

        return _ensure_unique_values(
            value,
            field_name="Technology choice collections",
        )

    @field_validator(
        "related_component_ids",
        "related_decision_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate technology-choice references."""

        return _ensure_unique_values(
            value,
            field_name="Technology choice identifier references",
        )

    @model_validator(mode="after")
    def validate_technology_choice(self) -> TechnologyChoice:
        """Validate alternatives and selected technology status."""

        normalized_technology = self.technology.casefold()
        normalized_alternatives = {
            alternative.casefold() for alternative in self.alternatives_considered
        }

        if normalized_technology in normalized_alternatives:
            raise ValueError(
                "The selected technology cannot also appear in alternatives_considered."
            )

        if self.status == "rejected" and self.related_component_ids:
            raise ValueError("A rejected technology cannot be assigned to architecture components.")

        return self


class DeploymentUnit(BuildWiseModel):
    """A separately deployable or managed runtime unit."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    unit_type: DeploymentUnitType
    environments: list[DeploymentEnvironment] = Field(min_length=1)

    component_ids: list[ArtifactId] = Field(min_length=1)

    hosting_platform: ShortText
    region: ShortText | None = None

    containerized: bool = False
    image_name: ShortText | None = None

    scaling_strategy: ScalingStrategy = "none"
    minimum_instances: int | None = Field(default=None, ge=0)
    maximum_instances: int | None = Field(default=None, ge=1)

    availability_target: AvailabilityTarget = "best_effort"
    custom_availability_target: ShortText | None = None

    health_check_required: bool = True
    health_check_path: ShortText | None = None

    public_endpoint: bool = False
    private_network_required: bool = False

    persistent_storage_required: bool = False
    storage_description: MediumText | None = None

    environment_variables: list[Slug] = Field(default_factory=list)
    secret_names: list[Slug] = Field(default_factory=list)

    dependency_unit_ids: list[ArtifactId] = Field(default_factory=list)

    estimated_costs: list[CostEstimate] = Field(default_factory=list)

    @field_validator(
        "environments",
        "environment_variables",
        "secret_names",
    )
    @classmethod
    def ensure_unique_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate deployment values."""

        return _ensure_unique_values(
            value,
            field_name="Deployment unit collections",
        )

    @field_validator(
        "component_ids",
        "dependency_unit_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate deployment references."""

        return _ensure_unique_values(
            value,
            field_name="Deployment unit identifier references",
        )

    @model_validator(mode="after")
    def validate_deployment_unit(self) -> DeploymentUnit:
        """Validate containers, scaling, availability, and storage."""

        if self.id in self.dependency_unit_ids:
            raise ValueError("A deployment unit cannot depend on itself.")

        if self.containerized and self.image_name is None:
            raise ValueError("image_name is required when containerized is true.")

        if not self.containerized and self.image_name is not None:
            raise ValueError("image_name cannot be provided when containerized is false.")

        if self.scaling_strategy in {
            "horizontal",
            "auto_scaling",
            "queue_based",
            "hybrid",
        }:
            if self.minimum_instances is None:
                raise ValueError(
                    "minimum_instances is required for horizontally scaled deployment units."
                )

            if self.maximum_instances is None:
                raise ValueError(
                    "maximum_instances is required for horizontally scaled deployment units."
                )

        if (
            self.minimum_instances is not None
            and self.maximum_instances is not None
            and self.maximum_instances < self.minimum_instances
        ):
            raise ValueError("maximum_instances cannot be lower than minimum_instances.")

        if (
            self.scaling_strategy
            in {
                "none",
                "vertical",
                "serverless",
                "partitioning",
                "read_replicas",
            }
            and self.maximum_instances is not None
        ):
            raise ValueError(
                "maximum_instances should only be provided for horizontal, "
                "auto-scaling, queue-based, or hybrid scaling."
            )

        if self.availability_target == "custom":
            if self.custom_availability_target is None:
                raise ValueError(
                    "custom_availability_target is required when availability_target is custom."
                )
        elif self.custom_availability_target is not None:
            raise ValueError(
                "custom_availability_target can only be provided when "
                "availability_target is custom."
            )

        if self.health_check_required and self.health_check_path is None and self.unit_type in {
            "web_application",
            "api_service",
            "worker",
            "container_service",
        }:
            raise ValueError(
                "HTTP or container runtime units requiring health checks "
                "must define health_check_path."
            )

        if not self.health_check_required and self.health_check_path is not None:
            raise ValueError(
                "health_check_path cannot be provided when health checks are disabled."
            )

        if self.persistent_storage_required and self.storage_description is None:
            raise ValueError("storage_description is required when persistent storage is needed.")

        if not self.persistent_storage_required and self.storage_description is not None:
            raise ValueError(
                "storage_description cannot be provided when persistent storage is not required."
            )

        overlapping_configuration = set(self.environment_variables).intersection(self.secret_names)

        if overlapping_configuration:
            formatted = ", ".join(sorted(overlapping_configuration))
            raise ValueError(
                "Configuration names cannot be both environment variables "
                f"and secrets: {formatted}."
            )

        return self


class ArchitectureDecision(BuildWiseModel):
    """An architecture decision record included in the solution proposal."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    title: ShortText
    context: MediumText
    decision: MediumText

    status: ArchitectureDecisionStatus = "proposed"

    rationale: MediumText
    consequences: list[MediumText] = Field(min_length=1)

    positive_consequences: list[MediumText] = Field(default_factory=list)
    negative_consequences: list[MediumText] = Field(default_factory=list)

    alternatives_considered: list[MediumText] = Field(default_factory=list)

    related_component_ids: list[ArtifactId] = Field(default_factory=list)
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)
    supersedes_decision_ids: list[ArtifactId] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    decided_at: datetime = Field(default_factory=utc_now)

    @field_validator("decided_at")
    @classmethod
    def normalize_decided_at(cls, value: datetime) -> datetime:
        """Require decision timestamps to be timezone-aware."""

        return _normalize_datetime(
            value,
            field_name="decided_at",
        )

    @field_validator(
        "consequences",
        "positive_consequences",
        "negative_consequences",
        "alternatives_considered",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate architecture-decision statements."""

        return _ensure_unique_values(
            value,
            field_name="Architecture decision collections",
        )

    @field_validator(
        "related_component_ids",
        "related_requirement_ids",
        "supersedes_decision_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate architecture-decision references."""

        return _ensure_unique_values(
            value,
            field_name="Architecture decision identifier references",
        )

    @model_validator(mode="after")
    def validate_architecture_decision(self) -> ArchitectureDecision:
        """Validate accepted, rejected, and superseding decisions."""

        if self.id in self.supersedes_decision_ids:
            raise ValueError("An architecture decision cannot supersede itself.")

        if self.status == "accepted" and not self.positive_consequences:
            raise ValueError(
                "An accepted architecture decision requires at least one positive consequence."
            )

        if self.status == "rejected" and self.supersedes_decision_ids:
            raise ValueError("A rejected architecture decision cannot supersede another decision.")

        if self.status == "superseded" and not self.supersedes_decision_ids:
            raise ValueError(
                "A superseded decision must identify the related decision "
                "chain through supersedes_decision_ids."
            )

        return self


class ArchitectureRisk(BuildWiseModel):
    """A technical or operational risk identified by the Solution Architect."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: ArchitectureRiskCategory

    severity: RiskSeverity
    likelihood: RiskLikelihood

    potential_impact: MediumText
    trigger_conditions: list[MediumText] = Field(default_factory=list)

    mitigation: MediumText
    contingency: MediumText | None = None

    owner: ShortText | None = None
    monitoring_indicator: MediumText | None = None

    accepted: bool = False
    acceptance_rationale: MediumText | None = None

    affected_component_ids: list[ArtifactId] = Field(default_factory=list)
    affected_deployment_unit_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    related_decision_ids: list[ArtifactId] = Field(default_factory=list)
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("trigger_conditions")
    @classmethod
    def ensure_unique_trigger_conditions(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate risk trigger conditions."""

        return _ensure_unique_values(
            value,
            field_name="trigger_conditions",
        )

    @field_validator(
        "affected_component_ids",
        "affected_deployment_unit_ids",
        "related_decision_ids",
        "related_requirement_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate architecture-risk references."""

        return _ensure_unique_values(
            value,
            field_name="Architecture risk identifier references",
        )

    @model_validator(mode="after")
    def validate_architecture_risk(self) -> ArchitectureRisk:
        """Validate risk acceptance and operational monitoring."""

        if self.accepted and self.acceptance_rationale is None:
            raise ValueError("acceptance_rationale is required when a risk is accepted.")

        if not self.accepted and self.acceptance_rationale is not None:
            raise ValueError("acceptance_rationale cannot be provided when accepted is false.")

        if (
            self.accepted
            and self.severity is RiskSeverity.CRITICAL
            and self.likelihood
            in {
                RiskLikelihood.LIKELY,
                RiskLikelihood.ALMOST_CERTAIN,
            }
        ):
            raise ValueError(
                "A likely or almost-certain critical architecture risk cannot be accepted."
            )

        if (
            self.severity
            in {
                RiskSeverity.HIGH,
                RiskSeverity.CRITICAL,
            }
            and self.monitoring_indicator is None
        ):
            raise ValueError("High and critical architecture risks require a monitoring indicator.")

        return self


class ScalabilityPlan(BuildWiseModel):
    """A measurable plan for scaling one architecture dimension."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    dimension: ScalabilityDimension
    description: MediumText

    current_assumption: ShortText
    expected_mvp_load: ShortText
    expected_growth_load: ShortText

    scaling_trigger: MediumText
    scaling_strategy: ScalingStrategy

    implementation_plan: list[MediumText] = Field(min_length=1)
    validation_method: MediumText

    bottlenecks: list[MediumText] = Field(default_factory=list)
    safeguards: list[MediumText] = Field(default_factory=list)

    related_component_ids: list[ArtifactId] = Field(min_length=1)
    related_deployment_unit_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)

    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE

    @field_validator(
        "implementation_plan",
        "bottlenecks",
        "safeguards",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate scalability-plan statements."""

        return _ensure_unique_values(
            value,
            field_name="Scalability plan collections",
        )

    @field_validator(
        "related_component_ids",
        "related_deployment_unit_ids",
        "related_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate scalability-plan references."""

        return _ensure_unique_values(
            value,
            field_name="Scalability plan identifier references",
        )

    @model_validator(mode="after")
    def validate_scalability_plan(self) -> ScalabilityPlan:
        """Ensure scalable dimensions use an actionable strategy."""

        if self.scaling_strategy == "none":
            raise ValueError("A scalability plan cannot use the none scaling strategy.")

        return self


class ObservabilityRequirement(BuildWiseModel):
    """A required operational signal, alert, dashboard, or diagnostic view."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    category: ObservabilityCategory
    signals: list[ObservabilitySignal] = Field(min_length=1)

    metric_or_event_name: ShortText
    measurement: MediumText

    collection_point: ShortText
    dimensions: list[Slug] = Field(default_factory=list)

    target_or_threshold: ShortText | None = None
    alert_required: bool = False
    alert_condition: MediumText | None = None

    dashboard_required: bool = False
    dashboard_description: MediumText | None = None

    retention_period: ShortText
    contains_sensitive_data: bool = False
    redaction_required: bool = False

    related_component_ids: list[ArtifactId] = Field(min_length=1)
    related_deployment_unit_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)

    priority: RequirementPriority = RequirementPriority.MUST_HAVE

    @field_validator(
        "signals",
        "dimensions",
    )
    @classmethod
    def ensure_unique_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate signals and dimensions."""

        return _ensure_unique_values(
            value,
            field_name="Observability requirement collections",
        )

    @field_validator(
        "related_component_ids",
        "related_deployment_unit_ids",
        "related_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate observability references."""

        return _ensure_unique_values(
            value,
            field_name="Observability requirement identifier references",
        )

    @model_validator(mode="after")
    def validate_observability_requirement(
        self,
    ) -> ObservabilityRequirement:
        """Validate alerts, dashboards, and sensitive telemetry."""

        if self.alert_required and self.alert_condition is None:
            raise ValueError("alert_condition is required when alert_required is true.")

        if not self.alert_required and self.alert_condition is not None:
            raise ValueError("alert_condition cannot be provided when alert_required is false.")

        if self.dashboard_required and self.dashboard_description is None:
            raise ValueError("dashboard_description is required when dashboard_required is true.")

        if not self.dashboard_required and self.dashboard_description is not None:
            raise ValueError(
                "dashboard_description cannot be provided when dashboard_required is false."
            )

        if self.contains_sensitive_data and not self.redaction_required:
            raise ValueError("Sensitive observability data requires redaction.")

        if self.priority is RequirementPriority.MUST_HAVE and self.target_or_threshold is None:
            raise ValueError(
                "A must-have observability requirement requires a target or threshold."
            )

        return self


class SolutionArchitecture(BuildWiseModel):
    """Canonical structured output produced by the Solution Architect.

    The solution architecture maps product and business requirements to
    logical components, communication paths, technologies, deployment units,
    architecture decisions, risks, scalability plans, observability, and
    architecture-owned cost estimates.

    Detailed AI design, model selection, prompt design, RAG design, AI
    guardrails, and AI evaluation remain owned by the AI Architect.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId
    requirements_specification_id: ArtifactId

    title: ShortText
    executive_summary: MediumText

    architecture_style: ArchitectureStyle
    architecture_style_rationale: MediumText

    components: list[ArchitectureComponent] = Field(min_length=1)
    connections: list[ArchitectureConnection] = Field(default_factory=list)
    technology_choices: list[TechnologyChoice] = Field(min_length=1)
    deployment_units: list[DeploymentUnit] = Field(min_length=1)

    decisions: list[ArchitectureDecision] = Field(min_length=1)
    risks: list[ArchitectureRisk] = Field(default_factory=list)

    scalability_plans: list[ScalabilityPlan] = Field(default_factory=list)
    observability_requirements: list[ObservabilityRequirement] = Field(
        min_length=1,
    )

    security_considerations: list[MediumText] = Field(default_factory=list)
    privacy_considerations: list[MediumText] = Field(default_factory=list)
    data_architecture_summary: MediumText
    integration_architecture_summary: MediumText
    deployment_summary: MediumText
    operational_summary: MediumText

    architecture_principles: list[MediumText] = Field(min_length=1)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    open_questions: list[MediumText] = Field(default_factory=list)

    architecture_cost_estimates: list[CostEstimate] = Field(
        default_factory=list,
    )

    decision: SolutionArchitectureDecision
    decision_rationale: MediumText

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    generated_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at", "updated_at")
    @classmethod
    def normalize_architecture_timestamp(
        cls,
        value: datetime,
        info: object,
    ) -> datetime:
        """Require architecture timestamps to be timezone-aware."""

        field_name = getattr(info, "field_name", "timestamp")

        return _normalize_datetime(
            value,
            field_name=field_name,
        )

    @field_validator(
        "components",
        "connections",
        "technology_choices",
        "deployment_units",
        "decisions",
        "risks",
        "scalability_plans",
        "observability_requirements",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[_HasArtifactId],
    ) -> list[_HasArtifactId]:
        """Prevent duplicate artifact IDs inside each architecture collection."""

        artifact_ids = [item.id for item in value]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(
                "SolutionArchitecture artifact IDs must be unique within each collection."
            )

        return value

    @field_validator(
        "security_considerations",
        "privacy_considerations",
        "architecture_principles",
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
        """Prevent duplicate architecture statements."""

        return _ensure_unique_values(
            value,
            field_name="Solution architecture text collections",
        )

    @model_validator(mode="after")
    def validate_solution_architecture(self) -> SolutionArchitecture:
        """Validate architecture traceability and internal references."""

        if self.updated_at < self.generated_at:
            raise ValueError("updated_at cannot be earlier than generated_at.")

        component_ids = {component.id for component in self.components}
        deployment_unit_ids = {unit.id for unit in self.deployment_units}
        decision_ids = {decision.id for decision in self.decisions}

        component_keys = [component.key for component in self.components]
        deployment_keys = [unit.key for unit in self.deployment_units]
        decision_keys = [decision.key for decision in self.decisions]
        observability_keys = [requirement.key for requirement in self.observability_requirements]

        all_keys = component_keys + deployment_keys + decision_keys + observability_keys

        if len(all_keys) != len(set(all_keys)):
            raise ValueError(
                "Component, deployment, decision, and observability keys "
                "must be globally unique within SolutionArchitecture."
            )

        for component in self.components:
            missing_dependencies = set(component.dependency_component_ids).difference(component_ids)

            if missing_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Component '{component.name}'",
                    reference_type="component dependencies",
                    identifiers=missing_dependencies,
                )

        connection_pairs: set[tuple[ArtifactId, ArtifactId, str]] = set()

        for connection in self.connections:
            missing_components = {
                connection.source_component_id,
                connection.target_component_id,
            }.difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Connection '{connection.name}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            connection_key = (
                connection.source_component_id,
                connection.target_component_id,
                connection.name.casefold(),
            )

            if connection_key in connection_pairs:
                raise ValueError(
                    f"Duplicate architecture connection detected for '{connection.name}'."
                )

            connection_pairs.add(connection_key)

        assigned_components: set[ArtifactId] = set()

        for deployment_unit in self.deployment_units:
            missing_components = set(deployment_unit.component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Deployment unit '{deployment_unit.name}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_unit_dependencies = set(deployment_unit.dependency_unit_ids).difference(
                deployment_unit_ids
            )

            if missing_unit_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Deployment unit '{deployment_unit.name}'",
                    reference_type="deployment-unit dependencies",
                    identifiers=missing_unit_dependencies,
                )

            duplicate_assignments = assigned_components.intersection(deployment_unit.component_ids)

            if duplicate_assignments:
                self._raise_duplicate_assignment_error(
                    owner=f"Deployment unit '{deployment_unit.name}'",
                    assignment_type="components",
                    identifiers=duplicate_assignments,
                )

            assigned_components.update(deployment_unit.component_ids)

        unassigned_components = component_ids.difference(assigned_components)

        if unassigned_components:
            self._raise_missing_reference_error(
                owner="SolutionArchitecture",
                reference_type="deployment assignments for components",
                identifiers=unassigned_components,
            )

        for technology in self.technology_choices:
            missing_components = set(technology.related_component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Technology choice '{technology.technology}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_decisions = set(technology.related_decision_ids).difference(decision_ids)

            if missing_decisions:
                self._raise_missing_reference_error(
                    owner=f"Technology choice '{technology.technology}'",
                    reference_type="architecture decisions",
                    identifiers=missing_decisions,
                )

        for decision in self.decisions:
            missing_components = set(decision.related_component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Architecture decision '{decision.title}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_superseded_decisions = set(decision.supersedes_decision_ids).difference(
                decision_ids
            )

            if missing_superseded_decisions:
                self._raise_missing_reference_error(
                    owner=f"Architecture decision '{decision.title}'",
                    reference_type="architecture decisions",
                    identifiers=missing_superseded_decisions,
                )

        for risk in self.risks:
            missing_components = set(risk.affected_component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Architecture risk '{risk.title}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_deployment_units = set(risk.affected_deployment_unit_ids).difference(
                deployment_unit_ids
            )

            if missing_deployment_units:
                self._raise_missing_reference_error(
                    owner=f"Architecture risk '{risk.title}'",
                    reference_type="deployment units",
                    identifiers=missing_deployment_units,
                )

            missing_decisions = set(risk.related_decision_ids).difference(decision_ids)

            if missing_decisions:
                self._raise_missing_reference_error(
                    owner=f"Architecture risk '{risk.title}'",
                    reference_type="architecture decisions",
                    identifiers=missing_decisions,
                )

        for plan in self.scalability_plans:
            missing_components = set(plan.related_component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=f"Scalability plan '{plan.dimension}'",
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_deployment_units = set(plan.related_deployment_unit_ids).difference(
                deployment_unit_ids
            )

            if missing_deployment_units:
                self._raise_missing_reference_error(
                    owner=f"Scalability plan '{plan.dimension}'",
                    reference_type="deployment units",
                    identifiers=missing_deployment_units,
                )

        observed_components: set[ArtifactId] = set()

        for requirement in self.observability_requirements:
            missing_components = set(requirement.related_component_ids).difference(component_ids)

            if missing_components:
                self._raise_missing_reference_error(
                    owner=(f"Observability requirement '{requirement.name}'"),
                    reference_type="components",
                    identifiers=missing_components,
                )

            missing_deployment_units = set(requirement.related_deployment_unit_ids).difference(
                deployment_unit_ids
            )

            if missing_deployment_units:
                self._raise_missing_reference_error(
                    owner=(f"Observability requirement '{requirement.name}'"),
                    reference_type="deployment units",
                    identifiers=missing_deployment_units,
                )

            observed_components.update(requirement.related_component_ids)

        critical_component_ids = {
            component.id for component in self.components if component.critical
        }

        unobserved_critical_components = critical_component_ids.difference(observed_components)

        if unobserved_critical_components:
            self._raise_missing_reference_error(
                owner="SolutionArchitecture",
                reference_type=("observability coverage for critical components"),
                identifiers=unobserved_critical_components,
            )

        production_units = [
            unit for unit in self.deployment_units if "production" in unit.environments
        ]

        if not production_units:
            raise ValueError(
                "SolutionArchitecture requires at least one deployment unit "
                "for the production environment."
            )

        accepted_decisions = [
            decision for decision in self.decisions if decision.status == "accepted"
        ]

        if not accepted_decisions:
            raise ValueError(
                "SolutionArchitecture requires at least one accepted architecture decision."
            )

        selected_technologies = [
            technology
            for technology in self.technology_choices
            if technology.status in {"selected", "approved"}
        ]

        if not selected_technologies:
            raise ValueError(
                "SolutionArchitecture requires at least one selected or approved technology choice."
            )

        if self.decision == "approved" and self.open_questions:
            raise ValueError("An approved SolutionArchitecture cannot contain open questions.")

        if self.decision == "approved_with_assumptions" and not self.assumptions:
            raise ValueError("approved_with_assumptions requires at least one assumption.")

        if self.decision == "requires_clarification" and not self.open_questions:
            raise ValueError("requires_clarification requires at least one open question.")

        if self.decision == "cannot_proceed" and not self.limitations:
            raise ValueError("cannot_proceed requires at least one documented limitation.")

        return self

    @staticmethod
    def _raise_missing_reference_error(
        *,
        owner: str,
        reference_type: str,
        identifiers: set[ArtifactId],
    ) -> None:
        """Raise a consistently formatted missing-reference error."""

        formatted_identifiers = ", ".join(sorted(str(identifier) for identifier in identifiers))

        raise ValueError(f"{owner} references unknown {reference_type}: {formatted_identifiers}.")

    @staticmethod
    def _raise_duplicate_assignment_error(
        *,
        owner: str,
        assignment_type: str,
        identifiers: set[ArtifactId],
    ) -> None:
        """Raise a consistently formatted duplicate-assignment error."""

        formatted_identifiers = ", ".join(sorted(str(identifier) for identifier in identifiers))

        raise ValueError(f"{owner} duplicates assigned {assignment_type}: {formatted_identifiers}.")

    @classmethod
    def validate_requirements_ownership(
        cls,
        *,
        solution_architecture: SolutionArchitecture,
        requirements_specification: object,
    ) -> None:
        """Validate architecture ownership and requirement references.

        A local import prevents an unnecessary module-import dependency.
        """

        from buildwise.domain.requirements import RequirementsSpecification

        if not isinstance(
            requirements_specification,
            RequirementsSpecification,
        ):
            raise TypeError(
                "requirements_specification must be a RequirementsSpecification instance."
            )

        if solution_architecture.session_id != requirements_specification.session_id:
            raise ValueError(
                "SolutionArchitecture and RequirementsSpecification session IDs must match."
            )

        if solution_architecture.requirements_specification_id != requirements_specification.id:
            raise ValueError(
                "SolutionArchitecture.requirements_specification_id must "
                "match RequirementsSpecification.id."
            )

        functional_requirement_ids = {
            requirement.id for requirement in requirements_specification.functional_requirements
        }
        non_functional_requirement_ids = {
            requirement.id for requirement in requirements_specification.non_functional_requirements
        }

        valid_requirement_ids = functional_requirement_ids.union(non_functional_requirement_ids)

        referenced_requirement_ids: set[ArtifactId] = set()

        for component in solution_architecture.components:
            referenced_requirement_ids.update(component.related_functional_requirement_ids)
            referenced_requirement_ids.update(component.related_non_functional_requirement_ids)

        for connection in solution_architecture.connections:
            referenced_requirement_ids.update(connection.related_requirement_ids)

        for decision in solution_architecture.decisions:
            referenced_requirement_ids.update(decision.related_requirement_ids)

        for risk in solution_architecture.risks:
            referenced_requirement_ids.update(risk.related_requirement_ids)

        for plan in solution_architecture.scalability_plans:
            referenced_requirement_ids.update(plan.related_requirement_ids)

        for requirement in solution_architecture.observability_requirements:
            referenced_requirement_ids.update(requirement.related_requirement_ids)

        missing_requirements = referenced_requirement_ids.difference(valid_requirement_ids)

        if missing_requirements:
            cls._raise_missing_reference_error(
                owner="SolutionArchitecture",
                reference_type="RequirementsSpecification requirements",
                identifiers=missing_requirements,
            )

        mapped_functional_requirements = {
            requirement_id
            for component in solution_architecture.components
            for requirement_id in component.related_functional_requirement_ids
        }

        must_have_functional_requirement_ids = {
            requirement.id
            for requirement in requirements_specification.functional_requirements
            if requirement.priority is RequirementPriority.MUST_HAVE
        }

        unmapped_must_have_requirements = must_have_functional_requirement_ids.difference(
            mapped_functional_requirements
        )

        if unmapped_must_have_requirements:
            cls._raise_missing_reference_error(
                owner="SolutionArchitecture",
                reference_type=("component mappings for must-have functional requirements"),
                identifiers=unmapped_must_have_requirements,
            )
