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
    AIUseCaseType,
    ConfidenceLevel,
    ModelStrategyType,
    RequirementPriority,
    RiskLikelihood,
    RiskSeverity,
)


class _HasArtifactId(Protocol):
    """Structural type for AI architecture artifacts with an ID."""

    id: ArtifactId


AIArchitectureDecision = Literal[
    "approved",
    "approved_with_assumptions",
    "requires_clarification",
    "cannot_proceed",
]

AICapabilityStatus = Literal[
    "proposed",
    "validated",
    "deferred",
    "rejected",
]

AICapabilityCriticality = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

ModelRole = Literal[
    "generation",
    "reasoning",
    "classification",
    "extraction",
    "embedding",
    "reranking",
    "moderation",
    "vision",
    "speech",
    "fallback",
    "judge",
]

ModelHostingType = Literal[
    "managed_api",
    "cloud_managed",
    "self_hosted",
    "on_device",
    "hybrid",
]

PromptType = Literal[
    "system",
    "task",
    "classification",
    "extraction",
    "generation",
    "evaluation",
    "guardrail",
    "tool_instruction",
    "routing",
    "repair",
]

PromptVariableType = Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "list",
    "object",
    "artifact",
]

PromptRiskLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

AIToolType = Literal[
    "local_function",
    "crew_ai_tool",
    "mcp_server",
    "application_integration",
    "web_search",
    "web_scraping",
    "database",
    "file_system",
    "code_execution",
    "external_api",
    "notification",
    "other",
]

ToolSideEffect = Literal[
    "none",
    "read_only",
    "reversible_write",
    "irreversible_write",
    "external_action",
]

AgentProcessType = Literal[
    "sequential",
    "hierarchical",
    "flow_orchestrated",
    "direct_agent",
]

AgentMemoryType = Literal[
    "none",
    "short_term",
    "long_term",
    "entity",
    "external",
    "hybrid",
]

RAGRetrievalMode = Literal[
    "dense",
    "sparse",
    "hybrid",
    "graph",
    "metadata_filtered",
    "multi_stage",
]

ChunkingStrategyType = Literal[
    "fixed_size",
    "recursive",
    "semantic",
    "document_structure",
    "parent_child",
    "custom",
]

EmbeddingStrategyType = Literal[
    "single_model",
    "domain_specific",
    "multilingual",
    "multi_vector",
    "hybrid",
]

ContextStrategyType = Literal[
    "top_k",
    "reranked",
    "parent_expansion",
    "adjacent_merge",
    "token_budgeted",
    "compressed",
    "multi_source",
]

GuardrailStage = Literal[
    "input",
    "retrieval",
    "prompt",
    "tool",
    "generation",
    "output",
    "agent",
    "workflow",
]

GuardrailType = Literal[
    "schema_validation",
    "content_filter",
    "prompt_injection_detection",
    "pii_detection",
    "secret_detection",
    "policy_validation",
    "authorization",
    "tool_allowlist",
    "output_grounding",
    "citation_validation",
    "hallucination_detection",
    "rate_limit",
    "budget_limit",
    "human_approval",
    "custom",
]

GuardrailAction = Literal[
    "allow",
    "reject",
    "redact",
    "sanitize",
    "retry",
    "repair",
    "fallback",
    "request_human_review",
    "continue_with_warning",
    "fail_workflow",
]

EvaluationType = Literal[
    "offline",
    "online",
    "human",
    "llm_as_judge",
    "deterministic",
    "hybrid",
]

EvaluationMetricType = Literal[
    "accuracy",
    "precision",
    "recall",
    "f1",
    "groundedness",
    "faithfulness",
    "relevance",
    "completeness",
    "correctness",
    "toxicity",
    "safety",
    "latency",
    "cost",
    "tool_success",
    "schema_validity",
    "citation_quality",
    "retrieval_recall",
    "retrieval_precision",
    "task_completion",
    "human_rating",
    "custom",
]

EvaluationDatasetType = Literal[
    "golden",
    "synthetic",
    "production_sample",
    "adversarial",
    "regression",
    "benchmark",
]

AIRiskCategory = Literal[
    "hallucination",
    "incorrect_output",
    "bias",
    "toxicity",
    "prompt_injection",
    "data_leakage",
    "privacy",
    "security",
    "tool_misuse",
    "excessive_agency",
    "model_drift",
    "retrieval_failure",
    "evaluation_gap",
    "vendor_lock_in",
    "availability",
    "latency",
    "cost",
    "compliance",
    "observability",
    "human_oversight",
    "other",
]

AIObservabilitySignal = Literal[
    "llm_trace",
    "prompt_version",
    "model_call",
    "tool_call",
    "agent_step",
    "flow_event",
    "token_usage",
    "cost",
    "latency",
    "time_to_first_token",
    "tokens_per_second",
    "guardrail_decision",
    "evaluation_score",
    "retrieval_trace",
    "error",
]


def _ensure_unique_values[T](
    value: list[T],
    *,
    field_name: str,
) -> list[T]:
    """Return a list after validating that all values are unique."""

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


class AICapability(BuildWiseModel):
    """A product capability that requires an AI-specific design."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    use_case_type: AIUseCaseType
    status: AICapabilityStatus = "proposed"
    criticality: AICapabilityCriticality = "medium"

    user_value: MediumText
    expected_behavior: MediumText
    non_ai_fallback: MediumText | None = None

    input_description: MediumText
    output_description: MediumText

    deterministic_output_required: bool = False
    human_review_required: bool = False
    user_visible: bool = True

    related_feature_ids: list[ArtifactId] = Field(default_factory=list)
    related_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    related_non_functional_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    assumptions: list[MediumText] = Field(default_factory=list)
    limitations: list[MediumText] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "related_feature_ids",
        "related_functional_requirement_ids",
        "related_non_functional_requirement_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate capability references."""

        return _ensure_unique_values(
            value,
            field_name="AI capability identifier references",
        )

    @field_validator("assumptions", "limitations")
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicated capability statements."""

        return _ensure_unique_values(
            value,
            field_name="AI capability text collections",
        )

    @model_validator(mode="after")
    def validate_capability(self) -> AICapability:
        """Validate critical capability controls."""

        if (
            self.criticality == "critical"
            and self.user_visible
            and not self.human_review_required
            and self.non_ai_fallback is None
        ):
            raise ValueError(
                "A critical user-visible AI capability requires human review "
                "or a documented non-AI fallback."
            )

        if self.status == "rejected" and self.related_feature_ids:
            raise ValueError("A rejected AI capability cannot be assigned to product features.")

        return self


class ModelRequirement(BuildWiseModel):
    """Functional and operational requirements for an AI model role."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    role: ModelRole
    purpose: MediumText

    required_capabilities: list[MediumText] = Field(min_length=1)
    quality_requirements: list[MediumText] = Field(min_length=1)

    maximum_context_tokens: int | None = Field(default=None, ge=1)
    maximum_output_tokens: int | None = Field(default=None, ge=1)

    maximum_latency_ms: int | None = Field(default=None, ge=1)
    maximum_cost_per_request_usd: float | None = Field(
        default=None,
        ge=0.0,
    )

    structured_output_required: bool = False
    tool_calling_required: bool = False
    multimodal_required: bool = False
    streaming_required: bool = False

    data_residency_requirement: MediumText | None = None
    privacy_requirement: MediumText | None = None

    related_capability_ids: list[ArtifactId] = Field(min_length=1)
    related_requirement_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "required_capabilities",
        "quality_requirements",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate model requirement statements."""

        return _ensure_unique_values(
            value,
            field_name="Model requirement text collections",
        )

    @field_validator(
        "related_capability_ids",
        "related_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate model requirement references."""

        return _ensure_unique_values(
            value,
            field_name="Model requirement identifier references",
        )


