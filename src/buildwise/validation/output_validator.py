"""Final deterministic validation across completed consulting stages."""

from __future__ import annotations

from buildwise.application.cost_aggregator import aggregate_project_costs
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.enums import SpecialistType
from buildwise.domain.product import ProductDefinition
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.flows.state import BuildWiseFlowState
from buildwise.planning.execution_graph import validate_execution_graph


def validate_output(state: BuildWiseFlowState) -> None:
    """Validate all prerequisites for assembling an approved blueprint."""

    discovery = _require(state.discovery_result, "discovery_result")
    product = _require(state.product_planning_result, "product_planning_result")
    plan = _require(state.specialist_execution_plan, "specialist_execution_plan")
    technical = _require(state.technical_planning_result, "technical_planning_result")
    cost_summary = _require(state.cost_summary, "cost_summary")
    review = _require(state.lead_review, "lead_review")

    if cost_summary.session_id != state.session_id:
        raise ValueError("cost_summary.session_id must match Flow session_id.")
    expected_costs = aggregate_project_costs(
        product_planning=product,
        technical_planning=technical,
    )
    if (
        cost_summary.estimates != expected_costs.estimates
        or cost_summary.totals != expected_costs.totals
    ):
        raise ValueError("CostSummary is stale or inconsistent with planning artifacts.")

    session_artifacts = {
        "discovery_result": discovery,
        "product_planning_result": product,
        "product_definition": product.product_definition,
        "requirements": product.requirements,
        "technical_planning_result": technical,
        "solution_architecture": technical.solution_architecture,
        "ai_architecture": technical.ai_architecture,
    }
    for name, artifact in session_artifacts.items():
        if artifact is not None and artifact.session_id != state.session_id:
            raise ValueError(f"{name}.session_id must match Flow session_id.")

    # Re-run the aggregate and cross-artifact domain validators at the final boundary.
    ProductPlanningResult.model_validate(product.model_dump())
    TechnicalPlanningResult.model_validate(technical.model_dump())
    ProductDefinition.validate_discovery_ownership(
        product_definition=product.product_definition,
        discovery_result=discovery,
    )
    RequirementsSpecification.validate_product_ownership(
        requirements_specification=product.requirements,
        product_definition=product.product_definition,
    )
    SolutionArchitecture.validate_requirements_ownership(
        solution_architecture=technical.solution_architecture,
        requirements_specification=product.requirements,
    )

    selected = {item.specialist for item in plan.recommendations}
    validate_execution_graph(
        selected_specialists=selected,
        dependencies=plan.dependencies,
        execution_groups=plan.execution_groups,
    )
    failed = set(state.failed_specialists)
    effective_selected = selected - failed
    technical.validate_specialist_selection(
        ai_selected=SpecialistType.AI_ARCHITECTURE in effective_selected,
        security_selected=SpecialistType.SECURITY_ARCHITECTURE in effective_selected,
        qa_selected=SpecialistType.QA_AND_EVALUATION in effective_selected,
    )
    review.validate_decision_consistency()

    if not review.approved_for_blueprint:
        raise ValueError("Lead Review has not approved blueprint assembly.")
    if any(request.blocking for request in review.revision_requests):
        raise ValueError("A blocking revision remains before blueprint approval.")


def _require[T](value: T | None, name: str) -> T:
    if value is None:
        raise ValueError(f"{name} is required before blueprint assembly.")
    return value
