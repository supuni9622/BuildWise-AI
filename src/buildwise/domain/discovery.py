from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    MediumText,
    NormalizedScore,
    Percentage,
    SessionId,
    ShortText,
    Slug,
    SourceMetadata,
    generate_uuid,
    utc_now,
)
from buildwise.domain.enums import (
    CapabilityType,
    ConfidenceLevel,
    FactSourceType,
    RiskLikelihood,
    RiskSeverity,
)
from buildwise.domain.intake import ProductIdeaContext

ClarificationQuestionType = Literal[
    "free_text",
    "single_choice",
    "multiple_choice",
    "boolean",
    "integer",
    "decimal",
]

ClarificationCategory = Literal[
    "problem",
    "target_users",
    "user_needs",
    "desired_outcomes",
    "product_scope",
    "features",
    "platform",
    "business_model",
    "market",
    "timeline",
    "budget",
    "technical_constraints",
    "integrations",
    "data",
    "ai_capabilities",
    "security",
    "compliance",
    "operations",
    "success_metrics",
    "existing_product",
    "other",
]

UnknownImpactArea = Literal[
    "product",
    "business",
    "market",
    "architecture",
    "ai",
    "security",
    "qa",
    "delivery",
    "cost",
    "compliance",
]

RiskCategory = Literal[
    "product",
    "business",
    "market",
    "technical",
    "architecture",
    "ai",
    "security",
    "privacy",
    "compliance",
    "quality",
    "delivery",
    "cost",
    "operational",
]

CapabilityClassificationSource = Literal[
    "deterministic",
    "llm",
    "hybrid",
]


