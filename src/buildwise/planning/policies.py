"""Pure specialist-selection policy rules.

Every function in this module is a deterministic, side-effect-free
transformation of validated BuildWise domain artifacts into a selection
decision. No function here calls an LLM, touches the database, or inspects
raw prompt or model-output text. Selection is driven only by structured
booleans, enums, and categories already produced by Discovery and Product
Planning.

Functions never mutate their inputs.
"""

from __future__ import annotations

from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import (
    BudgetDecisionType,
    CapabilityType,
    RequirementPriority,
    RiskSeverity,
    SpecialistSelectionReason,
    SpecialistType,
)
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.specialist_planning import (
    BudgetDecision,
    SpecialistRecommendation,
)
from buildwise.flows.state import FlowRuntimeLimits

# Structured, boolean-valued Discovery signals that justify pulling Market &
# GTM work earlier into the Product Planning Crew. These are read from
# ``CapabilityClassification.specialist_signals`` (a slug-validated boolean mapping),
# never from raw prompt or narrative text.
_MARKET_CONTEXT_SIGNAL_KEYS = (
    "market_analysis_required",
    "competitor_analysis_required",
    "pricing_strategy_required",
    "launch_strategy_required",
    "unvalidated_commercial_assumptions",
    "evidence_backed_positioning_required",
    "competitive_category",
    "investor_ready_blueprint_requested",
)

_MARKET_RISK_CATEGORIES = frozenset({"market", "business"})

_AI_CAPABILITIES = frozenset(
    {
        CapabilityType.AI_ASSISTED,
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    }
)

_CORE_AI_CAPABILITIES = frozenset(
    {
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    }
)

_SECURITY_NFR_CATEGORIES = frozenset(
    {
        "security",
        "privacy",
        "compliance",
        "data_integrity",
    }
)

_SENSITIVE_DATA_CLASSIFICATIONS = frozenset(
    {
        "restricted",
        "sensitive_personal",
        "regulated",
    }
)

_QUALITY_NFR_CATEGORIES = frozenset(
    {
        "performance",
        "availability",
        "reliability",
        "security",
        "accessibility",
        "recoverability",
        "data_integrity",
        "compliance",
    }
)

_COMPLEX_FAILURE_EDGE_CASE_CATEGORIES = frozenset(
    {
        "concurrency",
        "partial_failure",
        "dependency_failure",
        "data_consistency",
        "state_transition",
    }
)

_HIGH_SEVERITY_RISKS = frozenset({RiskSeverity.HIGH, RiskSeverity.CRITICAL})

_EFFORT_LOW = "low"
_EFFORT_MEDIUM = "medium"
_EFFORT_HIGH = "high"


def should_include_early_market_context(
    discovery: DiscoveryResult,
    *,
    explicitly_requested: bool = False,
    explicitly_excluded: bool = False,
) -> bool:
    """Decide whether Market & GTM should join the Product Planning Crew.

    This decision happens before ``ProductPlanningResult`` exists, so it may
    only use ``DiscoveryResult`` signals. Market & GTM is never selected
    merely because "every product exists in a market" — a positive,
    structured signal is required.
    """

    if explicitly_requested:
        return True

    if explicitly_excluded:
        return False

    classification = discovery.capability_classification

    has_market_signal = any(
        classification.specialist_signals.get(key, False) for key in _MARKET_CONTEXT_SIGNAL_KEYS
    )

    if has_market_signal:
        return True

    has_material_market_risk = any(
        risk.category in _MARKET_RISK_CATEGORIES and risk.severity in _HIGH_SEVERITY_RISKS
        for risk in discovery.risks
    )

    if has_material_market_risk:
        return True

    has_weakly_defined_market = any(
        "market" in unknown.impact_areas for unknown in discovery.unknowns
    )

    return has_weakly_defined_market


def evaluate_solution_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation:
    """Evaluate Solution Architecture selection.

    Solution Architecture is required for every current BuildWise
    consultation: it is the technical foundation every other specialist and
    the final blueprint depend on.
    """

    classification = discovery.capability_classification
    requirements = product_planning.requirements

    high_effort_signals = (
        classification.real_time_processing_required
        or classification.external_integrations_expected
        or classification.regulated_domain_detected
        or len(requirements.integration_requirements) >= 3
    )

    effort = _EFFORT_HIGH if high_effort_signals else _EFFORT_MEDIUM

    return SpecialistRecommendation(
        specialist=SpecialistType.SOLUTION_ARCHITECTURE,
        required=True,
        reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
        explanation=(
            "Every BuildWise technical blueprint requires a solution "
            "architecture mapped to the validated requirements."
        ),
        estimated_effort=effort,
    )


