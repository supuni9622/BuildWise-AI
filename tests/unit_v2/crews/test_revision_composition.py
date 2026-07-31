"""Unit tests for revision-aware Crew composition: a task regenerates only
when targeted or an upstream dependency also regenerates; everything else
is skipped and reused from the prior result. No live LLM calls.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from buildwisev2.agents import AgentFactory
from buildwisev2.crews.product_planning import create_product_planning_crew
from buildwisev2.crews.technical_planning import create_technical_planning_crew
from buildwisev2.domain.architecture import (
    DeploymentView,
    SolutionArchitecture,
    SolutionArchitectureDecision,
)
from buildwisev2.domain.common import SpecialistType
from buildwisev2.domain.market_and_gtm import MarketAndGTMDecision, MarketAndGTMStrategy
from buildwisev2.domain.planning_results import ProductPlanningResult, TechnicalPlanningResult
from buildwisev2.domain.product import ProductDefinition, ProductDefinitionDecision
from buildwisev2.domain.requirements import RequirementsDecision, RequirementsSpecification
from buildwisev2.domain.review import RevisionRequest, RevisionTarget
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    BudgetDecisionType,
    EffortLevel,
    SpecialistExecutionPlan,
    SpecialistRecommendation,
    SpecialistSelectionReason,
)

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


@pytest.fixture
def agent_factory() -> AgentFactory:
    return AgentFactory()


@pytest.fixture
def prior_product_planning() -> ProductPlanningResult:
    session_id = uuid4()
    return ProductPlanningResult(
        session_id=session_id,
        market_and_gtm=MarketAndGTMStrategy(
            session_id=session_id,
            segments=[],
            positioning="p",
            decision=MarketAndGTMDecision.APPROVED,
        ),
        product_definition=ProductDefinition(
            session_id=session_id,
            vision="v",
            value_proposition="vp",
            goals=["g"],
            personas=[],
            features=[],
            mvp_feature_ids=[],
            decision=ProductDefinitionDecision.APPROVED,
        ),
        requirements=RequirementsSpecification(
            session_id=session_id,
            functional_requirements=[],
            non_functional_requirements=[],
            decision=RequirementsDecision.APPROVED,
        ),
    )


@pytest.fixture
def prior_technical_planning(
    prior_product_planning: ProductPlanningResult,
) -> TechnicalPlanningResult:
    return TechnicalPlanningResult(
        session_id=prior_product_planning.session_id,
        solution_architecture=SolutionArchitecture(
            session_id=prior_product_planning.session_id,
            system_context="c",
            components=[],
            deployment=DeploymentView(description="d"),
            scalability_strategy="s",
            reliability_strategy="r",
            observability_strategy="o",
            decision=SolutionArchitectureDecision.APPROVED,
        ),
    )


def _plan(*specialists: SpecialistType) -> SpecialistExecutionPlan:
    recommendations = [
        SpecialistRecommendation(
            specialist=specialist,
            required=specialist == SpecialistType.SOLUTION_ARCHITECTURE,
            reason=SpecialistSelectionReason.MANDATORY,
            explanation="test",
            estimated_effort=EffortLevel.MEDIUM,
        )
        for specialist in specialists
    ]
    return SpecialistExecutionPlan(
        recommendations=recommendations,
        execution_groups=[],
        dependencies=[],
        budget=BudgetDecision(decision=BudgetDecisionType.APPROVED, explanation="ok"),
        execution_summary="test",
    )


def test_requirements_only_revision_skips_market_and_product(
    agent_factory: AgentFactory,
    prior_product_planning: ProductPlanningResult,
) -> None:
    crew = create_product_planning_crew(
        include_market_and_gtm=True,
        agent_factory=agent_factory,
        revision_requests=[
            RevisionRequest(target=RevisionTarget.REQUIREMENTS, issue="x", instructions="y")
        ],
        prior_result=prior_product_planning,
    )

    assert [t.name for t in crew.tasks] == ["requirements"]


def test_product_definition_revision_cascades_to_requirements_not_market(
    agent_factory: AgentFactory,
    prior_product_planning: ProductPlanningResult,
) -> None:
    crew = create_product_planning_crew(
        include_market_and_gtm=True,
        agent_factory=agent_factory,
        revision_requests=[
            RevisionRequest(target=RevisionTarget.PRODUCT_DEFINITION, issue="x", instructions="y")
        ],
        prior_result=prior_product_planning,
    )

    assert [t.name for t in crew.tasks] == ["product_definition", "requirements"]


def test_market_revision_cascades_through_product_and_requirements(
    agent_factory: AgentFactory,
    prior_product_planning: ProductPlanningResult,
) -> None:
    crew = create_product_planning_crew(
        include_market_and_gtm=True,
        agent_factory=agent_factory,
        revision_requests=[
            RevisionRequest(target=RevisionTarget.MARKET_AND_GTM, issue="x", instructions="y")
        ],
        prior_result=prior_product_planning,
    )

    assert [t.name for t in crew.tasks] == ["market_and_gtm", "product_definition", "requirements"]


def test_product_planning_revision_without_prior_result_raises(agent_factory: AgentFactory) -> None:
    with pytest.raises(ValueError, match="prior_result"):
        create_product_planning_crew(
            include_market_and_gtm=False,
            agent_factory=agent_factory,
            revision_requests=[
                RevisionRequest(target=RevisionTarget.REQUIREMENTS, issue="x", instructions="y")
            ],
        )


def test_qa_only_revision_skips_solution_and_ai(
    agent_factory: AgentFactory,
    prior_technical_planning: TechnicalPlanningResult,
) -> None:
    plan = _plan(SpecialistType.SOLUTION_ARCHITECTURE, SpecialistType.QA_AND_EVALUATION)

    crew = create_technical_planning_crew(
        specialist_plan=plan,
        agent_factory=agent_factory,
        revision_requests=[
            RevisionRequest(target=RevisionTarget.QA_EVALUATION, issue="x", instructions="y")
        ],
        prior_result=prior_technical_planning,
    )

    assert [t.name for t in crew.tasks] == ["qa_evaluation"]


def test_solution_revision_cascades_to_every_selected_downstream(
    agent_factory: AgentFactory,
    prior_technical_planning: TechnicalPlanningResult,
) -> None:
    plan = _plan(
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    )

    crew = create_technical_planning_crew(
        specialist_plan=plan,
        agent_factory=agent_factory,
        revision_requests=[
            RevisionRequest(
                target=RevisionTarget.SOLUTION_ARCHITECTURE, issue="x", instructions="y"
            )
        ],
        prior_result=prior_technical_planning,
    )

    assert [t.name for t in crew.tasks] == [
        "solution_architecture",
        "ai_architecture",
        "security_architecture",
        "qa_evaluation",
    ]
