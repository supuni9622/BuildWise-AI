from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import BuildWiseModel, MediumText
from buildwise.domain.discovery import CapabilityClassification, DiscoveryResult
from buildwise.domain.enums import (
    CapabilityType,
    RequirementPriority,
    RiskSeverity,
    SessionStage,
    SessionStatus,
    SpecialistSelectionReason,
    SpecialistType,
)
from buildwise.domain.requirements import RequirementsSpecification
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


class SpecialistRoutingDecision(BuildWiseModel):
    """Deterministic selection decision for one BuildWise specialist."""

    specialist: SpecialistType
    selected: bool

    reason: SpecialistSelectionReason | None = None
    rationale: MediumText

    execution_order: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_selection_decision(self) -> SpecialistRoutingDecision:
        """Validate selected and non-selected decision metadata."""

        if self.selected:
            if self.reason is None:
                raise ValueError("A selected specialist requires a selection reason.")

            if self.execution_order is None:
                raise ValueError("A selected specialist requires an execution order.")
        else:
            if self.reason is not None:
                raise ValueError("A non-selected specialist cannot have a selection reason.")

            if self.execution_order is not None:
                raise ValueError("A non-selected specialist cannot have an execution order.")

        return self


class SpecialistRoutingPlan(BuildWiseModel):
    """Ordered specialist-selection plan produced by deterministic routing."""

    decisions: list[SpecialistRoutingDecision] = Field(min_length=1)

    @field_validator("decisions")
    @classmethod
    def validate_decisions(
        cls,
        value: list[SpecialistRoutingDecision],
    ) -> list[SpecialistRoutingDecision]:
        """Require unique specialists and contiguous selected execution order."""

        specialists = [decision.specialist for decision in value]

        if len(specialists) != len(set(specialists)):
            raise ValueError("A specialist may appear only once in a routing plan.")

        selected_orders = sorted(
            decision.execution_order
            for decision in value
            if decision.selected and decision.execution_order is not None
        )

        expected_orders = list(range(1, len(selected_orders) + 1))

        if selected_orders != expected_orders:
            raise ValueError(
                "Selected specialist execution orders must be contiguous and start at one."
            )

        selected_specialists = {decision.specialist for decision in value if decision.selected}

        always_required = {
            SpecialistType.MARKET_AND_GTM,
            SpecialistType.SOLUTION_ARCHITECTURE,
        }

        missing_required = always_required.difference(selected_specialists)

        if missing_required:
            formatted = ", ".join(sorted(specialist.value for specialist in missing_required))
            raise ValueError(
                f"The routing plan is missing always-required specialists: {formatted}."
            )

        return value

    @property
    def selected_decisions(self) -> list[SpecialistRoutingDecision]:
        """Return selected decisions in execution order."""

        return sorted(
            (decision for decision in self.decisions if decision.selected),
            key=lambda decision: decision.execution_order or 0,
        )

    @property
    def selected_specialists(self) -> list[SpecialistType]:
        """Return selected specialist types in execution order."""

        return [decision.specialist for decision in self.selected_decisions]

    def get_decision(
        self,
        specialist: SpecialistType,
    ) -> SpecialistRoutingDecision:
        """Return the routing decision for one specialist."""

        decision = next(
            (item for item in self.decisions if item.specialist is specialist),
            None,
        )

        if decision is None:
            raise ValueError(f"No routing decision exists for '{specialist.value}'.")

        return decision


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


def build_specialist_routing_plan(
    state: BuildWiseFlowState,
) -> SpecialistRoutingPlan:
    """Build the deterministic specialist execution plan.

    The market/GTM and solution architecture specialists are always selected.

    AI, security, and QA/evaluation specialists are selected from structured
    Discovery and Requirements signals. Product naming or free-form keyword
    matching is intentionally not used.
    """

    discovery = _require_discovery_result(state)
    requirements = _require_requirements_specification(state)

    decisions: list[SpecialistRoutingDecision] = []
    next_execution_order = 1

    decisions.append(
        SpecialistRoutingDecision(
            specialist=SpecialistType.MARKET_AND_GTM,
            selected=True,
            reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
            rationale=(
                "Market and go-to-market analysis is required for every "
                "BuildWise product blueprint."
            ),
            execution_order=next_execution_order,
        )
    )
    next_execution_order += 1

    decisions.append(
        SpecialistRoutingDecision(
            specialist=SpecialistType.SOLUTION_ARCHITECTURE,
            selected=True,
            reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
            rationale=(
                "Every BuildWise blueprint requires a solution architecture "
                "mapped to the validated requirements."
            ),
            execution_order=next_execution_order,
        )
    )
    next_execution_order += 1

    ai_selected, ai_reason, ai_rationale = _evaluate_ai_architect(
        discovery.capability_classification,
        requirements,
    )

    decisions.append(
        SpecialistRoutingDecision(
            specialist=SpecialistType.AI_ARCHITECTURE,
            selected=ai_selected,
            reason=ai_reason,
            rationale=ai_rationale,
            execution_order=(next_execution_order if ai_selected else None),
        )
    )

    if ai_selected:
        next_execution_order += 1

    security_selected, security_reason, security_rationale = _evaluate_security_architect(
        discovery=discovery,
        requirements=requirements,
    )

    decisions.append(
        SpecialistRoutingDecision(
            specialist=SpecialistType.SECURITY_ARCHITECTURE,
            selected=security_selected,
            reason=security_reason,
            rationale=security_rationale,
            execution_order=(next_execution_order if security_selected else None),
        )
    )

    if security_selected:
        next_execution_order += 1

    qa_selected, qa_reason, qa_rationale = _evaluate_qa_architect(
        discovery=discovery,
        requirements=requirements,
        ai_architect_selected=ai_selected,
    )

    decisions.append(
        SpecialistRoutingDecision(
            specialist=SpecialistType.QA_AND_EVALUATION,
            selected=qa_selected,
            reason=qa_reason,
            rationale=qa_rationale,
            execution_order=(next_execution_order if qa_selected else None),
        )
    )

    return SpecialistRoutingPlan(decisions=decisions)


def apply_specialist_routing_plan(
    *,
    state: BuildWiseFlowState,
    plan: SpecialistRoutingPlan,
) -> None:
    """Register a specialist routing plan in Flow state.

    This function keeps state mutation outside the pure decision-building
    function. It should be called once by the specialist-planning Flow step.
    """

    if state.specialist_executions:
        raise ValueError("Specialist routing has already been applied to this Flow.")

    for decision in plan.decisions:
        state.register_specialist(
            specialist=decision.specialist,
            selected=decision.selected,
            reason=(decision.reason.value if decision.reason is not None else None),
            rationale=decision.rationale,
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