class ModelSelection(BuildWiseModel):
    """A selected model or model-family recommendation."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText

    provider: ShortText
    model: ShortText
    role: ModelRole
    hosting_type: ModelHostingType

    requirement_id: ArtifactId
    related_capability_ids: list[ArtifactId] = Field(min_length=1)

    purpose: MediumText
    rationale: MediumText

    advantages: list[MediumText] = Field(min_length=1)
    disadvantages: list[MediumText] = Field(default_factory=list)
    alternatives_considered: list[ShortText] = Field(default_factory=list)

    fallback_model_selection_id: ArtifactId | None = None

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    maximum_output_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    maximum_retry_attempts: int = Field(default=2, ge=0, le=10)

    supports_structured_output: bool = False
    supports_tool_calling: bool = False
    supports_streaming: bool = False
    supports_vision: bool = False

    estimated_costs: list[CostEstimate] = Field(default_factory=list)

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    @field_validator(
        "related_capability_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate model-selection references."""

        return _ensure_unique_values(
            value,
            field_name="Model selection identifier references",
        )

    @field_validator(
        "advantages",
        "disadvantages",
        "alternatives_considered",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate model-selection statements."""

        return _ensure_unique_values(
            value,
            field_name="Model selection text collections",
        )

    @model_validator(mode="after")
    def validate_selection(self) -> ModelSelection:
        """Validate alternatives and fallback behavior."""

        if self.fallback_model_selection_id == self.id:
            raise ValueError("A model selection cannot use itself as fallback.")

        selected_model = f"{self.provider}/{self.model}".casefold()
        alternatives = {alternative.casefold() for alternative in self.alternatives_considered}

        if selected_model in alternatives or self.model.casefold() in alternatives:
            raise ValueError("The selected model cannot also appear in alternatives_considered.")

        return self


class PromptVariable(BuildWiseModel):
    """A variable supplied to a versioned prompt contract."""

    name: Slug
    variable_type: PromptVariableType
    description: MediumText

    required: bool = True
    sensitive: bool = False

    default_value_description: MediumText | None = None
    validation_rule: MediumText | None = None

    @model_validator(mode="after")
    def validate_prompt_variable(self) -> PromptVariable:
        """Validate optional variable defaults."""

        if self.required and self.default_value_description is not None:
            raise ValueError("A required prompt variable should not define a default.")

        return self


class PromptContract(BuildWiseModel):
    """A versioned prompt interface used by an AI capability."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    prompt_type: PromptType

    version: ShortText
    purpose: MediumText

    related_capability_ids: list[ArtifactId] = Field(min_length=1)
    related_agent_design_ids: list[ArtifactId] = Field(default_factory=list)
    model_selection_ids: list[ArtifactId] = Field(default_factory=list)

    system_behavior: MediumText | None = None
    instructions_summary: MediumText
    expected_output: MediumText

    variables: list[PromptVariable] = Field(default_factory=list)

    structured_output_required: bool = False
    output_schema_path: str | None = None

    prohibited_behavior: list[MediumText] = Field(min_length=1)
    failure_behavior: MediumText
    repair_strategy: MediumText | None = None

    risk_level: PromptRiskLevel = "medium"
    human_review_required: bool = False

    @field_validator(
        "related_capability_ids",
        "related_agent_design_ids",
        "model_selection_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate prompt references."""

        return _ensure_unique_values(
            value,
            field_name="Prompt contract identifier references",
        )

    @field_validator("prohibited_behavior")
    @classmethod
    def ensure_unique_prohibited_behavior(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate prohibited behaviors."""

        return _ensure_unique_values(
            value,
            field_name="prohibited_behavior",
        )

    @field_validator("variables")
    @classmethod
    def ensure_unique_variables(
        cls,
        value: list[PromptVariable],
    ) -> list[PromptVariable]:
        """Prevent duplicate prompt variable names."""

        names = [variable.name for variable in value]

        if len(names) != len(set(names)):
            raise ValueError("Prompt variable names must be unique.")

        return value

    @model_validator(mode="after")
    def validate_prompt_contract(self) -> PromptContract:
        """Validate schema and high-risk review settings."""

        if self.structured_output_required and self.output_schema_path is None:
            raise ValueError("output_schema_path is required when structured output is required.")

        if not self.structured_output_required and self.output_schema_path is not None:
            raise ValueError(
                "output_schema_path cannot be provided when structured output is not required."
            )

        if self.output_schema_path is not None and not self.output_schema_path.startswith(
            "buildwise.domain."
        ):
            raise ValueError("output_schema_path must reference a BuildWise domain model.")

        if (
            self.risk_level in {"high", "critical"}
            and not self.human_review_required
            and self.repair_strategy is None
        ):
            raise ValueError("High-risk prompts require human review or a repair strategy.")

        return self


class AIToolPolicy(BuildWiseModel):
    """A controlled tool available to an AI agent or workflow."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    tool_type: AIToolType
    side_effect: ToolSideEffect

    purpose: MediumText
    allowed_operations: list[MediumText] = Field(min_length=1)
    prohibited_operations: list[MediumText] = Field(min_length=1)

    authentication_required: bool = False
    authorization_required: bool = False
    human_approval_required: bool = False

    timeout_seconds: int = Field(default=30, ge=1, le=600)
    maximum_retry_attempts: int = Field(default=1, ge=0, le=10)
    maximum_calls_per_execution: int = Field(default=5, ge=1, le=100)

    input_schema_path: str | None = None
    output_schema_path: str | None = None

    sensitive_data_allowed: bool = False
    argument_redaction_required: bool = False
    audit_logging_required: bool = True
    idempotency_required: bool = False

    related_capability_ids: list[ArtifactId] = Field(default_factory=list)
    related_agent_design_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "allowed_operations",
        "prohibited_operations",
    )
    @classmethod
    def ensure_unique_operation_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate tool operations."""

        return _ensure_unique_values(
            value,
            field_name="AI tool operation collections",
        )

    @field_validator(
        "related_capability_ids",
        "related_agent_design_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate tool references."""

        return _ensure_unique_values(
            value,
            field_name="AI tool identifier references",
        )

    @model_validator(mode="after")
    def validate_tool_policy(self) -> AIToolPolicy:
        """Validate side effects and security controls."""

        overlap = set(self.allowed_operations).intersection(self.prohibited_operations)

        if overlap:
            raise ValueError("A tool operation cannot be both allowed and prohibited.")

        if (
            self.side_effect
            in {
                "irreversible_write",
                "external_action",
            }
            and not self.human_approval_required
        ):
            raise ValueError("Irreversible writes and external actions require human approval.")

        if self.side_effect != "none" and not self.authorization_required:
            raise ValueError("Tools with side effects require authorization.")

        if self.sensitive_data_allowed and not self.argument_redaction_required:
            raise ValueError("Tools receiving sensitive data require argument redaction.")

        if (
            self.side_effect in {"reversible_write", "irreversible_write", "external_action"}
            and not self.audit_logging_required
        ):
            raise ValueError("Tools with write side effects require audit logging.")

        return self


class AgentDesign(BuildWiseModel):
    """An AI agent proposed within the product architecture."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText

    role: ShortText
    goal: MediumText
    backstory_summary: MediumText

    responsibilities: list[MediumText] = Field(min_length=1)
    exclusions: list[MediumText] = Field(min_length=1)

    process_type: AgentProcessType = "flow_orchestrated"
    memory_type: AgentMemoryType = "none"

    model_selection_id: ArtifactId
    prompt_contract_ids: list[ArtifactId] = Field(min_length=1)
    tool_policy_ids: list[ArtifactId] = Field(default_factory=list)

    related_capability_ids: list[ArtifactId] = Field(min_length=1)

    allow_delegation: bool = False
    maximum_iterations: int = Field(default=10, ge=1, le=50)
    maximum_tool_calls: int = Field(default=10, ge=0, le=100)

    structured_output_required: bool = True
    output_schema_path: str | None = None

    human_approval_required: bool = False
    failure_behavior: MediumText

    @field_validator(
        "responsibilities",
        "exclusions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate agent statements."""

        return _ensure_unique_values(
            value,
            field_name="Agent design text collections",
        )

    @field_validator(
        "prompt_contract_ids",
        "tool_policy_ids",
        "related_capability_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate agent references."""

        return _ensure_unique_values(
            value,
            field_name="Agent design identifier references",
        )

    @model_validator(mode="after")
    def validate_agent_design(self) -> AgentDesign:
        """Validate responsibility boundaries and outputs."""

        overlap = {value.casefold() for value in self.responsibilities}.intersection(
            value.casefold() for value in self.exclusions
        )

        if overlap:
            raise ValueError("Agent responsibilities and exclusions cannot overlap.")

        if self.structured_output_required and self.output_schema_path is None:
            raise ValueError("output_schema_path is required for structured agent output.")

        if not self.structured_output_required and self.output_schema_path is not None:
            raise ValueError(
                "output_schema_path cannot be provided when structured output is disabled."
            )

        if self.output_schema_path is not None and not self.output_schema_path.startswith(
            "buildwise.domain."
        ):
            raise ValueError("output_schema_path must reference a BuildWise domain model.")

        if self.maximum_tool_calls == 0 and self.tool_policy_ids:
            raise ValueError("tool_policy_ids cannot be provided when maximum_tool_calls is zero.")

        return self


class AgentWorkflowStep(BuildWiseModel):
    """A single step in an agent or AI workflow."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    sequence: int = Field(ge=1)
    name: ShortText
    description: MediumText

    agent_design_id: ArtifactId | None = None
    capability_id: ArtifactId

    input_description: MediumText
    output_description: MediumText

    depends_on_step_ids: list[ArtifactId] = Field(default_factory=list)

    conditional: bool = False
    condition: MediumText | None = None

    human_approval_required: bool = False
    failure_behavior: MediumText

    @field_validator("depends_on_step_ids")
    @classmethod
    def ensure_unique_dependencies(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate workflow dependencies."""

        return _ensure_unique_values(
            value,
            field_name="depends_on_step_ids",
        )

    @model_validator(mode="after")
    def validate_workflow_step(self) -> AgentWorkflowStep:
        """Validate conditions and self-dependencies."""

        if self.id in self.depends_on_step_ids:
            raise ValueError("A workflow step cannot depend on itself.")

        if self.conditional and self.condition is None:
            raise ValueError("condition is required for a conditional workflow step.")

        if not self.conditional and self.condition is not None:
            raise ValueError("condition cannot be provided for an unconditional step.")

        return self


class AgentWorkflow(BuildWiseModel):
    """A structured AI or agent workflow."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    process_type: AgentProcessType
    steps: list[AgentWorkflowStep] = Field(min_length=1)

    entry_condition: MediumText
    completion_condition: MediumText
    failure_behavior: MediumText

    maximum_execution_seconds: int = Field(default=600, ge=1, le=7_200)
    maximum_total_tool_calls: int = Field(default=30, ge=0, le=500)

    state_description: MediumText
    persistence_required: bool = False
    resumable: bool = False
    streaming_required: bool = False

    @field_validator("steps")
    @classmethod
    def validate_steps(
        cls,
        value: list[AgentWorkflowStep],
    ) -> list[AgentWorkflowStep]:
        """Require unique contiguous workflow sequences."""

        ids = [step.id for step in value]
        sequences = [step.sequence for step in value]

        if len(ids) != len(set(ids)):
            raise ValueError("Agent workflow step IDs must be unique.")

        if len(sequences) != len(set(sequences)):
            raise ValueError("Agent workflow step sequences must be unique.")

        expected = list(range(1, len(value) + 1))

        if sorted(sequences) != expected:
            raise ValueError("Agent workflow step sequences must be contiguous and start at one.")

        return sorted(value, key=lambda step: step.sequence)

    @model_validator(mode="after")
    def validate_workflow(self) -> AgentWorkflow:
        """Validate workflow dependencies and resumability."""

        step_ids = {step.id for step in self.steps}

        for step in self.steps:
            missing_dependencies = set(step.depends_on_step_ids).difference(step_ids)

            if missing_dependencies:
                raise ValueError(f"Workflow step '{step.name}' references unknown dependencies.")

        if self.resumable and not self.persistence_required:
            raise ValueError("A resumable workflow requires persistence.")

        return self


class EmbeddingStrategy(BuildWiseModel):
    """Embedding design for a RAG implementation."""

    provider: ShortText
    model: ShortText
    strategy_type: EmbeddingStrategyType

    dimensions: int | None = Field(default=None, ge=1)
    multilingual: bool = False

    normalization_required: bool = False
    batch_size: int = Field(default=32, ge=1, le=2_048)

    rationale: MediumText
    limitations: list[MediumText] = Field(default_factory=list)

    @field_validator("limitations")
    @classmethod
    def ensure_unique_limitations(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate embedding limitations."""

        return _ensure_unique_values(
            value,
            field_name="limitations",
        )


class ChunkingStrategy(BuildWiseModel):
    """Chunking design for indexed knowledge."""

    strategy_type: ChunkingStrategyType

    target_chunk_tokens: int = Field(ge=50, le=8_000)
    overlap_tokens: int = Field(default=0, ge=0, le=2_000)

    preserve_headings: bool = True
    preserve_tables: bool = True
    preserve_code_blocks: bool = True

    parent_child_enabled: bool = False
    metadata_fields: list[Slug] = Field(default_factory=list)

    rationale: MediumText
    validation_method: MediumText

    @field_validator("metadata_fields")
    @classmethod
    def ensure_unique_metadata_fields(
        cls,
        value: list[Slug],
    ) -> list[Slug]:
        """Prevent duplicate metadata fields."""

        return _ensure_unique_values(
            value,
            field_name="metadata_fields",
        )

    @model_validator(mode="after")
    def validate_chunking(self) -> ChunkingStrategy:
        """Validate overlap relative to chunk size."""

        if self.overlap_tokens >= self.target_chunk_tokens:
            raise ValueError("overlap_tokens must be lower than target_chunk_tokens.")

        if self.strategy_type == "parent_child" and not self.parent_child_enabled:
            raise ValueError("The parent_child strategy requires parent_child_enabled.")

        return self


class RetrievalStrategy(BuildWiseModel):
    """Retrieval and reranking strategy for RAG."""

    retrieval_mode: RAGRetrievalMode

    initial_top_k: int = Field(default=20, ge=1, le=1_000)
    final_top_k: int = Field(default=5, ge=1, le=100)

    metadata_filtering_required: bool = False
    reranking_required: bool = False

    reranker_provider: ShortText | None = None
    reranker_model: ShortText | None = None

    minimum_relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    rationale: MediumText
    fallback_behavior: MediumText

    @model_validator(mode="after")
    def validate_retrieval(self) -> RetrievalStrategy:
        """Validate top-k and reranker configuration."""

        if self.final_top_k > self.initial_top_k:
            raise ValueError("final_top_k cannot exceed initial_top_k.")

        if self.reranking_required:
            if self.reranker_provider is None or self.reranker_model is None:
                raise ValueError("Reranking requires reranker_provider and reranker_model.")
        elif self.reranker_provider is not None or self.reranker_model is not None:
            raise ValueError(
                "Reranker configuration cannot be supplied when reranking is disabled."
            )

        return self


class ContextConstructionStrategy(BuildWiseModel):
    """Strategy for constructing LLM context from retrieval results."""

    strategy_types: list[ContextStrategyType] = Field(min_length=1)

    maximum_context_tokens: int = Field(ge=100, le=1_000_000)
    reserved_output_tokens: int = Field(ge=1)

    citation_required: bool = True
    source_deduplication_required: bool = True

    truncation_strategy: MediumText
    empty_context_behavior: MediumText

    @field_validator("strategy_types")
    @classmethod
    def ensure_unique_strategy_types(
        cls,
        value: list[ContextStrategyType],
    ) -> list[ContextStrategyType]:
        """Prevent duplicate context strategies."""

        return _ensure_unique_values(
            value,
            field_name="strategy_types",
        )

    @model_validator(mode="after")
    def validate_context_strategy(
        self,
    ) -> ContextConstructionStrategy:
        """Validate token allocation."""

        if self.reserved_output_tokens >= self.maximum_context_tokens:
            raise ValueError("reserved_output_tokens must be lower than maximum_context_tokens.")

        return self


class RAGDesign(BuildWiseModel):
    """Complete retrieval-augmented generation design."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    enabled: bool = True
    related_capability_ids: list[ArtifactId] = Field(min_length=1)

    knowledge_sources: list[MediumText] = Field(min_length=1)
    ingestion_strategy: MediumText

    chunking: ChunkingStrategy
    embedding: EmbeddingStrategy
    retrieval: RetrievalStrategy
    context_construction: ContextConstructionStrategy

    vector_store: ShortText
    metadata_strategy: MediumText

    access_control_filtering_required: bool = False
    freshness_strategy: MediumText
    deletion_strategy: MediumText

    evaluation_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    @field_validator(
        "related_capability_ids",
        "evaluation_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate RAG references."""

        return _ensure_unique_values(
            value,
            field_name="RAG identifier references",
        )

    @field_validator("knowledge_sources")
    @classmethod
    def ensure_unique_knowledge_sources(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate knowledge-source descriptions."""

        return _ensure_unique_values(
            value,
            field_name="knowledge_sources",
        )

    @model_validator(mode="after")
    def validate_rag_design(self) -> RAGDesign:
        """Validate enabled RAG configuration."""

        if not self.enabled:
            raise ValueError("A RAGDesign artifact should only be created when RAG is enabled.")

        return self


class AIGuardrail(BuildWiseModel):
    """A deterministic or model-assisted AI guardrail."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    stage: GuardrailStage
    guardrail_type: GuardrailType

    trigger_condition: MediumText
    validation_method: MediumText
    action: GuardrailAction

    blocking: bool = True
    retry_allowed: bool = False
    maximum_retry_attempts: int | None = Field(default=None, ge=1, le=10)

    human_review_required: bool = False
    audit_required: bool = True

    related_capability_ids: list[ArtifactId] = Field(default_factory=list)
    related_agent_design_ids: list[ArtifactId] = Field(default_factory=list)
    related_tool_policy_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "related_capability_ids",
        "related_agent_design_ids",
        "related_tool_policy_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate guardrail references."""

        return _ensure_unique_values(
            value,
            field_name="AI guardrail identifier references",
        )

    @model_validator(mode="after")
    def validate_guardrail(self) -> AIGuardrail:
        """Validate retries and approval behavior."""

        if self.retry_allowed and self.maximum_retry_attempts is None:
            raise ValueError("maximum_retry_attempts is required when retry is allowed.")

        if not self.retry_allowed and self.maximum_retry_attempts is not None:
            raise ValueError("maximum_retry_attempts cannot be provided when retry is disabled.")

        if self.action == "request_human_review" and not self.human_review_required:
            raise ValueError("A human-review guardrail action requires human_review_required.")

        return self


class AIEvaluationMetric(BuildWiseModel):
    """A measurable AI quality or runtime metric."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    metric_type: EvaluationMetricType

    description: MediumText
    measurement_method: MediumText

    target: ShortText
    minimum_acceptable_value: ShortText | None = None

    blocking: bool = False
    higher_is_better: bool | None = None

    related_capability_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("related_capability_ids")
    @classmethod
    def ensure_unique_capability_ids(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate metric capability references."""

        return _ensure_unique_values(
            value,
            field_name="related_capability_ids",
        )


class EvaluationDataset(BuildWiseModel):
    """A dataset used for AI evaluation or regression testing."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    dataset_type: EvaluationDatasetType

    purpose: MediumText
    source_description: MediumText

    expected_size: int = Field(ge=1)
    contains_sensitive_data: bool = False

    anonymization_required: bool = False
    human_review_required: bool = False

    versioning_strategy: MediumText
    refresh_strategy: MediumText

    related_capability_ids: list[ArtifactId] = Field(min_length=1)

    @field_validator("related_capability_ids")
    @classmethod
    def ensure_unique_capability_ids(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate dataset capability references."""

        return _ensure_unique_values(
            value,
            field_name="related_capability_ids",
        )

    @model_validator(mode="after")
    def validate_dataset(self) -> EvaluationDataset:
        """Validate sensitive evaluation data controls."""

        if self.contains_sensitive_data and not self.anonymization_required:
            raise ValueError("Sensitive evaluation datasets require anonymization.")

        return self


class AIEvaluationRequirement(BuildWiseModel):
    """A complete evaluation requirement for an AI capability."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    evaluation_type: EvaluationType
    related_capability_ids: list[ArtifactId] = Field(min_length=1)

    metric_ids: list[ArtifactId] = Field(min_length=1)
    dataset_ids: list[ArtifactId] = Field(min_length=1)

    execution_frequency: ShortText
    blocking_release: bool = False

    failure_action: MediumText
    regression_policy: MediumText

    owner: ShortText
    reporting_destination: MediumText

    @field_validator(
        "related_capability_ids",
        "metric_ids",
        "dataset_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate evaluation references."""

        return _ensure_unique_values(
            value,
            field_name="AI evaluation identifier references",
        )


class AIObservabilityRequirement(BuildWiseModel):
    """An observability requirement specific to AI execution."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    name: ShortText
    description: MediumText

    signals: list[AIObservabilitySignal] = Field(min_length=1)

    collection_point: ShortText
    dimensions: list[Slug] = Field(default_factory=list)

    target_or_threshold: ShortText | None = None
    alert_required: bool = False
    alert_condition: MediumText | None = None

    retention_period: ShortText
    sensitive_data_possible: bool = False
    redaction_required: bool = False

    related_capability_ids: list[ArtifactId] = Field(default_factory=list)
    related_agent_design_ids: list[ArtifactId] = Field(default_factory=list)
    related_model_selection_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    priority: RequirementPriority = RequirementPriority.MUST_HAVE

    @field_validator("signals", "dimensions")
    @classmethod
    def ensure_unique_values(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate observability signals and dimensions."""

        return _ensure_unique_values(
            value,
            field_name="AI observability collections",
        )

    @field_validator(
        "related_capability_ids",
        "related_agent_design_ids",
        "related_model_selection_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate AI observability references."""

        return _ensure_unique_values(
            value,
            field_name="AI observability identifier references",
        )

    @model_validator(mode="after")
    def validate_observability(
        self,
    ) -> AIObservabilityRequirement:
        """Validate alerts and sensitive telemetry."""

        if self.alert_required and self.alert_condition is None:
            raise ValueError("alert_condition is required when alerting is enabled.")

        if not self.alert_required and self.alert_condition is not None:
            raise ValueError("alert_condition cannot be provided when alerting is disabled.")

        if self.sensitive_data_possible and not self.redaction_required:
            raise ValueError("Potentially sensitive AI telemetry requires redaction.")

        if self.priority is RequirementPriority.MUST_HAVE and self.target_or_threshold is None:
            raise ValueError(
                "A must-have AI observability requirement requires a target or threshold."
            )

        return self


class AIArchitectureRisk(BuildWiseModel):
    """A risk specific to model-driven or agentic behavior."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: AIRiskCategory

    severity: RiskSeverity
    likelihood: RiskLikelihood

    potential_impact: MediumText
    trigger_conditions: list[MediumText] = Field(default_factory=list)

    mitigation: MediumText
    contingency: MediumText | None = None

    monitoring_indicator: MediumText | None = None
    owner: ShortText | None = None

    accepted: bool = False
    acceptance_rationale: MediumText | None = None

    affected_capability_ids: list[ArtifactId] = Field(default_factory=list)
    affected_model_selection_ids: list[ArtifactId] = Field(
        default_factory=list,
    )
    affected_agent_design_ids: list[ArtifactId] = Field(default_factory=list)
    related_guardrail_ids: list[ArtifactId] = Field(default_factory=list)
    related_evaluation_requirement_ids: list[ArtifactId] = Field(
        default_factory=list,
    )

    @field_validator("trigger_conditions")
    @classmethod
    def ensure_unique_trigger_conditions(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate AI-risk triggers."""

        return _ensure_unique_values(
            value,
            field_name="trigger_conditions",
        )

    @field_validator(
        "affected_capability_ids",
        "affected_model_selection_ids",
        "affected_agent_design_ids",
        "related_guardrail_ids",
        "related_evaluation_requirement_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate AI-risk references."""

        return _ensure_unique_values(
            value,
            field_name="AI architecture risk identifier references",
        )

    @model_validator(mode="after")
    def validate_risk(self) -> AIArchitectureRisk:
        """Validate monitoring and acceptance controls."""

        if self.accepted and self.acceptance_rationale is None:
            raise ValueError("acceptance_rationale is required when a risk is accepted.")

        if not self.accepted and self.acceptance_rationale is not None:
            raise ValueError("acceptance_rationale cannot be provided when accepted is false.")

        if (
            self.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}
            and self.monitoring_indicator is None
        ):
            raise ValueError("High and critical AI risks require a monitoring indicator.")

        if (
            self.accepted
            and self.severity is RiskSeverity.CRITICAL
            and self.likelihood
            in {
                RiskLikelihood.LIKELY,
                RiskLikelihood.ALMOST_CERTAIN,
            }
        ):
            raise ValueError("A likely or almost-certain critical AI risk cannot be accepted.")

        return self


class AIArchitecture(BuildWiseModel):
    """Canonical structured output produced by the AI Architect.

    This artifact defines AI capabilities, model strategy, prompts, tools,
    agents, workflows, RAG, guardrails, evaluation, observability, risks,
    and AI-specific costs.

    General application components, deployment topology, technology choices,
    and infrastructure remain owned by SolutionArchitecture.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId

    requirements_specification_id: ArtifactId
    solution_architecture_id: ArtifactId

    title: ShortText
    executive_summary: MediumText

    model_strategy: ModelStrategyType
    model_strategy_rationale: MediumText

    capabilities: list[AICapability] = Field(min_length=1)

    model_requirements: list[ModelRequirement] = Field(min_length=1)
    model_selections: list[ModelSelection] = Field(min_length=1)

    prompt_contracts: list[PromptContract] = Field(default_factory=list)
    tool_policies: list[AIToolPolicy] = Field(default_factory=list)

    agent_designs: list[AgentDesign] = Field(default_factory=list)
    agent_workflows: list[AgentWorkflow] = Field(default_factory=list)

    rag_designs: list[RAGDesign] = Field(default_factory=list)

    guardrails: list[AIGuardrail] = Field(min_length=1)

    evaluation_metrics: list[AIEvaluationMetric] = Field(min_length=1)
    evaluation_datasets: list[EvaluationDataset] = Field(min_length=1)
    evaluation_requirements: list[AIEvaluationRequirement] = Field(
        min_length=1,
    )

    observability_requirements: list[AIObservabilityRequirement] = Field(
        min_length=1,
    )

    risks: list[AIArchitectureRisk] = Field(default_factory=list)

    human_oversight_strategy: MediumText
    fallback_strategy: MediumText
    cost_control_strategy: MediumText
    privacy_strategy: MediumText
    security_boundary_summary: MediumText

    ai_principles: list[MediumText] = Field(min_length=1)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    open_questions: list[MediumText] = Field(default_factory=list)

    ai_cost_estimates: list[CostEstimate] = Field(default_factory=list)

    decision: AIArchitectureDecision
    decision_rationale: MediumText

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    generated_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at", "updated_at")
    @classmethod
    def normalize_timestamp(
        cls,
        value: datetime,
        info: object,
    ) -> datetime:
        """Normalize AI architecture timestamps to UTC."""

        field_name = getattr(info, "field_name", "timestamp")

        return _normalize_datetime(
            value,
            field_name=field_name,
        )

    @field_validator(
        "capabilities",
        "model_requirements",
        "model_selections",
        "prompt_contracts",
        "tool_policies",
        "agent_designs",
        "agent_workflows",
        "rag_designs",
        "guardrails",
        "evaluation_metrics",
        "evaluation_datasets",
        "evaluation_requirements",
        "observability_requirements",
        "risks",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[_HasArtifactId],
    ) -> list[_HasArtifactId]:
        """Prevent duplicate IDs within AI architecture collections."""

        artifact_ids = [item.id for item in value]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("AIArchitecture artifact IDs must be unique within each collection.")

        return value

    @field_validator(
        "ai_principles",
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
        """Prevent duplicate AI architecture statements."""

        return _ensure_unique_values(
            value,
            field_name="AI architecture text collections",
        )

    @model_validator(mode="after")
    def validate_ai_architecture(self) -> AIArchitecture:
        """Validate AI architecture references and completeness."""

        if self.updated_at < self.generated_at:
            raise ValueError("updated_at cannot be earlier than generated_at.")

        capability_ids = {capability.id for capability in self.capabilities}
        model_requirement_ids = {requirement.id for requirement in self.model_requirements}
        model_selection_ids = {selection.id for selection in self.model_selections}
        prompt_contract_ids = {prompt.id for prompt in self.prompt_contracts}
        tool_policy_ids = {policy.id for policy in self.tool_policies}
        agent_design_ids = {design.id for design in self.agent_designs}
        evaluation_metric_ids = {metric.id for metric in self.evaluation_metrics}
        evaluation_dataset_ids = {dataset.id for dataset in self.evaluation_datasets}
        evaluation_requirement_ids = {
            requirement.id for requirement in self.evaluation_requirements
        }
        guardrail_ids = {guardrail.id for guardrail in self.guardrails}

        self._validate_model_references(
            capability_ids=capability_ids,
            model_requirement_ids=model_requirement_ids,
            model_selection_ids=model_selection_ids,
        )
        self._validate_prompt_references(
            capability_ids=capability_ids,
            agent_design_ids=agent_design_ids,
            model_selection_ids=model_selection_ids,
        )
        self._validate_tool_references(
            capability_ids=capability_ids,
            agent_design_ids=agent_design_ids,
        )
        self._validate_agent_references(
            capability_ids=capability_ids,
            model_selection_ids=model_selection_ids,
            prompt_contract_ids=prompt_contract_ids,
            tool_policy_ids=tool_policy_ids,
        )
        self._validate_workflow_references(
            capability_ids=capability_ids,
            agent_design_ids=agent_design_ids,
        )
        self._validate_rag_references(
            capability_ids=capability_ids,
            evaluation_requirement_ids=evaluation_requirement_ids,
        )
        self._validate_guardrail_references(
            capability_ids=capability_ids,
            agent_design_ids=agent_design_ids,
            tool_policy_ids=tool_policy_ids,
        )
        self._validate_evaluation_references(
            capability_ids=capability_ids,
            evaluation_metric_ids=evaluation_metric_ids,
            evaluation_dataset_ids=evaluation_dataset_ids,
        )
        self._validate_observability_references(
            capability_ids=capability_ids,
            agent_design_ids=agent_design_ids,
            model_selection_ids=model_selection_ids,
        )
        self._validate_risk_references(
            capability_ids=capability_ids,
            model_selection_ids=model_selection_ids,
            agent_design_ids=agent_design_ids,
            guardrail_ids=guardrail_ids,
            evaluation_requirement_ids=evaluation_requirement_ids,
        )
        self._validate_required_design_coverage(
            capability_ids=capability_ids,
        )
        self._validate_decision_consistency()

        return self

    def _validate_model_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        model_requirement_ids: set[ArtifactId],
        model_selection_ids: set[ArtifactId],
    ) -> None:
        """Validate model requirement and selection references."""

        for requirement in self.model_requirements:
            self._require_known_references(
                owner=f"Model requirement '{requirement.key}'",
                reference_type="capabilities",
                identifiers=set(requirement.related_capability_ids),
                valid_identifiers=capability_ids,
            )

        for selection in self.model_selections:
            self._require_known_references(
                owner=f"Model selection '{selection.name}'",
                reference_type="capabilities",
                identifiers=set(selection.related_capability_ids),
                valid_identifiers=capability_ids,
            )

            if selection.requirement_id not in model_requirement_ids:
                self._raise_missing_reference_error(
                    owner=f"Model selection '{selection.name}'",
                    reference_type="model requirements",
                    identifiers={selection.requirement_id},
                )

            if (
                selection.fallback_model_selection_id is not None
                and selection.fallback_model_selection_id not in model_selection_ids
            ):
                self._raise_missing_reference_error(
                    owner=f"Model selection '{selection.name}'",
                    reference_type="fallback model selections",
                    identifiers={selection.fallback_model_selection_id},
                )

    def _validate_prompt_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
        model_selection_ids: set[ArtifactId],
    ) -> None:
        """Validate prompt contract references."""

        for prompt in self.prompt_contracts:
            self._require_known_references(
                owner=f"Prompt contract '{prompt.name}'",
                reference_type="capabilities",
                identifiers=set(prompt.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"Prompt contract '{prompt.name}'",
                reference_type="agent designs",
                identifiers=set(prompt.related_agent_design_ids),
                valid_identifiers=agent_design_ids,
            )
            self._require_known_references(
                owner=f"Prompt contract '{prompt.name}'",
                reference_type="model selections",
                identifiers=set(prompt.model_selection_ids),
                valid_identifiers=model_selection_ids,
            )

    def _validate_tool_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
    ) -> None:
        """Validate AI tool policy references."""

        for policy in self.tool_policies:
            self._require_known_references(
                owner=f"AI tool policy '{policy.name}'",
                reference_type="capabilities",
                identifiers=set(policy.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"AI tool policy '{policy.name}'",
                reference_type="agent designs",
                identifiers=set(policy.related_agent_design_ids),
                valid_identifiers=agent_design_ids,
            )

    def _validate_agent_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        model_selection_ids: set[ArtifactId],
        prompt_contract_ids: set[ArtifactId],
        tool_policy_ids: set[ArtifactId],
    ) -> None:
        """Validate AI agent design references."""

        for design in self.agent_designs:
            self._require_known_references(
                owner=f"Agent design '{design.name}'",
                reference_type="capabilities",
                identifiers=set(design.related_capability_ids),
                valid_identifiers=capability_ids,
            )

            if design.model_selection_id not in model_selection_ids:
                self._raise_missing_reference_error(
                    owner=f"Agent design '{design.name}'",
                    reference_type="model selections",
                    identifiers={design.model_selection_id},
                )

            self._require_known_references(
                owner=f"Agent design '{design.name}'",
                reference_type="prompt contracts",
                identifiers=set(design.prompt_contract_ids),
                valid_identifiers=prompt_contract_ids,
            )
            self._require_known_references(
                owner=f"Agent design '{design.name}'",
                reference_type="tool policies",
                identifiers=set(design.tool_policy_ids),
                valid_identifiers=tool_policy_ids,
            )

    def _validate_workflow_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
    ) -> None:
        """Validate agent workflow references."""

        for workflow in self.agent_workflows:
            for step in workflow.steps:
                if step.capability_id not in capability_ids:
                    self._raise_missing_reference_error(
                        owner=f"Workflow step '{step.name}'",
                        reference_type="capabilities",
                        identifiers={step.capability_id},
                    )

                if (
                    step.agent_design_id is not None
                    and step.agent_design_id not in agent_design_ids
                ):
                    self._raise_missing_reference_error(
                        owner=f"Workflow step '{step.name}'",
                        reference_type="agent designs",
                        identifiers={step.agent_design_id},
                    )

    def _validate_rag_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        evaluation_requirement_ids: set[ArtifactId],
    ) -> None:
        """Validate RAG design references."""

        for design in self.rag_designs:
            self._require_known_references(
                owner="RAG design",
                reference_type="capabilities",
                identifiers=set(design.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner="RAG design",
                reference_type="evaluation requirements",
                identifiers=set(design.evaluation_requirement_ids),
                valid_identifiers=evaluation_requirement_ids,
            )

    def _validate_guardrail_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
        tool_policy_ids: set[ArtifactId],
    ) -> None:
        """Validate guardrail references."""

        for guardrail in self.guardrails:
            self._require_known_references(
                owner=f"AI guardrail '{guardrail.name}'",
                reference_type="capabilities",
                identifiers=set(guardrail.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"AI guardrail '{guardrail.name}'",
                reference_type="agent designs",
                identifiers=set(guardrail.related_agent_design_ids),
                valid_identifiers=agent_design_ids,
            )
            self._require_known_references(
                owner=f"AI guardrail '{guardrail.name}'",
                reference_type="tool policies",
                identifiers=set(guardrail.related_tool_policy_ids),
                valid_identifiers=tool_policy_ids,
            )

    def _validate_evaluation_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        evaluation_metric_ids: set[ArtifactId],
        evaluation_dataset_ids: set[ArtifactId],
    ) -> None:
        """Validate evaluation metric, dataset, and requirement references."""

        for metric in self.evaluation_metrics:
            self._require_known_references(
                owner=f"Evaluation metric '{metric.name}'",
                reference_type="capabilities",
                identifiers=set(metric.related_capability_ids),
                valid_identifiers=capability_ids,
            )

        for dataset in self.evaluation_datasets:
            self._require_known_references(
                owner=f"Evaluation dataset '{dataset.name}'",
                reference_type="capabilities",
                identifiers=set(dataset.related_capability_ids),
                valid_identifiers=capability_ids,
            )

        for requirement in self.evaluation_requirements:
            self._require_known_references(
                owner=f"Evaluation requirement '{requirement.name}'",
                reference_type="capabilities",
                identifiers=set(requirement.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"Evaluation requirement '{requirement.name}'",
                reference_type="metrics",
                identifiers=set(requirement.metric_ids),
                valid_identifiers=evaluation_metric_ids,
            )
            self._require_known_references(
                owner=f"Evaluation requirement '{requirement.name}'",
                reference_type="datasets",
                identifiers=set(requirement.dataset_ids),
                valid_identifiers=evaluation_dataset_ids,
            )

    def _validate_observability_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
        model_selection_ids: set[ArtifactId],
    ) -> None:
        """Validate AI observability references."""

        for requirement in self.observability_requirements:
            self._require_known_references(
                owner=f"AI observability requirement '{requirement.name}'",
                reference_type="capabilities",
                identifiers=set(requirement.related_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"AI observability requirement '{requirement.name}'",
                reference_type="agent designs",
                identifiers=set(requirement.related_agent_design_ids),
                valid_identifiers=agent_design_ids,
            )
            self._require_known_references(
                owner=f"AI observability requirement '{requirement.name}'",
                reference_type="model selections",
                identifiers=set(requirement.related_model_selection_ids),
                valid_identifiers=model_selection_ids,
            )

    def _validate_risk_references(
        self,
        *,
        capability_ids: set[ArtifactId],
        model_selection_ids: set[ArtifactId],
        agent_design_ids: set[ArtifactId],
        guardrail_ids: set[ArtifactId],
        evaluation_requirement_ids: set[ArtifactId],
    ) -> None:
        """Validate AI risk references."""

        for risk in self.risks:
            self._require_known_references(
                owner=f"AI risk '{risk.title}'",
                reference_type="capabilities",
                identifiers=set(risk.affected_capability_ids),
                valid_identifiers=capability_ids,
            )
            self._require_known_references(
                owner=f"AI risk '{risk.title}'",
                reference_type="model selections",
                identifiers=set(risk.affected_model_selection_ids),
                valid_identifiers=model_selection_ids,
            )
            self._require_known_references(
                owner=f"AI risk '{risk.title}'",
                reference_type="agent designs",
                identifiers=set(risk.affected_agent_design_ids),
                valid_identifiers=agent_design_ids,
            )
            self._require_known_references(
                owner=f"AI risk '{risk.title}'",
                reference_type="guardrails",
                identifiers=set(risk.related_guardrail_ids),
                valid_identifiers=guardrail_ids,
            )
            self._require_known_references(
                owner=f"AI risk '{risk.title}'",
                reference_type="evaluation requirements",
                identifiers=set(risk.related_evaluation_requirement_ids),
                valid_identifiers=evaluation_requirement_ids,
            )

    def _validate_required_design_coverage(
        self,
        *,
        capability_ids: set[ArtifactId],
    ) -> None:
        """Require every capability to have model and evaluation coverage."""

        modeled_capabilities = {
            capability_id
            for requirement in self.model_requirements
            for capability_id in requirement.related_capability_ids
        }

        evaluated_capabilities = {
            capability_id
            for requirement in self.evaluation_requirements
            for capability_id in requirement.related_capability_ids
        }

        unmodeled = capability_ids.difference(modeled_capabilities)

        if unmodeled:
            self._raise_missing_reference_error(
                owner="AIArchitecture",
                reference_type="model requirement coverage for capabilities",
                identifiers=unmodeled,
            )

        unevaluated = capability_ids.difference(evaluated_capabilities)

        if unevaluated:
            self._raise_missing_reference_error(
                owner="AIArchitecture",
                reference_type="evaluation coverage for capabilities",
                identifiers=unevaluated,
            )

        rag_capability_ids = {
            capability.id
            for capability in self.capabilities
            if capability.use_case_type is AIUseCaseType.RAG
        }

        rag_designed_capabilities = {
            capability_id
            for design in self.rag_designs
            for capability_id in design.related_capability_ids
        }

        missing_rag_designs = rag_capability_ids.difference(rag_designed_capabilities)

        if missing_rag_designs:
            self._raise_missing_reference_error(
                owner="AIArchitecture",
                reference_type="RAG designs for RAG capabilities",
                identifiers=missing_rag_designs,
            )

        agentic_capability_ids = {
            capability.id
            for capability in self.capabilities
            if capability.use_case_type is AIUseCaseType.AGENTIC_AUTOMATION
        }

        workflow_capability_ids = {
            step.capability_id for workflow in self.agent_workflows for step in workflow.steps
        }

        missing_agent_workflows = agentic_capability_ids.difference(workflow_capability_ids)

        if missing_agent_workflows:
            self._raise_missing_reference_error(
                owner="AIArchitecture",
                reference_type="agent workflows for agentic capabilities",
                identifiers=missing_agent_workflows,
            )

    def _validate_decision_consistency(self) -> None:
        """Validate terminal decision metadata."""

        if self.decision == "approved" and self.open_questions:
            raise ValueError("An approved AIArchitecture cannot contain open questions.")

        if self.decision == "approved_with_assumptions" and not self.assumptions:
            raise ValueError("approved_with_assumptions requires at least one assumption.")

        if self.decision == "requires_clarification" and not self.open_questions:
            raise ValueError("requires_clarification requires at least one open question.")

        if self.decision == "cannot_proceed" and not self.limitations:
            raise ValueError("cannot_proceed requires at least one documented limitation.")

    @staticmethod
    def _require_known_references(
        *,
        owner: str,
        reference_type: str,
        identifiers: set[ArtifactId],
        valid_identifiers: set[ArtifactId],
    ) -> None:
        """Require every identifier to exist in a supplied collection."""

        missing = identifiers.difference(valid_identifiers)

        if missing:
            AIArchitecture._raise_missing_reference_error(
                owner=owner,
                reference_type=reference_type,
                identifiers=missing,
            )

    @staticmethod
    def _raise_missing_reference_error(
        *,
        owner: str,
        reference_type: str,
        identifiers: set[ArtifactId],
    ) -> None:
        """Raise a consistently formatted missing-reference error."""

        formatted = ", ".join(sorted(str(identifier) for identifier in identifiers))

        raise ValueError(f"{owner} references unknown {reference_type}: {formatted}.")

    @classmethod
    def validate_architecture_ownership(
        cls,
        *,
        ai_architecture: AIArchitecture,
        solution_architecture: object,
    ) -> None:
        """Validate ownership against SolutionArchitecture."""

        from buildwise.domain.architecture import SolutionArchitecture

        if not isinstance(solution_architecture, SolutionArchitecture):
            raise TypeError("solution_architecture must be a SolutionArchitecture instance.")

        if ai_architecture.session_id != solution_architecture.session_id:
            raise ValueError("AIArchitecture and SolutionArchitecture session IDs must match.")

        if ai_architecture.solution_architecture_id != solution_architecture.id:
            raise ValueError(
                "AIArchitecture.solution_architecture_id must match SolutionArchitecture.id."
            )

        if (
            ai_architecture.requirements_specification_id
            != solution_architecture.requirements_specification_id
        ):
            raise ValueError(
                "AIArchitecture and SolutionArchitecture must reference the "
                "same RequirementsSpecification."
            )

    @classmethod
    def validate_requirements_ownership(
        cls,
        *,
        ai_architecture: AIArchitecture,
        requirements_specification: object,
    ) -> None:
        """Validate requirement references against RequirementsSpecification."""

        from buildwise.domain.requirements import RequirementsSpecification

        if not isinstance(
            requirements_specification,
            RequirementsSpecification,
        ):
            raise TypeError(
                "requirements_specification must be a RequirementsSpecification instance."
            )

        if ai_architecture.session_id != requirements_specification.session_id:
            raise ValueError("AIArchitecture and RequirementsSpecification session IDs must match.")

        if ai_architecture.requirements_specification_id != requirements_specification.id:
            raise ValueError(
                "AIArchitecture.requirements_specification_id must match "
                "RequirementsSpecification.id."
            )

        functional_requirement_ids = {
            requirement.id for requirement in requirements_specification.functional_requirements
        }
        non_functional_requirement_ids = {
            requirement.id for requirement in requirements_specification.non_functional_requirements
        }

        valid_requirement_ids = functional_requirement_ids.union(non_functional_requirement_ids)

        referenced_requirement_ids: set[ArtifactId] = set()

        for capability in ai_architecture.capabilities:
            referenced_requirement_ids.update(capability.related_functional_requirement_ids)
            referenced_requirement_ids.update(capability.related_non_functional_requirement_ids)

        for requirement in ai_architecture.model_requirements:
            referenced_requirement_ids.update(requirement.related_requirement_ids)

        missing = referenced_requirement_ids.difference(valid_requirement_ids)

        if missing:
            cls._raise_missing_reference_error(
                owner="AIArchitecture",
                reference_type="RequirementsSpecification requirements",
                identifiers=missing,
            )
