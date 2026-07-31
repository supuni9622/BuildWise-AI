"""Unit tests for the deterministic Specialist Planner. No LLM calls."""

from __future__ import annotations

from uuid import uuid4

import pytest

from buildwisev2.domain.common import CapabilityType, FlowRuntimeLimits, SpecialistType
from buildwisev2.domain.discovery import (
    CapabilityClassification,
    CompletenessAssessment,
    DiscoveryDecision,
    DiscoveryResult,
)
from buildwisev2.domain.planning_results import ProductPlanningResult
from buildwisev2.domain.product import (
    ProductDefinition,
    ProductDefinitionDecision,
    ProductFeature,
)
from buildwisev2.domain.requirements import (
    EdgeCase,
    FunctionalRequirement,
    NFRCategory,
    NonFunctionalRequirement,
    RequirementPriority,
    RequirementsDecision,
    RequirementsSpecification,
)
from buildwisev2.domain.specialist_planning import BudgetDecisionType
from buildwisev2.planning import SpecialistPlanner


def make_discovery(session_id, **overrides) -> DiscoveryResult:
    base = dict(
        session_id=session_id,
        interpreted_idea="An app",
        capability_classification=CapabilityClassification(),
        completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
        decision=DiscoveryDecision.CONTINUE,
        confidence=0.8,
    )
    base.update(overrides)
    return DiscoveryResult(**base)


def make_product_planning(
    session_id,
    *,
    features: list[ProductFeature] | None = None,
    mvp_feature_ids: list[str] | None = None,
    functional_requirements: list[FunctionalRequirement] | None = None,
    non_functional_requirements: list[NonFunctionalRequirement] | None = None,
    edge_cases: list[EdgeCase] | None = None,
) -> ProductPlanningResult:
    product_definition = ProductDefinition(
        session_id=session_id,
        vision="v",
        value_proposition="vp",
        goals=["g"],
        personas=[],
        features=features or [],
        mvp_feature_ids=mvp_feature_ids or [],
        decision=ProductDefinitionDecision.APPROVED,
    )
    requirements = RequirementsSpecification(
        session_id=session_id,
        functional_requirements=functional_requirements or [],
        non_functional_requirements=non_functional_requirements or [],
        edge_cases=edge_cases or [],
        decision=RequirementsDecision.APPROVED,
    )
    return ProductPlanningResult(
        session_id=session_id,
        product_definition=product_definition,
        requirements=requirements,
    )


@pytest.fixture
def planner() -> SpecialistPlanner:
    return SpecialistPlanner()


def test_standard_saas_selects_only_solution_architecture(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(session_id)
    product_planning = make_product_planning(session_id)

    plan = planner.create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(),
    )

    assert plan.selected_specialists() == {SpecialistType.SOLUTION_ARCHITECTURE}
    assert plan.budget.decision == BudgetDecisionType.APPROVED


def test_ai_rag_assistant_with_sensitive_data_selects_all_four(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(
        session_id,
        capability_classification=CapabilityClassification(
            capabilities=[CapabilityType.AI_CORE, CapabilityType.RAG],
            ai_required=True,
            rag_required=True,
            sensitive_data_detected=True,
        ),
    )
    product_planning = make_product_planning(session_id)

    plan = planner.create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(),
    )

    assert plan.selected_specialists() == {
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    }
    dependency_pairs = {(d.source, d.target) for d in plan.dependencies}
    assert (
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
    ) in dependency_pairs
    assert (
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
    ) in dependency_pairs
    assert (
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    ) in dependency_pairs
    group_names = [g.specialists[0] for g in plan.execution_groups]
    assert group_names.index(SpecialistType.SOLUTION_ARCHITECTURE) < group_names.index(
        SpecialistType.AI_ARCHITECTURE
    )


def test_regulated_ai_workflow_under_tight_budget_is_deferred_not_silently_trimmed(
    planner: SpecialistPlanner,
) -> None:
    session_id = uuid4()
    discovery = make_discovery(
        session_id,
        capability_classification=CapabilityClassification(
            capabilities=[CapabilityType.AI_CORE],
            ai_required=True,
            sensitive_data_detected=True,
            regulated_domain_detected=True,
        ),
    )
    product_planning = make_product_planning(session_id)

    plan = planner.create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(maximum_agent_executions=1),
    )

    assert plan.budget.decision == BudgetDecisionType.DEFERRED
    assert plan.execution_groups == []
    assert plan.dependencies == []


def test_must_have_quality_nfr_selects_qa_without_ai_or_security(
    planner: SpecialistPlanner,
) -> None:
    session_id = uuid4()
    discovery = make_discovery(session_id)
    product_planning = make_product_planning(
        session_id,
        non_functional_requirements=[
            NonFunctionalRequirement(
                id="NFR-1",
                category=NFRCategory.AVAILABILITY,
                description="99.9% uptime",
                priority=RequirementPriority.MUST_HAVE,
            )
        ],
    )

    plan = planner.create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(),
    )

    assert plan.selected_specialists() == {
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    }


def test_explicit_exclusion_of_mandatory_specialist_raises(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(
        session_id,
        capability_classification=CapabilityClassification(sensitive_data_detected=True),
    )
    product_planning = make_product_planning(session_id)

    with pytest.raises(ValueError):
        planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
            explicitly_excluded={SpecialistType.SECURITY_ARCHITECTURE},
        )


def test_explicit_request_adds_optional_specialist(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(session_id)
    product_planning = make_product_planning(session_id)

    plan = planner.create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(),
        explicitly_requested={SpecialistType.SECURITY_ARCHITECTURE},
    )

    assert SpecialistType.SECURITY_ARCHITECTURE in plan.selected_specialists()


def test_incomplete_discovery_raises(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(
        session_id,
        completeness=CompletenessAssessment(can_continue=False, completeness_score=0.2),
    )
    product_planning = make_product_planning(session_id)

    with pytest.raises(ValueError):
        planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
        )


def test_mismatched_session_ids_raise(planner: SpecialistPlanner) -> None:
    discovery = make_discovery(uuid4())
    product_planning = make_product_planning(uuid4())

    with pytest.raises(ValueError):
        planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=FlowRuntimeLimits(),
        )


def test_determinism_across_repeated_calls(planner: SpecialistPlanner) -> None:
    session_id = uuid4()
    discovery = make_discovery(session_id)
    product_planning = make_product_planning(session_id)
    limits = FlowRuntimeLimits()

    plan_a = planner.create_execution_plan(
        discovery=discovery, product_planning=product_planning, limits=limits
    )
    plan_b = planner.create_execution_plan(
        discovery=discovery, product_planning=product_planning, limits=limits
    )

    assert plan_a.model_dump() == plan_b.model_dump()


def test_should_include_early_market_context() -> None:
    planner = SpecialistPlanner()
    session_id = uuid4()

    quiet = make_discovery(session_id)
    assert planner.should_include_early_market_context(discovery=quiet) is False
    assert (
        planner.should_include_early_market_context(discovery=quiet, explicitly_requested=True)
        is True
    )

    signaled = make_discovery(
        session_id,
        capability_classification=CapabilityClassification(specialist_signals=["market_and_gtm"]),
    )
    assert planner.should_include_early_market_context(discovery=signaled) is True
