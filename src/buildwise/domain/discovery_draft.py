"""Compact LLM contract and deterministic assembly for initial Discovery."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from buildwise.domain.common import (
    BuildWiseModel,
    MediumText,
    NormalizedScore,
    SessionId,
    ShortText,
    Slug,
    SourceMetadata,
)
from buildwise.domain.discovery import (
    Assumption,
    CapabilityClassification,
    ClarificationCategory,
    ClarificationQuestion,
    ClarificationQuestionSet,
    ClarificationQuestionType,
    DiscoveryResult,
    DiscoveryRisk,
    KnownFact,
    RiskCategory,
    SpecialistSignals,
    Unknown,
    UnknownImpactArea,
)
from buildwise.domain.enums import (
    CapabilityType,
    ConfidenceLevel,
    FactSourceType,
    RiskLikelihood,
    RiskSeverity,
)
from buildwise.domain.intake import (
    ProductIdeaContext,
    ProductIdeaRequest,
    ValidatedProductIdea,
)


class KnownFactDraft(BuildWiseModel):
    """Semantic fact without generated identity, timestamps, or reference IDs."""

    key: Slug
    statement: MediumText
    source_type: FactSourceType
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    confirmed_by_user: bool = False


class AssumptionDraft(BuildWiseModel):
    """Semantic working assumption without operational metadata."""

    key: Slug
    statement: MediumText
    rationale: MediumText
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    requires_validation: bool = True
    validation_question: MediumText | None = None
    affected_areas: list[UnknownImpactArea] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_validation_question(self) -> AssumptionDraft:
        if self.requires_validation and self.validation_question is None:
            raise ValueError("validation_question is required when requires_validation is true.")
        if not self.requires_validation and self.validation_question is not None:
            raise ValueError(
                "validation_question must be absent when requires_validation is false."
            )
        return self


class UnknownDraft(BuildWiseModel):
    """Semantic unknown whose identity and routing fields are derived later."""

    key: Slug
    description: MediumText
    reason_missing: MediumText
    impact_areas: list[UnknownImpactArea] = Field(min_length=1)
    blocking: bool = False
    priority: int = Field(default=3, ge=1, le=5)
    can_proceed_with_assumption: bool = True
    recommended_assumption: MediumText | None = None

    @model_validator(mode="after")
    def validate_assumption_strategy(self) -> UnknownDraft:
        if self.can_proceed_with_assumption and self.recommended_assumption is None:
            raise ValueError("recommended_assumption is required when progress is allowed.")
        if not self.can_proceed_with_assumption and self.recommended_assumption is not None:
            raise ValueError("recommended_assumption must be absent when progress is not allowed.")
        return self


class DiscoveryRiskDraft(BuildWiseModel):
    """Semantic preliminary risk without generated identity or references."""

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


class DiscoveryCompletenessDraft(BuildWiseModel):
    """Completeness evidence from which all decision fields are derived."""

    score: NormalizedScore
    missing_categories: list[ClarificationCategory] = Field(default_factory=list)
    satisfied_categories: list[ClarificationCategory] = Field(default_factory=list)
    rationale: MediumText
    threshold: NormalizedScore = 0.75


class ClarificationQuestionDraft(BuildWiseModel):
    """Question linked to unknown keys rather than generated UUIDs."""

    key: Slug
    category: ClarificationCategory
    question: MediumText
    question_type: ClarificationQuestionType = "free_text"
    rationale: MediumText
    required: bool = True
    priority: int = Field(default=3, ge=1, le=5)
    options: list[ShortText] = Field(default_factory=list)
    allow_other: bool = False
    related_unknown_keys: list[Slug] = Field(min_length=1)
    affected_areas: list[UnknownImpactArea] = Field(default_factory=list)
    placeholder: ShortText | None = None
    help_text: MediumText | None = None

    @model_validator(mode="after")
    def validate_options(self) -> ClarificationQuestionDraft:
        is_choice = self.question_type in {"single_choice", "multiple_choice"}
        if is_choice and len(self.options) < 2:
            raise ValueError("Choice questions require at least two options.")
        if not is_choice and (self.options or self.allow_other):
            raise ValueError("Only choice questions may provide options or allow_other.")
        return self


class ClarificationQuestionSetDraft(BuildWiseModel):
    """Semantic clarification set without ownership IDs or timestamps."""

    round_number: int = Field(ge=1)
    questions: list[ClarificationQuestionDraft] = Field(min_length=1, max_length=10)
    summary: MediumText
    blocking: bool


class CapabilitySignalsDraft(BuildWiseModel):
    """Capability decisions with companion booleans derived during assembly."""

    capabilities: list[CapabilityType] = Field(min_length=1)
    primary_capability: CapabilityType
    confidence: ConfidenceLevel
    confidence_score: NormalizedScore
    rationale: MediumText
    specialist_signals: SpecialistSignals = Field(default_factory=SpecialistSignals)

    @model_validator(mode="before")
    @classmethod
    def include_primary_capability(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        capabilities = list(normalized.get("capabilities") or [])
        primary = normalized.get("primary_capability")
        if primary is not None:
            capabilities.append(primary)
        normalized["capabilities"] = list(dict.fromkeys(capabilities))
        return normalized


class DiscoveryDraft(BuildWiseModel):
    """Compact initial Discovery contract generated by the LLM."""

    title: ShortText
    summary: MediumText
    problem_interpretation: MediumText
    target_user_interpretation: MediumText
    desired_outcome_interpretation: MediumText
    target_users: list[ShortText] = Field(min_length=1)
    desired_outcomes: list[MediumText] = Field(min_length=1)

    known_facts: list[KnownFactDraft] = Field(default_factory=list)
    assumptions: list[AssumptionDraft] = Field(default_factory=list)
    unknowns: list[UnknownDraft] = Field(default_factory=list)
    risks: list[DiscoveryRiskDraft] = Field(default_factory=list)
    completeness: DiscoveryCompletenessDraft
    clarification_questions: ClarificationQuestionSetDraft | None = None
    capability_signals: CapabilitySignalsDraft
    limitations: list[MediumText] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    @model_validator(mode="after")
    def validate_semantic_consistency(self) -> DiscoveryDraft:
        unknown_keys = [unknown.key for unknown in self.unknowns]
        if len(unknown_keys) != len(set(unknown_keys)):
            raise ValueError("Unknown keys must be unique.")

        fact_keys = {fact.key for fact in self.known_facts}
        assumption_keys = {assumption.key for assumption in self.assumptions}
        if overlap := fact_keys.intersection(assumption_keys):
            raise ValueError(
                "A key cannot be both a known fact and an assumption: " + ", ".join(sorted(overlap))
            )

        blockers = {unknown.key for unknown in self.unknowns if unknown.blocking}
        if blockers and self.clarification_questions is None:
            raise ValueError("Clarification questions are required for blocking unknowns.")
        if self.clarification_questions is not None:
            referenced = {
                key
                for question in self.clarification_questions.questions
                for key in question.related_unknown_keys
            }
            missing = referenced.difference(unknown_keys)
            if missing:
                raise ValueError(
                    "Clarification questions reference missing unknown keys: "
                    + ", ".join(sorted(missing))
                )
        return self


def assemble_discovery_result(
    draft: DiscoveryDraft,
    *,
    session_id: SessionId,
    product_idea: ProductIdeaRequest,
) -> DiscoveryResult:
    """Build the canonical Discovery artifact from semantic model decisions."""

    intake_source = SourceMetadata(
        reference_type="user_input",
        source_key="product_idea_request",
        title="Submitted product idea",
        description="The validated product idea submitted for this consultation.",
        confidence=ConfidenceLevel.HIGH,
        retrieved_at=product_idea.submitted_at,
    )
    source_ids = [intake_source.id]
    validated_idea = ValidatedProductIdea(
        session_id=session_id,
        title=product_idea.title or draft.title,
        summary=draft.summary,
        original_idea=product_idea.idea,
        normalized_problem_statement=(
            product_idea.problem_statement or draft.problem_interpretation
        ),
        target_users=product_idea.target_users or draft.target_users,
        desired_outcomes=product_idea.desired_outcomes or draft.desired_outcomes,
        requested_features=product_idea.known_features,
        constraints=product_idea.known_constraints,
        user_assumptions=product_idea.existing_assumptions,
        target_platforms=product_idea.target_platforms,
        delivery_expectation=product_idea.delivery_expectation,
        idea_maturity=product_idea.idea_maturity,
        preferred_timeline=product_idea.preferred_timeline,
        estimated_budget=product_idea.estimated_budget,
        industry=product_idea.industry,
        target_market=product_idea.target_market,
        geographic_scope=product_idea.geographic_scope,
        existing_product=product_idea.existing_product,
        existing_product_description=product_idea.existing_product_description,
        requests_ai_capabilities=product_idea.requests_ai_capabilities,
        handles_sensitive_data=product_idea.handles_sensitive_data,
        regulated_domain=product_idea.regulated_domain,
        additional_context=product_idea.additional_context,
        validation_confidence=draft.confidence,
        validation_notes=draft.limitations,
        source_metadata=[intake_source],
    )

    unknowns = [
        Unknown(
            key=item.key,
            description=item.description,
            reason_missing=item.reason_missing,
            impact_areas=item.impact_areas,
            blocking=item.blocking,
            priority=item.priority,
            can_proceed_with_assumption=item.can_proceed_with_assumption,
            recommended_assumption=item.recommended_assumption,
            clarification_required=item.blocking,
        )
        for item in draft.unknowns
    ]
    unknown_by_key = {unknown.key: unknown for unknown in unknowns}
    blocking_keys = [unknown.key for unknown in unknowns if unknown.blocking]
    non_blocking_keys = [unknown.key for unknown in unknowns if not unknown.blocking]

    questions = _assemble_questions(
        draft.clarification_questions,
        session_id=session_id,
        unknown_by_key=unknown_by_key,
        has_blockers=bool(blocking_keys),
    )

    capability_set = set(draft.capability_signals.capabilities)
    ai_capabilities = {
        CapabilityType.AI_ASSISTED,
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    }
    classification = CapabilityClassification(
        capabilities=draft.capability_signals.capabilities,
        primary_capability=draft.capability_signals.primary_capability,
        confidence=draft.capability_signals.confidence,
        confidence_score=draft.capability_signals.confidence_score,
        classification_source="hybrid",
        rationale=draft.capability_signals.rationale,
        ai_required=bool(capability_set.intersection(ai_capabilities)),
        rag_required=CapabilityType.RAG in capability_set,
        agents_required=CapabilityType.AGENTIC_WORKFLOW in capability_set,
        automation_required=CapabilityType.AUTOMATION in capability_set,
        sensitive_data_detected=CapabilityType.SENSITIVE_DATA in capability_set,
        regulated_domain_detected=CapabilityType.REGULATED in capability_set,
        real_time_processing_required=CapabilityType.REAL_TIME in capability_set,
        external_integrations_expected=(CapabilityType.INTEGRATION_HEAVY in capability_set),
        specialist_signals=draft.capability_signals.specialist_signals,
        evidence_reference_ids=source_ids,
    )

    has_blockers = bool(blocking_keys)
    completeness = {
        "score": draft.completeness.score,
        "percentage": draft.completeness.score * 100,
        "is_complete": (
            draft.completeness.score >= draft.completeness.threshold and not has_blockers
        ),
        "can_continue": not has_blockers,
        "clarification_required": has_blockers,
        "blocking_unknown_keys": blocking_keys,
        "non_blocking_unknown_keys": non_blocking_keys,
        "missing_categories": draft.completeness.missing_categories,
        "satisfied_categories": draft.completeness.satisfied_categories,
        "rationale": draft.completeness.rationale,
        "threshold": draft.completeness.threshold,
    }
    route: Literal[
        "request_clarification",
        "continue_to_product_definition",
        "continue_with_limitations",
        "fail_discovery",
    ] = (
        "request_clarification"
        if has_blockers
        else (
            "continue_with_limitations" if draft.limitations else "continue_to_product_definition"
        )
    )

    return DiscoveryResult(
        session_id=session_id,
        idea_context=ProductIdeaContext(
            session_id=session_id,
            validated_idea=validated_idea,
            unresolved_context_keys=[unknown.key for unknown in unknowns],
            source_metadata=[intake_source],
        ),
        summary=draft.summary,
        problem_interpretation=draft.problem_interpretation,
        target_user_interpretation=draft.target_user_interpretation,
        desired_outcome_interpretation=draft.desired_outcome_interpretation,
        known_facts=[
            KnownFact(
                key=item.key,
                statement=item.statement,
                source_type=item.source_type,
                confidence=item.confidence,
                source_reference_ids=(
                    source_ids
                    if item.source_type
                    in {
                        FactSourceType.USER_PROVIDED,
                        FactSourceType.CLARIFICATION_ANSWER,
                    }
                    else []
                ),
                confirmed_by_user=item.confirmed_by_user,
            )
            for item in draft.known_facts
        ],
        assumptions=[
            Assumption(
                key=item.key,
                statement=item.statement,
                rationale=item.rationale,
                confidence=item.confidence,
                requires_validation=item.requires_validation,
                validation_question=item.validation_question,
                affected_areas=item.affected_areas,
            )
            for item in draft.assumptions
        ],
        unknowns=unknowns,
        risks=[
            DiscoveryRisk(
                title=item.title,
                description=item.description,
                category=item.category,
                severity=item.severity,
                likelihood=item.likelihood,
                rationale=item.rationale,
                potential_impact=item.potential_impact,
                early_mitigation=item.early_mitigation,
                requires_specialist_review=item.requires_specialist_review,
                affected_capabilities=item.affected_capabilities,
            )
            for item in draft.risks
        ],
        completeness=completeness,
        clarification_questions=questions,
        capability_classification=classification,
        recommended_next_step=route,
        limitations=draft.limitations,
        source_metadata=[intake_source],
        confidence=draft.confidence,
        confidence_score=draft.confidence_score,
    )


def _assemble_questions(
    draft: ClarificationQuestionSetDraft | None,
    *,
    session_id: SessionId,
    unknown_by_key: dict[Slug, Unknown],
    has_blockers: bool,
) -> ClarificationQuestionSet | None:
    if not has_blockers or draft is None:
        return None
    return ClarificationQuestionSet(
        session_id=session_id,
        round_number=draft.round_number,
        questions=[
            ClarificationQuestion(
                key=item.key,
                category=item.category,
                question=item.question,
                question_type=item.question_type,
                rationale=item.rationale,
                required=item.required,
                priority=item.priority,
                options=item.options,
                allow_other=item.allow_other,
                related_unknown_ids=[unknown_by_key[key].id for key in item.related_unknown_keys],
                affected_areas=item.affected_areas,
                placeholder=item.placeholder,
                help_text=item.help_text,
            )
            for item in draft.questions
        ],
        summary=draft.summary,
        blocking=draft.blocking,
    )