def evaluate_ai_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    """Evaluate AI Architecture selection from structured AI signals."""

    classification = discovery.capability_classification
    product_definition = product_planning.product_definition
    requirements = product_planning.requirements

    classified_capabilities = set(classification.capabilities)
    classified_ai = bool(classified_capabilities.intersection(_AI_CAPABILITIES))
    classified_core_ai = bool(classified_capabilities.intersection(_CORE_AI_CAPABILITIES))

    mvp_feature_ids = set(product_definition.mvp_feature_ids)
    ai_enabled_mvp_feature = any(
        feature.ai_enabled
        for feature in product_definition.features
        if feature.id in mvp_feature_ids
    )

    ai_functional_requirement = any(
        requirement.category == "ai" for requirement in requirements.functional_requirements
    )

    llm_integration = any(
        requirement.integration_type == "llm_provider"
        for requirement in requirements.integration_requirements
    )

    selected = (
        classification.ai_required
        or classification.rag_required
        or classification.agents_required
        or classified_ai
        or ai_enabled_mvp_feature
        or ai_functional_requirement
        or llm_integration
    )

    if not selected:
        return None

    multiple_ai_capabilities = len(classified_capabilities.intersection(_AI_CAPABILITIES)) > 1
    effort = _EFFORT_HIGH if (classified_core_ai or multiple_ai_capabilities) else _EFFORT_MEDIUM

    return SpecialistRecommendation(
        specialist=SpecialistType.AI_ARCHITECTURE,
        required=False,
        reason=SpecialistSelectionReason.AI_CAPABILITY_REQUIRED,
        explanation=(
            "The validated capability classification, product definition, "
            "or requirements contain an AI, RAG, or agentic capability that "
            "requires dedicated AI architecture."
        ),
        estimated_effort=effort,
    )


def evaluate_security_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    """Evaluate Security Architecture selection from structured risk signals.

    Reasons are prioritized: sensitive data, then regulated domain, then
    privileged external integrations, then general high risk.
    """

    classification = discovery.capability_classification
    requirements = product_planning.requirements

    sensitive_data_requirement = any(
        requirement.contains_sensitive_data
        or requirement.subject_to_regulation
        or requirement.data_classification in _SENSITIVE_DATA_CLASSIFICATIONS
        for requirement in requirements.data_requirements
    )

    security_nfr = any(
        requirement.category in _SECURITY_NFR_CATEGORIES
        for requirement in requirements.non_functional_requirements
    )

    privileged_integration = any(
        requirement.authentication_method not in {"none", "not_decided"}
        for requirement in requirements.integration_requirements
    )

    high_security_risk = any(
        risk.category in {"security", "privacy", "compliance"}
        and risk.severity in _HIGH_SEVERITY_RISKS
        for risk in discovery.risks
    )

    selected = (
        classification.sensitive_data_detected
        or classification.regulated_domain_detected
        or sensitive_data_requirement
        or security_nfr
        or privileged_integration
        or high_security_risk
    )

    if not selected:
        return None

    high_effort = (
        classification.sensitive_data_detected
        or classification.regulated_domain_detected
        or sensitive_data_requirement
    )
    effort = _EFFORT_HIGH if high_effort else _EFFORT_MEDIUM

    if classification.sensitive_data_detected or sensitive_data_requirement:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=False,
            reason=SpecialistSelectionReason.SENSITIVE_DATA,
            explanation=(
                "Sensitive or restricted data requirements require dedicated security architecture."
            ),
            estimated_effort=effort,
        )

    if classification.regulated_domain_detected:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=False,
            reason=SpecialistSelectionReason.REGULATED_DOMAIN,
            explanation=(
                "The product operates in a regulated domain and requires "
                "dedicated security and compliance architecture."
            ),
            estimated_effort=effort,
        )

    if privileged_integration:
        return SpecialistRecommendation(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            required=False,
            reason=SpecialistSelectionReason.EXTERNAL_INTEGRATIONS,
            explanation=(
                "Authenticated or privileged external integrations require "
                "dedicated trust-boundary and access-control review."
            ),
            estimated_effort=effort,
        )

    return SpecialistRecommendation(
        specialist=SpecialistType.SECURITY_ARCHITECTURE,
        required=False,
        reason=SpecialistSelectionReason.HIGH_RISK,
        explanation=(
            "Security, privacy, compliance, or data-integrity requirements "
            "create a material risk requiring specialist review."
        ),
        estimated_effort=effort,
    )


