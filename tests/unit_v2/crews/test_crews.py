"""Unit tests verifying Crew composition. No live LLM calls — Agent/Task/Crew
construction never calls a model, it only configures native CrewAI objects.
"""

from __future__ import annotations

import os

import pytest
from crewai import Crew, Process

from buildwisev2.agents.factory import AgentFactory
from buildwisev2.crews.discovery import create_discovery_crew
from buildwisev2.crews.lead_review import create_lead_review_crew
from buildwisev2.crews.product_planning import create_product_planning_crew
from buildwisev2.crews.technical_planning import create_technical_planning_crew
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    BudgetDecisionType,
    SpecialistExecutionPlan,
)

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


@pytest.fixture
def agent_factory() -> AgentFactory:
    return AgentFactory()


def _plan(*specialists) -> SpecialistExecutionPlan:
    from buildwisev2.domain.common import SpecialistType
    from buildwisev2.domain.specialist_planning import (
        EffortLevel,
        SpecialistRecommendation,
        SpecialistSelectionReason,
    )

    recommendations = [
        SpecialistRecommendation(
            specialist=SpecialistType(s),
            required=s == "solution_architecture",
            reason=SpecialistSelectionReason.MANDATORY,
            explanation="test",
            estimated_effort=EffortLevel.MEDIUM,
        )
        for s in specialists
    ]
    return SpecialistExecutionPlan(
        recommendations=recommendations,
        execution_groups=[],
        dependencies=[],
        budget=BudgetDecision(decision=BudgetDecisionType.APPROVED, explanation="ok"),
        execution_summary="test",
    )


def test_discovery_crew_is_single_agent_single_task(agent_factory: AgentFactory) -> None:
    crew = create_discovery_crew(agent_factory=agent_factory)

    assert isinstance(crew, Crew)
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
    assert crew.process == Process.sequential
    assert crew.memory is False


def test_product_planning_crew_without_market_has_two_agents(agent_factory: AgentFactory) -> None:
    crew = create_product_planning_crew(agent_factory=agent_factory, include_market_and_gtm=False)

    assert [t.name for t in crew.tasks] == ["product_definition", "requirements"]
    assert len(crew.agents) == 2


def test_product_planning_crew_with_market_has_three_agents_and_context_wiring(
    agent_factory: AgentFactory,
) -> None:
    crew = create_product_planning_crew(agent_factory=agent_factory, include_market_and_gtm=True)

    assert [t.name for t in crew.tasks] == ["market_and_gtm", "product_definition", "requirements"]
    assert len(crew.agents) == 3
    product_task = crew.tasks[1]
    requirements_task = crew.tasks[2]
    assert product_task.context == [crew.tasks[0]]
    assert requirements_task.context == [product_task]


def test_technical_planning_crew_requires_solution_architecture(
    agent_factory: AgentFactory,
) -> None:
    with pytest.raises(ValueError):
        create_technical_planning_crew(specialist_plan=_plan(), agent_factory=agent_factory)


def test_technical_planning_crew_lightweight_plan_has_only_solution(
    agent_factory: AgentFactory,
) -> None:
    crew = create_technical_planning_crew(
        specialist_plan=_plan("solution_architecture"),
        agent_factory=agent_factory,
    )

    assert [t.name for t in crew.tasks] == ["solution_architecture"]


def test_technical_planning_crew_full_ai_plan_wires_dependencies_in_order(
    agent_factory: AgentFactory,
) -> None:
    crew = create_technical_planning_crew(
        specialist_plan=_plan(
            "solution_architecture",
            "ai_architecture",
            "security_architecture",
            "qa_and_evaluation",
        ),
        agent_factory=agent_factory,
    )

    names = [t.name for t in crew.tasks]
    assert names == [
        "solution_architecture",
        "ai_architecture",
        "security_architecture",
        "qa_evaluation",
    ]
    solution_task, ai_task, security_task, qa_task = crew.tasks
    assert ai_task.context == [solution_task]
    assert security_task.context == [solution_task, ai_task]
    assert qa_task.context == [solution_task, ai_task, security_task]


def test_technical_planning_crew_security_only_plan_skips_ai(agent_factory: AgentFactory) -> None:
    crew = create_technical_planning_crew(
        specialist_plan=_plan("solution_architecture", "security_architecture"),
        agent_factory=agent_factory,
    )

    names = [t.name for t in crew.tasks]
    assert names == ["solution_architecture", "security_architecture"]
    solution_task, security_task = crew.tasks
    assert security_task.context == [solution_task]


def test_lead_review_crew_is_single_agent_single_task(agent_factory: AgentFactory) -> None:
    crew = create_lead_review_crew(agent_factory=agent_factory)

    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
    assert crew.tasks[0].name == "lead_review"
