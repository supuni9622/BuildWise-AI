"""Pure, deterministic specialist-selection rules.

Every function here is a pure function of its structured inputs: no I/O, no
LLM calls, no mutation. Selection reads only structured signals — the
``discovery.capability_classification`` flags/enum values and the
``specialist_signals`` controlled vocabulary the Discovery Task instructs
the agent to populate (see ``buildwisev2.tasks.discovery``) — never raw
prose via keyword matching, per the planner PRD's goal to avoid
keyword-only classification.
"""

from __future__ import annotations

from buildwisev2.domain.common import CapabilityType, FlowRuntimeLimits, SpecialistType
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.planning_results import ProductPlanningResult
from buildwisev2.domain.requirements import NFRCategory, RequirementPriority
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    BudgetDecisionType,
    EffortLevel,
    SpecialistRecommendation,
    SpecialistSelectionReason,
)

# Specialists are dropped in this order when budget requires trimming —
# preserves the priority order from the planner PRD section 15.1: Solution
# and mandatory Security/AI/QA are never optional, so only the remaining
# optional recommendations are candidates, least-preserved first.
_OPTIONAL_DROP_ORDER = (
    SpecialistType.QA_AND_EVALUATION,
    SpecialistType.AI_ARCHITECTURE,
    SpecialistType.SECURITY_ARCHITECTURE,
)

_AI_CAPABILITY_TYPES = {
    CapabilityType.AI_ASSISTED,
    CapabilityType.AI_CORE,
    CapabilityType.RAG,
    CapabilityType.AGENTIC_WORKFLOW,
}
_HIGH_EFFORT_AI_TYPES = {CapabilityType.RAG, CapabilityType.AGENTIC_WORKFLOW}
_MUST_HAVE_QUALITY_NFR_CATEGORIES = {
    NFRCategory.PERFORMANCE,
    NFRCategory.AVAILABILITY,
    NFRCategory.RELIABILITY,
    NFRCategory.SECURITY,
    NFRCategory.ACCESSIBILITY,
    NFRCategory.RECOVERABILITY,
    NFRCategory.DATA_INTEGRITY,
    NFRCategory.COMPLIANCE,
}


def should_include_early_market_context(
    discovery: DiscoveryResult,
    *,
    explicitly_requested: bool = False,
) -> bool:
    """Decide, before Product Planning Crew construction, whether to include
    the Market & GTM Strategist in that Crew's early-market-context mode.
    """

    if explicitly_requested:
        return True
    return (
        SpecialistType.MARKET_AND_GTM.value
        in discovery.capability_classification.specialist_signals
    )


def evaluate_solution_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation:
    """Solution Architecture is mandatory for the current BuildWise MVP."""

    effort = (
        EffortLevel.HIGH
        if (
            discovery.capability_classification.real_time_processing_required
            or discovery.capability_classification.external_integrations_expected
            or discovery.capability_classification.regulated_domain_detected
        )
        else EffortLevel.MEDIUM
    )
    return SpecialistRecommendation(
        specialist=SpecialistType.SOLUTION_ARCHITECTURE,
        required=True,
        reason=SpecialistSelectionReason.MANDATORY,
        explanation=(
            "Every build-ready BuildWise blueprint requires a general solution architecture."
        ),
        estimated_effort=effort,
    )


def evaluate_ai_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    classification = discovery.capability_classification
    ai_capabilities_present = _AI_CAPABILITY_TYPES.intersection(classification.capabilities)
    ai_feature_signal = any(
        feature.ai_enabled
        for feature in product_planning.product_definition.features
        if feature.id in product_planning.product_definition.mvp_feature_ids
    )
    ai_requirement_signal = any(
        requirement.category == "ai"
        for requirement in product_planning.requirements.functional_requirements
    )

    if not (
        ai_capabilities_present
        or classification.ai_required
        or classification.rag_required
        or classification.agents_required
        or ai_feature_signal
        or ai_requirement_signal
    ):
        return None

    is_core = (
        CapabilityType.AI_CORE in classification.capabilities or classification.agents_required
    )
    high_effort = (
        bool(_HIGH_EFFORT_AI_TYPES.intersection(classification.capabilities))
        or len(ai_capabilities_present) > 1
    )

    return SpecialistRecommendation(
        specialist=SpecialistType.AI_ARCHITECTURE,
        required=is_core,
        reason=SpecialistSelectionReason.AI_CAPABILITY,
        explanation=(
            "The product has a core AI capability that requires dedicated AI design."
            if is_core
            else "The product has an AI-assisted capability that requires AI design."
        ),
        estimated_effort=EffortLevel.HIGH if high_effort else EffortLevel.MEDIUM,
    )