def evaluate_qa_and_evaluation(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
    *,
    ai_selected: bool,
    security_selected: bool,
) -> SpecialistRecommendation | None:
    """Evaluate QA & Evaluation selection.

    ``security_selected`` is accepted for interface symmetry with the other
    evaluators and to make the caller's intent explicit at the call site; QA
    selection itself is driven by AI, quality, and risk signals, while the
    Security -> QA execution dependency is handled separately by
    ``execution_graph``.
    """

    requirements = product_planning.requirements

    critical_quality_requirement = any(
        requirement.priority is RequirementPriority.MUST_HAVE
        and requirement.category in _QUALITY_NFR_CATEGORIES
        for requirement in requirements.non_functional_requirements
    )

    high_risk_exists = any(risk.severity in _HIGH_SEVERITY_RISKS for risk in discovery.risks)

    complex_failure_behavior = any(
        edge_case.blocking or edge_case.category in _COMPLEX_FAILURE_EDGE_CASE_CATEGORIES
        for edge_case in requirements.edge_cases
    )

    selected = (
        ai_selected or critical_quality_requirement or high_risk_exists or complex_failure_behavior
    )

    if not selected:
        return None

    effort = (
        _EFFORT_HIGH
        if (ai_selected or high_risk_exists or complex_failure_behavior)
        else _EFFORT_MEDIUM
    )

    if ai_selected:
        return SpecialistRecommendation(
            specialist=SpecialistType.QA_AND_EVALUATION,
            required=False,
            reason=SpecialistSelectionReason.AI_CAPABILITY_REQUIRED,
            explanation=(
                "AI-generated or model-driven behavior requires a dedicated "
                "evaluation and regression strategy."
            ),
            estimated_effort=effort,
        )

    if high_risk_exists:
        return SpecialistRecommendation(
            specialist=SpecialistType.QA_AND_EVALUATION,
            required=False,
            reason=SpecialistSelectionReason.HIGH_RISK,
            explanation=(
                "High or critical Discovery risks require a dedicated QA and validation strategy."
            ),
            estimated_effort=effort,
        )

    return SpecialistRecommendation(
        specialist=SpecialistType.QA_AND_EVALUATION,
        required=False,
        reason=SpecialistSelectionReason.PRODUCT_COMPLEXITY,
        explanation=(
            "Must-have quality attributes or complex failure paths require "
            "a dedicated QA and evaluation strategy."
        ),
        estimated_effort=effort,
    )


# Specialists whose selection reason marks them as safety-critical: budget
# pressure and non-owner exclusion requests may not silently drop these.
# Solution Architecture is always protected and is handled separately.
_PROTECTED_SECURITY_REASONS = frozenset(
    {
        SpecialistSelectionReason.SENSITIVE_DATA,
        SpecialistSelectionReason.REGULATED_DOMAIN,
    }
)
_PROTECTED_QA_REASONS = frozenset(
    {
        SpecialistSelectionReason.AI_CAPABILITY_REQUIRED,
        SpecialistSelectionReason.HIGH_RISK,
    }
)

# Coarse, deliberately approximate per-specialist cost policy constants.
# These are policy thresholds, not provider pricing calculations: the
# planner must never estimate exact token or dollar usage (see PRD ยง15).
_ESTIMATED_AGENT_EXECUTIONS_PER_SPECIALIST = 1
_ESTIMATED_COST_USD_PER_SPECIALIST = 0.75

# Drop order under budget pressure: least-protected, lowest-priority first.
_BUDGET_DROP_ORDER = (
    SpecialistType.QA_AND_EVALUATION,
    SpecialistType.SECURITY_ARCHITECTURE,
    SpecialistType.AI_ARCHITECTURE,
)


