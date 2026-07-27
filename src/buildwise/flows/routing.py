from __future__ import annotations

from enum import StrEnum

from buildwise.domain.common import MediumText
from buildwise.domain.discovery import CapabilityClassification, DiscoveryResult
from buildwise.domain.enums import (
    BudgetDecisionType,
    CapabilityType,
    DependencyType,
    ExecutionMode,
    RequirementPriority,
    RiskSeverity,
    SessionStage,
    SessionStatus,
    SpecialistSelectionReason,
    SpecialistType,
)
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.specialist_planning import (
    BudgetDecision,
    SpecialistDependency,
    SpecialistExecutionGroup,
    SpecialistExecutionPlan,
    SpecialistRecommendation,
)
from buildwise.flows.state import BuildWiseFlowState


class FlowRoute(StrEnum):
    """Canonical route labels emitted by BuildWise CrewAI Flow routers.

    CrewAI router methods return strings. Using a StrEnum keeps those labels
    centralized, typed, and safe to reference from matching @listen methods.
    """

    REQUEST_CLARIFICATION = "request_clarification"
    RUN_DISCOVERY = "run_discovery"
    RUN_PRODUCT_DEFINITION = "run_product_definition"
    RUN_REQUIREMENTS = "run_requirements"
    PLAN_SPECIALISTS = "plan_specialists"
    RUN_SPECIALISTS = "run_specialists"
    RUN_LEAD_REVIEW = "run_lead_review"
    RUN_TARGETED_REVISION = "run_targeted_revision"
    ASSEMBLE_BLUEPRINT = "assemble_blueprint"
    COMPLETE_FLOW = "complete_flow"
    FAIL_FLOW = "fail_flow"


def route_after_discovery(state: BuildWiseFlowState) -> FlowRoute:
    """Choose the next Flow route after Discovery completes.

    The Discovery Crew produces the semantic assessment. This function makes
    the actual application-level route decision deterministically from that
    structured output.
    """

    discovery = _require_discovery_result(state)

    if discovery.recommended_next_step == "fail_discovery":
        return FlowRoute.FAIL_FLOW

    if (
        discovery.completeness.clarification_required
        or discovery.recommended_next_step == "request_clarification"
    ):
        return FlowRoute.REQUEST_CLARIFICATION

    if discovery.recommended_next_step in {
        "continue_to_product_definition",
        "continue_with_limitations",
    }:
        return FlowRoute.RUN_PRODUCT_DEFINITION

    raise ValueError("DiscoveryResult contains an unsupported next-step decision.")


def route_after_clarification(state: BuildWiseFlowState) -> FlowRoute:
    """Route a resumed clarification session back through Discovery.

    Clarification changes the product context. Discovery must run again to
    recalculate facts, assumptions, unknowns, completeness, and capability
    classification before downstream work continues.
    """

    if state.status is not SessionStatus.RESUMING:
        raise ValueError("Clarification routing requires a Flow in resuming status.")

    if state.stage is not SessionStage.CLARIFICATION:
        raise ValueError("Clarification routing requires the clarification stage.")

    if not state.clarification_answers:
        raise ValueError("Clarification routing requires submitted answers.")

    return FlowRoute.RUN_DISCOVERY


def route_after_product_definition(
    state: BuildWiseFlowState,
) -> FlowRoute:
    """Choose the next route after Product Definition."""

    product_definition = state.product_definition

    if product_definition is None:
        raise ValueError("Product definition routing requires ProductDefinition.")

    if product_definition.decision == "cannot_proceed":
        return FlowRoute.FAIL_FLOW

    if product_definition.decision == "requires_clarification":
        return FlowRoute.REQUEST_CLARIFICATION

    if product_definition.decision in {
        "approved",
        "approved_with_assumptions",
    }:
        return FlowRoute.RUN_REQUIREMENTS

    raise ValueError("ProductDefinition contains an unsupported decision.")