def evaluate_security_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    classification = discovery.capability_classification
    has_privileged_integration = any(
        integration.is_privileged
        for integration in product_planning.requirements.integration_requirements
    )

    if classification.sensitive_data_detected:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=True,
            reason=SpecialistSelectionReason.SENSITIVE_DATA,
            explanation=(
                "Discovery detected sensitive data; a dedicated security architecture is mandatory."
            ),
            estimated_effort=(
                EffortLevel.HIGH if classification.regulated_domain_detected else EffortLevel.MEDIUM
            ),
        )
    if classification.regulated_domain_detected:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=True,
            reason=SpecialistSelectionReason.REGULATED_DOMAIN,
            explanation=(
                "Discovery detected a regulated domain; a dedicated security architecture "
                "is mandatory."
            ),
            estimated_effort=EffortLevel.HIGH,
        )
    if has_privileged_integration or classification.external_integrations_expected:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=False,
            reason=SpecialistSelectionReason.EXTERNAL_INTEGRATIONS,
            explanation=(
                "The product has privileged or external integrations that warrant security review."
            ),
            estimated_effort=EffortLevel.MEDIUM,
        )
    if SpecialistType.SECURITY_ARCHITECTURE.value in classification.specialist_signals:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=False,
            reason=SpecialistSelectionReason.HIGH_RISK,
            explanation="Discovery flagged a security-relevant signal for this product.",
            estimated_effort=EffortLevel.MEDIUM,
        )
    return None


def evaluate_qa_and_evaluation(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
    *,
    ai_selected: bool,
    security_selected: bool,
) -> SpecialistRecommendation | None:
    if ai_selected:
        return SpecialistRecommendation(
            specialist=SpecialistType.QA_AND_EVALUATION,
            required=True,
            reason=SpecialistSelectionReason.AI_CAPABILITY,
            explanation=(
                "AI Architecture was selected; user-visible AI outputs require an evaluation plan."
            ),
            estimated_effort=EffortLevel.HIGH,
        )

    has_must_have_quality_nfr = any(
        requirement.priority == RequirementPriority.MUST_HAVE
        and requirement.category in _MUST_HAVE_QUALITY_NFR_CATEGORIES
        for requirement in product_planning.requirements.non_functional_requirements
    )
    has_blocking_edge_case = any(
        edge_case.blocking for edge_case in product_planning.requirements.edge_cases
    )

    if has_must_have_quality_nfr or has_blocking_edge_case:
        return SpecialistRecommendation(
            specialist=SpecialistType.QA_AND_EVALUATION,
            required=False,
            reason=SpecialistSelectionReason.QUALITY_REQUIREMENT,
            explanation=(
                "Must-have quality requirements or blocking edge cases require a dedicated QA plan."
            ),
            estimated_effort=EffortLevel.MEDIUM,
        )
    if security_selected:
        return SpecialistRecommendation(
            specialist=SpecialistType.QA_AND_EVALUATION,
            required=False,
            reason=SpecialistSelectionReason.QUALITY_REQUIREMENT,
            explanation=(
                "Security Architecture was selected; its controls require validation coverage."
            ),
            estimated_effort=EffortLevel.MEDIUM,
        )
    return None


def apply_budget_policy(
    recommendations: list[SpecialistRecommendation],
    *,
    limits: FlowRuntimeLimits,
    explicitly_requested: set[SpecialistType],
) -> tuple[list[SpecialistRecommendation], BudgetDecision]:
    """Trim optional recommendations, never mandatory ones, to fit coarse limits.

    This is a coarse policy gate, not a token/dollar estimator: it compares
    the number of recommended specialist agents against
    ``limits.maximum_agent_executions`` (each specialist Crew execution
    consumes at least one agent execution).
    """

    if len(recommendations) <= limits.maximum_agent_executions:
        return recommendations, BudgetDecision(
            decision=BudgetDecisionType.APPROVED,
            explanation="All recommended specialists fit within the session's execution budget.",
        )

    kept = {rec.specialist: rec for rec in recommendations}
    excluded: list[SpecialistType] = []
    limitations: list[str] = []

    for specialist in _OPTIONAL_DROP_ORDER:
        if len(kept) <= limits.maximum_agent_executions:
            break
        rec = kept.get(specialist)
        if rec is None or rec.required or specialist in explicitly_requested:
            continue
        del kept[specialist]
        excluded.append(specialist)
        limitations.append(
            f"{specialist.value} was omitted from this consultation because of the "
            "constrained execution budget for this session."
        )

    if len(kept) > limits.maximum_agent_executions:
        return recommendations, BudgetDecision(
            decision=BudgetDecisionType.DEFERRED,
            explanation=(
                "The mandatory specialist coverage for this consultation exceeds the "
                "session's execution budget even after dropping every optional specialist. "
                "Increase the budget or reduce consultation scope before continuing."
            ),
            excluded_specialists=excluded,
            limitations=limitations,
        )

    if excluded:
        return recommendations, BudgetDecision(
            decision=BudgetDecisionType.APPROVED_WITH_LIMITS,
            explanation=(
                "Some optional specialists were omitted to fit the session's execution budget."
            ),
            excluded_specialists=excluded,
            limitations=limitations,
        )

    return recommendations, BudgetDecision(
        decision=BudgetDecisionType.APPROVED,
        explanation="All recommended specialists fit within the session's execution budget.",
    )
