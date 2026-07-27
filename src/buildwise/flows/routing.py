from __future__ import annotations

from enum import StrEnum

from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import (
    SessionStage,
    SessionStatus,
    SpecialistType,
)
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
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


def _require_discovery_result(
    state: BuildWiseFlowState,
) -> DiscoveryResult:
    """Return the Discovery result required for routing."""

    if state.discovery_result is None:
        raise ValueError("Routing requires a completed DiscoveryResult.")

    return state.discovery_result