def route_after_requirements(
    state: BuildWiseFlowState,
) -> FlowRoute:
    """Choose the next route after Requirements Definition."""

    requirements = state.requirements_specification

    if requirements is None:
        raise ValueError("Requirements routing requires RequirementsSpecification.")

    if requirements.decision == "cannot_proceed":
        return FlowRoute.FAIL_FLOW

    if requirements.decision == "requires_clarification":
        return FlowRoute.REQUEST_CLARIFICATION

    if requirements.decision in {
        "approved",
        "approved_with_assumptions",
    }:
        return FlowRoute.PLAN_SPECIALISTS

    raise ValueError("RequirementsSpecification contains an unsupported decision.")


def build_specialist_execution_plan(
    state: BuildWiseFlowState,
) -> SpecialistExecutionPlan:
    """Build the deterministic specialist execution plan.

    Market & GTM and Solution Architecture are always selected. AI, Security,
    and QA/Evaluation are selected from structured Discovery and Requirements
    signals only. Product naming or free-form keyword matching is
    intentionally never used.

    This is the single planner model consumed by both the Flow (which
    registers the plan into ``BuildWiseFlowState`` via
    ``apply_specialist_execution_plan``) and the Technical Planning Crew
    (which reads ``recommendations`` to decide which specialists to run).
    """

    discovery = _require_discovery_result(state)
    requirements = _require_requirements_specification(state)

    recommendations: list[SpecialistRecommendation] = [
        SpecialistRecommendation(
            specialist=SpecialistType.MARKET_AND_GTM,
            required=True,
            reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
            explanation=(
                "Market and go-to-market analysis is required for every "
                "BuildWise product blueprint."
            ),
            estimated_effort="Medium",
        ),
        SpecialistRecommendation(
            specialist=SpecialistType.SOLUTION_ARCHITECTURE,
            required=True,
            reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
            explanation=(
                "Every BuildWise blueprint requires a solution architecture "
                "mapped to the validated requirements."
            ),
            estimated_effort="Medium",
        ),
    ]

    ai_selected, ai_reason, ai_explanation = _evaluate_ai_architect(
        discovery.capability_classification,
        requirements,
    )

    if ai_selected:
        recommendations.append(
            SpecialistRecommendation(
                specialist=SpecialistType.AI_ARCHITECTURE,
                required=False,
                reason=ai_reason,
                explanation=ai_explanation,
                estimated_effort="High",
            )
        )

    security_selected, security_reason, security_explanation = _evaluate_security_architect(
        discovery=discovery,
        requirements=requirements,
    )

    if security_selected:
        recommendations.append(
            SpecialistRecommendation(
                specialist=SpecialistType.SECURITY_ARCHITECTURE,
                required=False,
                reason=security_reason,
                explanation=security_explanation,
                estimated_effort="Medium",
            )
        )

    qa_selected, qa_reason, qa_explanation = _evaluate_qa_architect(
        discovery=discovery,
        requirements=requirements,
        ai_architect_selected=ai_selected,
    )

    if qa_selected:
        recommendations.append(
            SpecialistRecommendation(
                specialist=SpecialistType.QA_AND_EVALUATION,
                required=False,
                reason=qa_reason,
                explanation=qa_explanation,
                estimated_effort="Medium",
            )
        )

    technical_specialists = [SpecialistType.SOLUTION_ARCHITECTURE]

    if ai_selected:
        technical_specialists.append(SpecialistType.AI_ARCHITECTURE)

    if security_selected:
        technical_specialists.append(SpecialistType.SECURITY_ARCHITECTURE)

    if qa_selected:
        technical_specialists.append(SpecialistType.QA_AND_EVALUATION)

    execution_groups = [
        SpecialistExecutionGroup(
            name="market_and_gtm",
            execution_mode=ExecutionMode.PARALLEL,
            specialists=[SpecialistType.MARKET_AND_GTM],
            rationale=(
                "Market and GTM analysis has no dependency on the technical "
                "architecture and may run concurrently with it."
            ),
        ),
        SpecialistExecutionGroup(
            name="technical_architecture",
            execution_mode=ExecutionMode.SEQUENTIAL,
            specialists=technical_specialists,
            rationale=(
                "Solution Architecture must complete before any selected "
                "AI, Security, or QA specialist runs, since each depends on "
                "its output inside the Technical Planning Crew."
            ),
        ),
    ]

    dependencies: list[SpecialistDependency] = []

    if ai_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.AI_ARCHITECTURE,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description=(
                    "AI Architecture designs against the approved Solution "
                    "Architecture and cannot start before it completes."
                ),
            )
        )

    if security_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.SECURITY_ARCHITECTURE,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description=(
                    "Security Architecture reviews the approved Solution "
                    "Architecture's components and connections."
                ),
            )
        )

        if ai_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.AI_ARCHITECTURE,
                    target=SpecialistType.SECURITY_ARCHITECTURE,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description=(
                        "Security Architecture must also review the AI "
                        "Architecture's model, tool, and agent boundaries."
                    ),
                )
            )

    if qa_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.QA_AND_EVALUATION,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description="QA and Evaluation validates the approved Solution Architecture.",
            )
        )

        if ai_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.AI_ARCHITECTURE,
                    target=SpecialistType.QA_AND_EVALUATION,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description="QA and Evaluation includes AI evaluation coverage.",
                )
            )

        if security_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.SECURITY_ARCHITECTURE,
                    target=SpecialistType.QA_AND_EVALUATION,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description="QA and Evaluation validates the security controls.",
                )
            )

    excluded_explanations = {
        SpecialistType.AI_ARCHITECTURE: ai_explanation,
        SpecialistType.SECURITY_ARCHITECTURE: security_explanation,
        SpecialistType.QA_AND_EVALUATION: qa_explanation,
    }

    recommended_specialists = {recommendation.specialist for recommendation in recommendations}

    limitations = [
        f"{specialist.value}: {excluded_explanations[specialist]}"
        for specialist in (
            SpecialistType.AI_ARCHITECTURE,
            SpecialistType.SECURITY_ARCHITECTURE,
            SpecialistType.QA_AND_EVALUATION,
        )
        if specialist not in recommended_specialists
    ]

    budget = BudgetDecision(
        decision=BudgetDecisionType.APPROVED,
        explanation=(
            "Deterministic specialist selection requires no budget "
            "constraint beyond the specialists this plan already selected."
        ),
        limitations=limitations,
    )

    selected_summary = ", ".join(
        recommendation.specialist.value for recommendation in recommendations
    )

    return SpecialistExecutionPlan(
        recommendations=recommendations,
        execution_groups=execution_groups,
        dependencies=dependencies,
        budget=budget,
        execution_summary=(
            f"Selected {len(recommendations)} specialist(s) for this "
            f"consultation: {selected_summary}."
        ),
    )


