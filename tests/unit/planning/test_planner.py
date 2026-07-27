from __future__ import annotations

import pytest

from buildwise.domain.enums import (
    BudgetDecisionType,
    CapabilityType,
    SpecialistSelectionReason,
    SpecialistType,
)
from buildwise.flows.state import FlowRuntimeLimits
from buildwise.planning.planner import SpecialistPlanner, SpecialistPlanningError
from fixtures.planning import (
    build_discovery_result,
    build_product_planning_inputs,
    build_sensitive_data_requirement,
)

_SOLUTION = SpecialistType.SOLUTION_ARCHITECTURE
_AI = SpecialistType.AI_ARCHITECTURE
_SECURITY = SpecialistType.SECURITY_ARCHITECTURE
_QA = SpecialistType.QA_AND_EVALUATION


class TestCreateExecutionPlan:
    def test_standard_product_selects_only_solution(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        plan = SpecialistPlanner().create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
        )

        specialists = {recommendation.specialist for recommendation in plan.recommendations}

        assert specialists == {_SOLUTION}
        assert plan.budget.decision is BudgetDecisionType.APPROVED
        assert SpecialistType.MARKET_AND_GTM not in specialists

    def test_ai_rag_product_selects_solution_ai_security_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={
                "capabilities": [CapabilityType.AI_CORE, CapabilityType.RAG],
                "rag_required": True,
            },
            data_requirements=[build_sensitive_data_requirement()],
        )

        plan = SpecialistPlanner().create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
        )

        specialists = {recommendation.specialist for recommendation in plan.recommendations}

        assert specialists == {_SOLUTION, _AI, _SECURITY, _QA}
        assert plan.budget.decision is BudgetDecisionType.APPROVED

        # Solution -> AI -> Security -> QA, matching the fixed dependency graph.
        group_order = [group.specialists[0] for group in plan.execution_groups]
        assert group_order.index(_SOLUTION) < group_order.index(_AI)
        assert group_order.index(_AI) < group_order.index(_SECURITY)
        assert group_order.index(_SECURITY) < group_order.index(_QA)

    def test_explicit_request_adds_optional_specialist(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        plan = SpecialistPlanner().create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
            explicitly_requested={SpecialistType.QA_AND_EVALUATION},
        )

        specialists = {recommendation.specialist for recommendation in plan.recommendations}
        qa_recommendation = next(
            recommendation
            for recommendation in plan.recommendations
            if recommendation.specialist is _QA
        )

        assert _QA in specialists
        assert qa_recommendation.reason is SpecialistSelectionReason.EXPLICIT_USER_REQUEST

    def test_explicit_exclusion_of_optional_specialist_is_honored(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            data_requirements=[build_sensitive_data_requirement()],
            discovery_kwargs={"risks": []},
        )

        # Sensitive data alone selects Security via SENSITIVE_DATA, which is
        # protected; excluding it must raise instead of silently dropping it.
        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
                explicitly_excluded={SpecialistType.SECURITY_ARCHITECTURE},
            )

    def test_solution_architecture_cannot_be_excluded(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
                explicitly_excluded={SpecialistType.SOLUTION_ARCHITECTURE},
            )

    def test_market_and_gtm_is_rejected_as_a_technical_request(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
                explicitly_requested={SpecialistType.MARKET_AND_GTM},
            )

    def test_mismatched_session_ids_raise(self) -> None:
        _, product_planning = build_product_planning_inputs()
        other_discovery = build_discovery_result()

        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=other_discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
            )

    def test_blocking_discovery_raises(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={"can_continue": False},
        )

        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
            )

    def test_contradictory_request_and_exclusion_raises(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        with pytest.raises(SpecialistPlanningError):
            SpecialistPlanner().create_execution_plan(
                discovery=discovery,
                product_planning=product_planning,
                limits=FlowRuntimeLimits(),
                explicitly_requested={SpecialistType.QA_AND_EVALUATION},
                explicitly_excluded={SpecialistType.QA_AND_EVALUATION},
            )

    def test_plan_is_deterministic_across_repeated_calls(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={
                "capabilities": [CapabilityType.AI_CORE, CapabilityType.RAG],
                "rag_required": True,
            },
            data_requirements=[build_sensitive_data_requirement()],
        )
        limits = FlowRuntimeLimits()
        planner = SpecialistPlanner()

        first = planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=limits,
        )
        second = planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=limits,
        )

        assert first == second


class TestShouldIncludeEarlyMarketContext:
    def test_delegates_to_policy(self) -> None:
        discovery, _ = build_product_planning_inputs()
        planner = SpecialistPlanner()

        assert planner.should_include_early_market_context(discovery=discovery) is False
        assert (
            planner.should_include_early_market_context(
                discovery=discovery,
                explicitly_requested=True,
            )
            is True
        )