def is_protected_from_exclusion(recommendation: SpecialistRecommendation) -> bool:
    """Return whether a recommendation may never be dropped for budget reasons.

    Solution Architecture is always protected. AI Architecture is protected
    once selected, since AI Architecture is only ever recommended for a
    genuine AI capability need. Security and QA are protected only when
    their selection reason itself signals a safety-critical need.
    """

    if recommendation.specialist is SpecialistType.SOLUTION_ARCHITECTURE:
        return True

    if recommendation.specialist is SpecialistType.AI_ARCHITECTURE:
        # Only a genuinely core AI capability (RAG, agentic workflow, or
        # multiple AI capabilities) is protected; a single lighter
        # AI-assisted signal may still be trimmed under budget pressure or
        # an explicit exclusion request.
        return recommendation.estimated_effort == _EFFORT_HIGH

    if recommendation.specialist is SpecialistType.SECURITY_ARCHITECTURE:
        return recommendation.reason in _PROTECTED_SECURITY_REASONS

    if recommendation.specialist is SpecialistType.QA_AND_EVALUATION:
        return recommendation.reason in _PROTECTED_QA_REASONS

    return False


def apply_budget_policy(
    recommendations: list[SpecialistRecommendation],
    *,
    limits: FlowRuntimeLimits,
    explicitly_requested: set[SpecialistType],
) -> tuple[list[SpecialistRecommendation], BudgetDecision]:
    """Apply coarse runtime-limit policy to a set of recommendations.

    This uses a small fixed per-specialist cost constant rather than any
    real token or dollar estimate, matching the coarse, non-predictive
    budget policy required by the planner. Recommendations are never
    reordered; only trimmed from the least-priority, non-protected end.
    """

    if limits.maximum_estimated_cost_usd < _ESTIMATED_COST_USD_PER_SPECIALIST:
        return (
            [],
            BudgetDecision(
                decision=BudgetDecisionType.REJECTED,
                explanation=(
                    "The consultation budget cannot fund even the mandatory "
                    "Solution Architecture specialist under the current "
                    "cost limit."
                ),
                excluded_specialists=[
                    recommendation.specialist for recommendation in recommendations
                ],
                limitations=[
                    "The requested consultation cannot be delivered safely "
                    "within the configured cost limit."
                ],
            ),
        )

    protected_specialists = {
        recommendation.specialist
        for recommendation in recommendations
        if is_protected_from_exclusion(recommendation)
        or recommendation.specialist in explicitly_requested
    }

    selected = list(recommendations)
    excluded: list[SpecialistType] = []
    limitations: list[str] = []

    def _total_agent_executions(items: list[SpecialistRecommendation]) -> int:
        return len(items) * _ESTIMATED_AGENT_EXECUTIONS_PER_SPECIALIST

    for candidate in _BUDGET_DROP_ORDER:
        if _total_agent_executions(selected) <= limits.maximum_agent_executions:
            break

        if candidate in protected_specialists:
            continue

        dropped = next(
            (
                recommendation
                for recommendation in selected
                if recommendation.specialist == candidate
            ),
            None,
        )

        if dropped is None:
            continue

        selected = [
            recommendation for recommendation in selected if recommendation.specialist != candidate
        ]
        excluded.append(candidate)
        limitations.append(
            f"{candidate.value}: omitted because of the constrained "
            "consultation budget. "
            f"{dropped.explanation}"
        )

    if _total_agent_executions(selected) <= limits.maximum_agent_executions:
        if excluded:
            decision = BudgetDecisionType.APPROVED_WITH_LIMITS
            explanation = (
                "The consultation may proceed, but one or more optional "
                "specialists were excluded to respect the configured "
                "runtime limits."
            )
        else:
            decision = BudgetDecisionType.APPROVED
            explanation = "All justified specialists fit within the configured runtime limits."

        return (
            selected,
            BudgetDecision(
                decision=decision,
                explanation=explanation,
                excluded_specialists=excluded,
                limitations=limitations,
            ),
        )

    # Every droppable, non-protected specialist has already been removed and
    # the remaining protected coverage still exceeds the runtime limits: the
    # plan is not currently safe to execute, but may become safe with more
    # budget. Protected coverage is never silently dropped.
    return (
        [],
        BudgetDecision(
            decision=BudgetDecisionType.DEFERRED,
            explanation=(
                "The specialists required for a safe and complete "
                "consultation exceed the current runtime limits. Execution "
                "is deferred rather than delivered with unsafe reduced "
                "coverage."
            ),
            excluded_specialists=[],
            limitations=[
                "Planning could not proceed because required specialist "
                "coverage exceeds the configured runtime limits. Increase "
                "the runtime limits and retry."
            ],
        ),
    )