def apply_specialist_execution_plan(
    *,
    state: BuildWiseFlowState,
    plan: SpecialistExecutionPlan,
) -> None:
    """Register a specialist execution plan in Flow state.

    This function keeps state mutation outside the pure decision-building
    function. It should be called once by the specialist-planning Flow step.
    Only the specialists in ``plan.recommendations`` are registered; every
    other ``SpecialistType`` is implicitly not selected.
    """

    if state.specialist_executions:
        raise ValueError("A specialist execution plan has already been applied to this Flow.")

    for recommendation in plan.recommendations:
        state.register_specialist(
            specialist=recommendation.specialist,
            selected=True,
            reason=recommendation.reason.value,
            rationale=recommendation.explanation,
        )


def route_after_specialist_planning(
    state: BuildWiseFlowState,
) -> FlowRoute:
    """Route to specialist execution after selection is registered."""

    selected_executions = [
        execution for execution in state.specialist_executions if execution.status == "pending"
    ]

    if not selected_executions:
        raise ValueError("Specialist planning must select at least one specialist.")

    required_specialists = {
        SpecialistType.MARKET_AND_GTM,
        SpecialistType.SOLUTION_ARCHITECTURE,
    }

    selected_specialists = {execution.specialist for execution in selected_executions}

    missing_required = required_specialists.difference(selected_specialists)

    if missing_required:
        formatted = ", ".join(sorted(specialist.value for specialist in missing_required))
        raise ValueError(f"The Flow is missing required specialist executions: {formatted}.")

    return FlowRoute.RUN_SPECIALISTS