class KnownFact(BuildWiseModel):
    """A product fact supported directly by intake or clarification evidence.

    Known facts must be traceable to a source. Agent inference must not be
    represented as a known fact unless it has been confirmed by the user or
    another authoritative source.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    statement: MediumText
    source_type: FactSourceType = Field(
        description=(
            "Evidence origin. When set to user_provided or clarification_answer, "
            "source_reference_ids must contain at least one SourceMetadata ID."
        )
    )

    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    source_reference_ids: list[ArtifactId] = Field(
        default_factory=list,
        description=(
            "IDs of supporting SourceMetadata entries. Must be non-empty for "
            "user_provided and clarification_answer facts."
        ),
    )

    confirmed_by_user: bool = False
    discovered_at: datetime = Field(default_factory=utc_now)

    @field_validator("discovered_at")
    @classmethod
    def normalize_discovered_at(cls, value: datetime) -> datetime:
        """Require fact timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("discovered_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate evidence references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_fact_source(self) -> KnownFact:
        """Prevent derived statements from being marked as user-confirmed."""

        if self.source_type is FactSourceType.DERIVED and self.confirmed_by_user:
            raise ValueError("A derived fact cannot be marked as confirmed_by_user.")

        if (
            self.source_type
            in {
                FactSourceType.USER_PROVIDED,
                FactSourceType.CLARIFICATION_ANSWER,
            }
            and not self.source_reference_ids
        ):
            raise ValueError(
                "User-provided and clarification facts must contain at least one source reference."
            )

        return self


class Assumption(BuildWiseModel):
    """An explicit working assumption made because information is unavailable."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    statement: MediumText
    rationale: MediumText

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    requires_validation: bool = True

    validation_question: MediumText | None = None
    affected_areas: list[UnknownImpactArea] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        """Require assumption timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("affected_areas")
    @classmethod
    def ensure_unique_affected_areas(
        cls,
        value: list[UnknownImpactArea],
    ) -> list[UnknownImpactArea]:
        """Prevent duplicate impact areas."""

        if len(value) != len(set(value)):
            raise ValueError("affected_areas must contain unique values.")

        return value

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate assumption source references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_validation_requirement(self) -> Assumption:
        """Require a question when an assumption needs user validation."""

        if self.requires_validation and self.validation_question is None:
            raise ValueError("validation_question is required when requires_validation is true.")

        if not self.requires_validation and self.validation_question is not None:
            raise ValueError(
                "validation_question cannot be provided when requires_validation is false."
            )

        return self


class Unknown(BuildWiseModel):
    """A missing piece of information identified during Discovery."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    description: MediumText
    reason_missing: MediumText

    impact_areas: list[UnknownImpactArea] = Field(min_length=1)
    blocking: bool = False
    priority: int = Field(default=3, ge=1, le=5)

    can_proceed_with_assumption: bool = Field(
        default=True,
        description=(
            "Whether downstream work may proceed using a stated assumption. "
            "When true, recommended_assumption must be a non-null string; "
            "when false, recommended_assumption must be null."
        ),
    )
    recommended_assumption: MediumText | None = Field(
        default=None,
        description=(
            "The assumption that permits progress. Must be non-null exactly "
            "when can_proceed_with_assumption is true, and must be null when it is false."
        ),
    )

    clarification_required: bool = True
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("impact_areas")
    @classmethod
    def ensure_unique_impact_areas(
        cls,
        value: list[UnknownImpactArea],
    ) -> list[UnknownImpactArea]:
        """Prevent duplicate unknown impact areas."""

        if len(value) != len(set(value)):
            raise ValueError("impact_areas must contain unique values.")

        return value

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate source references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_unknown_strategy(self) -> Unknown:
        """Ensure unknown resolution behavior is internally consistent."""

        if self.blocking and not self.clarification_required:
            raise ValueError("A blocking unknown must require clarification.")

        if self.can_proceed_with_assumption and self.recommended_assumption is None:
            raise ValueError(
                "recommended_assumption is required when can_proceed_with_assumption is true."
            )

        if not self.can_proceed_with_assumption and self.recommended_assumption is not None:
            raise ValueError(
                "recommended_assumption cannot be provided when "
                "can_proceed_with_assumption is false."
            )

        return self


class DiscoveryRisk(BuildWiseModel):
    """A preliminary product risk identified during Discovery."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: RiskCategory

    severity: RiskSeverity
    likelihood: RiskLikelihood

    rationale: MediumText
    potential_impact: MediumText
    early_mitigation: MediumText | None = None

    requires_specialist_review: bool = False
    affected_capabilities: list[CapabilityType] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("affected_capabilities")
    @classmethod
    def ensure_unique_capabilities(
        cls,
        value: list[CapabilityType],
    ) -> list[CapabilityType]:
        """Prevent duplicate capability references."""

        if len(value) != len(set(value)):
            raise ValueError("affected_capabilities must be unique.")

        return value

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate risk source references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value


class CompletenessResult(BuildWiseModel):
    """Deterministic or LLM-assisted assessment of intake completeness."""

    score: NormalizedScore
    percentage: Percentage

    is_complete: bool
    can_continue: bool = Field(
        description=(
            "Whether Discovery may continue downstream. Must be false whenever "
            "blocking_unknown_keys is non-empty."
        )
    )
    clarification_required: bool = Field(
        description=(
            "Whether user clarification is required. Must be true whenever "
            "blocking_unknown_keys is non-empty, and false when is_complete is true."
        )
    )

    blocking_unknown_keys: list[Slug] = Field(
        default_factory=list,
        description=(
            "Keys of blocking Unknown entries. A non-empty list requires "
            "can_continue=false and clarification_required=true."
        ),
    )
    non_blocking_unknown_keys: list[Slug] = Field(default_factory=list)

    missing_categories: list[ClarificationCategory] = Field(
        default_factory=list,
    )
    satisfied_categories: list[ClarificationCategory] = Field(
        default_factory=list,
    )

    rationale: MediumText
    threshold: NormalizedScore = 0.75

    evaluated_at: datetime = Field(default_factory=utc_now)

    @field_validator("evaluated_at")
    @classmethod
    def normalize_evaluated_at(cls, value: datetime) -> datetime:
        """Require completeness timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator(
        "blocking_unknown_keys",
        "non_blocking_unknown_keys",
        "missing_categories",
        "satisfied_categories",
    )
    @classmethod
    def ensure_unique_values(cls, value: list[object]) -> list[object]:
        """Prevent duplicated completeness values."""

        if len(value) != len(set(value)):
            raise ValueError("Completeness result lists must be unique.")

        return value

    @model_validator(mode="after")
    def validate_completeness_state(self) -> CompletenessResult:
        """Ensure score, percentage, and decision fields agree."""

        expected_percentage = self.score * 100

        if abs(self.percentage - expected_percentage) > 0.01:
            raise ValueError("percentage must equal score multiplied by 100.")

        overlap = set(self.blocking_unknown_keys).intersection(self.non_blocking_unknown_keys)
        if overlap:
            formatted = ", ".join(sorted(overlap))
            raise ValueError(f"Unknown keys cannot be both blocking and non-blocking: {formatted}.")

        category_overlap = set(self.missing_categories).intersection(self.satisfied_categories)
        if category_overlap:
            formatted = ", ".join(sorted(category_overlap))
            raise ValueError(f"Categories cannot be both missing and satisfied: {formatted}.")

        if self.is_complete and self.score < self.threshold:
            raise ValueError("is_complete cannot be true when score is below threshold.")

        if (
            not self.is_complete
            and self.score >= self.threshold
            and not self.blocking_unknown_keys
        ):
            raise ValueError(
                "is_complete must be true when score meets the threshold "
                "and no blocking unknowns remain."
            )

        if self.blocking_unknown_keys and self.can_continue:
            raise ValueError("can_continue cannot be true while blocking unknowns remain.")

        if self.blocking_unknown_keys and not self.clarification_required:
            raise ValueError("Blocking unknowns require clarification.")

        if self.is_complete and self.clarification_required:
            raise ValueError("A complete intake cannot require clarification.")

        return self


class ClarificationQuestion(BuildWiseModel):
    """A targeted question generated to resolve one or more unknowns."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    key: Slug
    category: ClarificationCategory
    question: MediumText
    question_type: ClarificationQuestionType = Field(
        default="free_text",
        description=(
            "Question input type. Only single_choice and multiple_choice may "
            "have non-empty options or allow_other=true."
        ),
    )

    rationale: MediumText
    required: bool = True
    priority: int = Field(default=3, ge=1, le=5)

    options: list[ShortText] = Field(
        default_factory=list,
        description=(
            "Selectable answers. Provide at least two only for single_choice "
            "or multiple_choice; otherwise this must be an empty list."
        ),
    )
    allow_other: bool = Field(
        default=False,
        description=(
            "Whether a choice question accepts another answer. Must be false "
            "unless question_type is single_choice or multiple_choice."
        ),
    )

    related_unknown_ids: list[ArtifactId] = Field(min_length=1)
    affected_areas: list[UnknownImpactArea] = Field(default_factory=list)

    placeholder: ShortText | None = None
    help_text: MediumText | None = None

    @field_validator("options")
    @classmethod
    def ensure_unique_options(
        cls,
        value: list[ShortText],
    ) -> list[ShortText]:
        """Prevent duplicate selectable answers."""

        if len(value) != len(set(value)):
            raise ValueError("Clarification question options must be unique.")

        return value

    @field_validator("related_unknown_ids")
    @classmethod
    def ensure_unique_unknown_ids(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate unknown references."""

        if len(value) != len(set(value)):
            raise ValueError("related_unknown_ids must be unique.")

        return value

    @field_validator("affected_areas")
    @classmethod
    def ensure_unique_affected_areas(
        cls,
        value: list[UnknownImpactArea],
    ) -> list[UnknownImpactArea]:
        """Prevent duplicate impact areas."""

        if len(value) != len(set(value)):
            raise ValueError("affected_areas must contain unique values.")

        return value

    @model_validator(mode="after")
    def validate_question_options(self) -> ClarificationQuestion:
        """Validate option behavior for each question type."""

        choice_types = {
            "single_choice",
            "multiple_choice",
        }

        if self.question_type in choice_types and len(self.options) < 2:
            raise ValueError("Choice questions must provide at least two options.")

        if self.question_type not in choice_types and self.options:
            raise ValueError("Options may only be provided for choice questions.")

        if self.allow_other and self.question_type not in choice_types:
            raise ValueError("allow_other may only be enabled for choice questions.")

        return self


class ClarificationQuestionSet(BuildWiseModel):
    """A bounded collection of clarification questions for one Flow pause."""

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId

    round_number: int = Field(ge=1)
    questions: list[ClarificationQuestion] = Field(min_length=1, max_length=10)

    summary: MediumText
    blocking: bool

    generated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None

    @field_validator("generated_at", "expires_at")
    @classmethod
    def normalize_question_set_timestamp(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require clarification-set timestamps to be timezone-aware."""

        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Clarification question-set timestamps must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("questions")
    @classmethod
    def ensure_unique_questions(
        cls,
        value: list[ClarificationQuestion],
    ) -> list[ClarificationQuestion]:
        """Prevent duplicate question identifiers and keys."""

        question_ids = [question.id for question in value]
        question_keys = [question.key for question in value]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Clarification question IDs must be unique.")

        if len(question_keys) != len(set(question_keys)):
            raise ValueError("Clarification question keys must be unique.")

        return value

    @model_validator(mode="after")
    def validate_question_set(self) -> ClarificationQuestionSet:
        """Validate question-set timing and blocking semantics."""

        if self.expires_at is not None and self.expires_at <= self.generated_at:
            raise ValueError("expires_at must be later than generated_at.")

        contains_required_questions = any(question.required for question in self.questions)

        if self.blocking and not contains_required_questions:
            raise ValueError(
                "A blocking clarification set must contain at least one required question."
            )

        return self


class SpecialistSignals(BuildWiseModel):
    """Fixed specialist-routing signals supported by Discovery."""

    market_analysis_required: bool = False
    competitor_analysis_required: bool = False
    pricing_strategy_required: bool = False
    launch_strategy_required: bool = False
    unvalidated_commercial_assumptions: bool = False
    evidence_backed_positioning_required: bool = False
    competitive_category: bool = False
    investor_ready_blueprint_requested: bool = False

    def get(self, key: str, default: bool = False) -> bool:
        """Provide mapping-style reads for deterministic selection policies."""

        value = getattr(self, key, default)
        return value if isinstance(value, bool) else default


class CapabilityClassification(BuildWiseModel):
    """Classification of product capabilities detected during Discovery."""

    capabilities: list[CapabilityType] = Field(min_length=1)

    primary_capability: CapabilityType
    confidence: ConfidenceLevel
    confidence_score: NormalizedScore

    classification_source: CapabilityClassificationSource = "hybrid"
    rationale: MediumText

    ai_required: bool = False
    rag_required: bool = False
    agents_required: bool = False
    automation_required: bool = False
    sensitive_data_detected: bool = False
    regulated_domain_detected: bool = False
    real_time_processing_required: bool = False
    external_integrations_expected: bool = False

    specialist_signals: SpecialistSignals = Field(default_factory=SpecialistSignals)
    evidence_reference_ids: list[ArtifactId] = Field(default_factory=list)

    classified_at: datetime = Field(default_factory=utc_now)

    @field_validator("classified_at")
    @classmethod
    def normalize_classified_at(cls, value: datetime) -> datetime:
        """Require classification timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("classified_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator("capabilities")
    @classmethod
    def ensure_unique_capabilities(
        cls,
        value: list[CapabilityType],
    ) -> list[CapabilityType]:
        """Prevent duplicate capability classifications."""

        if len(value) != len(set(value)):
            raise ValueError("capabilities must contain unique values.")

        return value

    @field_validator("evidence_reference_ids")
    @classmethod
    def ensure_unique_evidence_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate classification evidence references."""

        if len(value) != len(set(value)):
            raise ValueError("evidence_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_capability_signals(self) -> CapabilityClassification:
        """Ensure explicit flags agree with classified capabilities."""

        capability_set = set(self.capabilities)

        if self.primary_capability not in capability_set:
            raise ValueError("primary_capability must be included in capabilities.")

        ai_capabilities = {
            CapabilityType.AI_ASSISTED,
            CapabilityType.AI_CORE,
            CapabilityType.RAG,
            CapabilityType.AGENTIC_WORKFLOW,
        }

        if capability_set.intersection(ai_capabilities) and not self.ai_required:
            raise ValueError("ai_required must be true when an AI capability is classified.")

        if self.rag_required and CapabilityType.RAG not in capability_set:
            raise ValueError("The RAG capability must be included when rag_required is true.")

        if self.agents_required and CapabilityType.AGENTIC_WORKFLOW not in capability_set:
            raise ValueError(
                "The agentic_workflow capability must be included when agents_required is true."
            )

        if self.automation_required and CapabilityType.AUTOMATION not in capability_set:
            raise ValueError(
                "The automation capability must be included when automation_required is true."
            )

        if self.sensitive_data_detected and CapabilityType.SENSITIVE_DATA not in capability_set:
            raise ValueError(
                "The sensitive_data capability must be included when "
                "sensitive_data_detected is true."
            )

        if self.regulated_domain_detected and CapabilityType.REGULATED not in capability_set:
            raise ValueError(
                "The regulated capability must be included when regulated_domain_detected is true."
            )

        if self.real_time_processing_required and CapabilityType.REAL_TIME not in capability_set:
            raise ValueError(
                "The real_time capability must be included when "
                "real_time_processing_required is true."
            )

        if (
            self.external_integrations_expected
            and CapabilityType.INTEGRATION_HEAVY not in capability_set
        ):
            raise ValueError(
                "The integration_heavy capability must be included when "
                "external_integrations_expected is true."
            )

        return self


class DiscoveryResult(BuildWiseModel):
    """Canonical structured output produced by the Discovery Analyst.

    This result separates evidence-backed facts, working assumptions, missing
    information, preliminary risks, completeness, clarification questions,
    and capability classification.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId

    idea_context: ProductIdeaContext

    summary: MediumText
    problem_interpretation: MediumText
    target_user_interpretation: MediumText
    desired_outcome_interpretation: MediumText

    known_facts: list[KnownFact] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    unknowns: list[Unknown] = Field(default_factory=list)
    risks: list[DiscoveryRisk] = Field(default_factory=list)

    completeness: CompletenessResult
    clarification_questions: ClarificationQuestionSet | None = None
    capability_classification: CapabilityClassification

    recommended_next_step: Literal[
        "request_clarification",
        "continue_to_product_definition",
        "continue_with_limitations",
        "fail_discovery",
    ]

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    discovered_at: datetime = Field(default_factory=utc_now)

    @field_validator("discovered_at")
    @classmethod
    def normalize_discovered_at(cls, value: datetime) -> datetime:
        """Require Discovery timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("discovered_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator(
        "known_facts",
        "assumptions",
        "unknowns",
        "risks",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate discovery artifact identifiers."""

        ids = [item.id for item in value]

        if len(ids) != len(set(ids)):
            raise ValueError("Discovery artifact IDs must be unique within each collection.")

        return value

    @field_validator("limitations")
    @classmethod
    def ensure_unique_limitations(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate limitation statements."""

        if len(value) != len(set(value)):
            raise ValueError("limitations must contain unique values.")

        return value

    @model_validator(mode="after")
    def validate_discovery_result(self) -> DiscoveryResult:
        """Validate session ownership and Discovery routing decisions."""

        if self.idea_context.session_id != self.session_id:
            raise ValueError("idea_context.session_id must match Discovery session_id.")

        unknown_ids = {unknown.id for unknown in self.unknowns}

        if self.clarification_questions is not None:
            if self.clarification_questions.session_id != self.session_id:
                raise ValueError(
                    "clarification_questions.session_id must match Discovery session_id."
                )

            referenced_unknown_ids = {
                unknown_id
                for question in self.clarification_questions.questions
                for unknown_id in question.related_unknown_ids
            }

            missing_unknown_ids = referenced_unknown_ids.difference(unknown_ids)

            if missing_unknown_ids:
                formatted = ", ".join(sorted(str(identifier) for identifier in missing_unknown_ids))
                raise ValueError(
                    "Clarification questions reference unknown IDs that are "
                    f"not present in DiscoveryResult: {formatted}."
                )

        if self.completeness.clarification_required:
            if self.clarification_questions is None:
                raise ValueError(
                    "clarification_questions are required when completeness requires clarification."
                )

            if self.recommended_next_step != "request_clarification":
                raise ValueError(
                    "The recommended next step must request clarification when "
                    "clarification is required."
                )

        if (
            not self.completeness.clarification_required
            and self.recommended_next_step == "request_clarification"
        ):
            raise ValueError(
                "Clarification cannot be recommended when completeness does not require it."
            )

        if (
            self.recommended_next_step == "continue_to_product_definition"
            and not self.completeness.can_continue
        ):
            raise ValueError(
                "Discovery cannot continue to product definition when can_continue is false."
            )

        if self.recommended_next_step == "continue_with_limitations" and not self.limitations:
            raise ValueError("continue_with_limitations requires at least one limitation.")

        if self.recommended_next_step == "fail_discovery" and self.completeness.can_continue:
            raise ValueError("Discovery should not fail while completeness allows continuation.")

        if self.completeness.is_complete and self.unknowns:
            blocking_unknowns = [unknown for unknown in self.unknowns if unknown.blocking]

            if blocking_unknowns:
                raise ValueError("A complete Discovery result cannot contain blocking unknowns.")

        fact_keys = {fact.key for fact in self.known_facts}
        assumption_keys = {assumption.key for assumption in self.assumptions}

        overlapping_keys = fact_keys.intersection(assumption_keys)

        if overlapping_keys:
            formatted = ", ".join(sorted(overlapping_keys))
            raise ValueError(
                f"A discovery key cannot be both a known fact and an assumption: {formatted}."
            )

        return self


class DiscoveryCompletenessRefinement(BuildWiseModel):
    """Evidence fields used to derive a consistent completeness decision."""

    score: NormalizedScore
    blocking_unknown_keys: list[Slug] = Field(default_factory=list)
    non_blocking_unknown_keys: list[Slug] = Field(default_factory=list)
    missing_categories: list[ClarificationCategory] = Field(default_factory=list)
    satisfied_categories: list[ClarificationCategory] = Field(default_factory=list)
    rationale: MediumText
    threshold: NormalizedScore = 0.75
    evaluated_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_result(
        cls,
        result: CompletenessResult,
    ) -> DiscoveryCompletenessRefinement:
        """Extract only non-derived completeness evidence from a full result."""

        return cls(
            score=result.score,
            blocking_unknown_keys=result.blocking_unknown_keys,
            non_blocking_unknown_keys=result.non_blocking_unknown_keys,
            missing_categories=result.missing_categories,
            satisfied_categories=result.satisfied_categories,
            rationale=result.rationale,
            threshold=result.threshold,
            evaluated_at=result.evaluated_at,
        )

    def to_result(self) -> CompletenessResult:
        """Derive decision booleans and percentage without LLM discretion."""

        has_blockers = bool(self.blocking_unknown_keys)
        is_complete = self.score >= self.threshold and not has_blockers
        return CompletenessResult(
            score=self.score,
            percentage=self.score * 100,
            is_complete=is_complete,
            can_continue=not has_blockers,
            clarification_required=has_blockers,
            blocking_unknown_keys=self.blocking_unknown_keys,
            non_blocking_unknown_keys=self.non_blocking_unknown_keys,
            missing_categories=self.missing_categories,
            satisfied_categories=self.satisfied_categories,
            rationale=self.rationale,
            threshold=self.threshold,
            evaluated_at=self.evaluated_at,
        )


class DiscoveryRefinement(BuildWiseModel):
    """Small clarification-time update merged into an accepted DiscoveryResult."""

    unknowns: list[Unknown] = Field(default_factory=list)
    completeness: DiscoveryCompletenessRefinement
    clarification_questions: ClarificationQuestionSet | None = None
    recommended_next_step: Literal[
        "request_clarification",
        "continue_to_product_definition",
        "continue_with_limitations",
        "fail_discovery",
    ]
    limitations: list[MediumText] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    @model_validator(mode="after")
    def validate_refinement_route(self) -> DiscoveryRefinement:
        clarification_required = bool(self.completeness.blocking_unknown_keys)
        if clarification_required:
            if self.clarification_questions is None:
                raise ValueError(
                    "clarification_questions are required when refinement "
                    "requires clarification."
                )
            if self.recommended_next_step != "request_clarification":
                raise ValueError(
                    "A refinement requiring clarification must request clarification."
                )
        elif self.recommended_next_step == "request_clarification":
            raise ValueError(
                "Clarification cannot be requested when it is not required."
            )
        if self.recommended_next_step == "continue_with_limitations" and not self.limitations:
            raise ValueError("continue_with_limitations requires at least one limitation.")
        return self
