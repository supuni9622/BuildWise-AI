from buildwise.application.cost_aggregator import ProjectCostAggregator
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.flows.state import FlowRuntimeLimits
from buildwise.planning.planner import SpecialistPlanner
from buildwise.planning.specialist_context import RequirementsProjection
from buildwise.reviewing.review_index import build_lead_review_index
from fixtures.planning import build_product_planning_inputs


def test_requirements_projection_excludes_narrative_context() -> None:
    _, planning = build_product_planning_inputs()
    projection = RequirementsProjection.from_artifact(planning.requirements)

    assert len(projection.model_dump_json()) < len(planning.requirements.model_dump_json())
    assert "user_stories" not in projection.model_fields
    assert "edge_cases" not in projection.model_fields


def test_review_index_is_smaller_than_required_artifact_payloads() -> None:
    discovery, planning = build_product_planning_inputs()
    plan = SpecialistPlanner().create_execution_plan(
        discovery=discovery,
        product_planning=planning,
        limits=FlowRuntimeLimits(),
    )
    technical = TechnicalPlanningResult.model_construct(
        session_id=discovery.session_id,
        solution_architecture=SolutionArchitecture.model_construct(
            architecture_cost_estimates=[]
        ),
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
    )
    costs = ProjectCostAggregator().aggregate(
        product_planning=planning,
        technical_planning=technical,
    )
    index = build_lead_review_index(
        discovery=discovery,
        product_definition=planning.product_definition,
        requirements=planning.requirements,
        specialist_plan=plan,
        cost_summary=costs,
        market_and_gtm=None,
        solution_architecture=None,
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
        revision_history=None,
    )
    full_chars = sum(
        len(item.model_dump_json())
        for item in (
            discovery,
            planning.product_definition,
            planning.requirements,
            plan,
            costs,
        )
    )

    assert len(index.model_dump_json()) < full_chars * 0.25
    assert any(
        finding.code == "selected_artifact_missing"
        for finding in index.deterministic_findings
    )