def route_after_specialists(
    state: BuildWiseFlowState,
) -> FlowRoute:
    """Choose review or failure after all selected specialists terminate."""

    selected_executions = [
        execution
        for execution in state.specialist_executions
        if execution.status
        not in {
            "not_selected",
            "skipped",
        }
    ]

    if not selected_executions:
        raise ValueError("Specialist completion routing requires selected specialists.")

    unfinished = [
        execution
        for execution in selected_executions
        if execution.status
        in {
            "pending",
            "running",
        }
    ]

    if unfinished:
        formatted = ", ".join(sorted(execution.specialist.value for execution in unfinished))
        raise ValueError(
            f"Specialist routing cannot continue while executions remain unfinished: {formatted}."
        )

    failed_required_specialists = [
        execution
        for execution in selected_executions
        if execution.status == "failed"
        and execution.specialist
        in {
            SpecialistType.MARKET_AND_GTM,
            SpecialistType.SOLUTION_ARCHITECTURE,
        }
    ]

    if failed_required_specialists:
        return FlowRoute.FAIL_FLOW

    return FlowRoute.RUN_LEAD_REVIEW


def route_after_review(
    *,
    revision_required: bool,
    approved: bool,
) -> FlowRoute:
    """Translate a structured Lead Reviewer decision into a Flow route.

    The complete review domain model will replace these two explicit flags
    when `buildwise.domain.review` is implemented.
    """

    if revision_required and approved:
        raise ValueError("A review cannot be approved while also requiring revision.")

    if revision_required:
        return FlowRoute.RUN_TARGETED_REVISION

    if approved:
        return FlowRoute.ASSEMBLE_BLUEPRINT

    return FlowRoute.FAIL_FLOW


def route_after_blueprint_assembly(
    state: BuildWiseFlowState,
) -> FlowRoute:
    """Route a successfully assembled blueprint to Flow completion."""

    if state.blueprint_artifact_id is None:
        raise ValueError("Blueprint completion routing requires blueprint_artifact_id.")

    if state.review_artifact_id is None:
        raise ValueError("Blueprint completion routing requires review_artifact_id.")

    return FlowRoute.COMPLETE_FLOW


def _evaluate_ai_architect(
    classification: CapabilityClassification,
    requirements: RequirementsSpecification,
) -> tuple[
    bool,
    SpecialistSelectionReason | None,
    MediumText,
]:
    """Determine whether dedicated AI architecture is required."""

    ai_capabilities = {
        CapabilityType.AI_ASSISTED,
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    }

    classified_ai = bool(set(classification.capabilities).intersection(ai_capabilities))

    ai_requirement_exists = any(
        requirement.category == "ai" for requirement in requirements.functional_requirements
    )

    selected = (
        classification.ai_required
        or classification.rag_required
        or classification.agents_required
        or classified_ai
        or ai_requirement_exists
    )

    if selected:
        return (
            True,
            SpecialistSelectionReason.AI_CAPABILITY_REQUIRED,
            (
                "The validated capability classification or requirements "
                "contain an AI, RAG, or agentic capability requiring "
                "dedicated AI architecture."
            ),
        )

    return (
        False,
        None,
        (
            "No validated AI, RAG, model-driven, or agentic capability "
            "requires a dedicated AI architecture."
        ),
    )


def _evaluate_security_architect(
    *,
    discovery: DiscoveryResult,
    requirements: RequirementsSpecification,
) -> tuple[
    bool,
    SpecialistSelectionReason | None,
    MediumText,
]:
    """Determine whether dedicated security architecture is required."""

    classification = discovery.capability_classification

    security_nfr_exists = any(
        requirement.category
        in {
            "security",
            "privacy",
            "compliance",
            "data_integrity",
        }
        for requirement in requirements.non_functional_requirements
    )

    sensitive_data_requirement_exists = any(
        requirement.contains_sensitive_data
        or requirement.subject_to_regulation
        or requirement.data_classification
        in {
            "restricted",
            "sensitive_personal",
            "regulated",
        }
        for requirement in requirements.data_requirements
    )

    privileged_integration_exists = any(
        requirement.authentication_method
        not in {
            "none",
            "not_decided",
        }
        for requirement in requirements.integration_requirements
    )

    high_security_risk_exists = any(
        risk.category
        in {
            "security",
            "privacy",
            "compliance",
        }
        and risk.severity
        in {
            RiskSeverity.HIGH,
            RiskSeverity.CRITICAL,
        }
        for risk in discovery.risks
    )

    selected = (
        classification.sensitive_data_detected
        or classification.regulated_domain_detected
        or sensitive_data_requirement_exists
        or security_nfr_exists
        or privileged_integration_exists
        or high_security_risk_exists
    )

    if not selected:
        return (
            False,
            None,
            (
                "The validated product context does not contain material "
                "sensitive-data, regulatory, privileged-integration, or "
                "high-severity security signals."
            ),
        )

    if classification.sensitive_data_detected or sensitive_data_requirement_exists:
        return (
            True,
            SpecialistSelectionReason.SENSITIVE_DATA,
            ("Sensitive or restricted data requirements require dedicated security architecture."),
        )

    if classification.regulated_domain_detected:
        return (
            True,
            SpecialistSelectionReason.REGULATED_DOMAIN,
            (
                "The product operates in a regulated domain and requires "
                "dedicated security and compliance architecture."
            ),
        )

    if privileged_integration_exists:
        return (
            True,
            SpecialistSelectionReason.EXTERNAL_INTEGRATIONS,
            (
                "Authenticated or privileged external integrations require "
                "dedicated trust-boundary and access-control review."
            ),
        )

    return (
        True,
        SpecialistSelectionReason.HIGH_RISK,
        (
            "Security, privacy, compliance, or data-integrity requirements "
            "create a material risk requiring specialist review."
        ),
    )


def _evaluate_qa_architect(
    *,
    discovery: DiscoveryResult,
    requirements: RequirementsSpecification,
    ai_architect_selected: bool,
) -> tuple[
    bool,
    SpecialistSelectionReason | None,
    MediumText,
]:
    """Determine whether dedicated QA and AI evaluation design is required."""

    quality_nfr_categories = {
        "performance",
        "availability",
        "reliability",
        "security",
        "accessibility",
        "recoverability",
        "data_integrity",
        "compliance",
    }

    critical_quality_requirement_exists = any(
        requirement.priority is RequirementPriority.MUST_HAVE
        and requirement.category in quality_nfr_categories
        for requirement in requirements.non_functional_requirements
    )

    high_risk_exists = any(
        risk.severity
        in {
            RiskSeverity.HIGH,
            RiskSeverity.CRITICAL,
        }
        for risk in discovery.risks
    )

    complex_failure_behavior_exists = any(
        edge_case.blocking
        or edge_case.category
        in {
            "concurrency",
            "partial_failure",
            "dependency_failure",
            "data_consistency",
            "state_transition",
        }
        for edge_case in requirements.edge_cases
    )

    selected = (
        ai_architect_selected
        or critical_quality_requirement_exists
        or high_risk_exists
        or complex_failure_behavior_exists
    )

    if not selected:
        return (
            False,
            None,
            (
                "The MVP requirements do not currently justify a separate "
                "QA and evaluation architecture artifact."
            ),
        )

    if ai_architect_selected:
        return (
            True,
            SpecialistSelectionReason.AI_CAPABILITY_REQUIRED,
            (
                "AI-generated or model-driven behavior requires a dedicated "
                "evaluation and regression strategy."
            ),
        )

    if high_risk_exists:
        return (
            True,
            SpecialistSelectionReason.HIGH_RISK,
            ("High or critical Discovery risks require a dedicated QA and validation strategy."),
        )

    return (
        True,
        SpecialistSelectionReason.PRODUCT_COMPLEXITY,
        (
            "Must-have quality attributes or complex failure paths require "
            "a dedicated QA and evaluation strategy."
        ),
    )


def _require_discovery_result(
    state: BuildWiseFlowState,
) -> DiscoveryResult:
    """Return the Discovery result required for routing."""

    if state.discovery_result is None:
        raise ValueError("Routing requires a completed DiscoveryResult.")

    return state.discovery_result


def _require_requirements_specification(
    state: BuildWiseFlowState,
) -> RequirementsSpecification:
    """Return the requirements specification required for routing."""

    if state.requirements_specification is None:
        raise ValueError("Specialist routing requires RequirementsSpecification.")

    return state.requirements_specification
