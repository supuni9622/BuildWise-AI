"""Integration test: SpecialistPlanner output feeds the Technical Planning Crew.

No live LLM call is made. Building a native ``crewai.Crew`` only assembles
local ``Agent``/``Task`` objects; no network request happens until
``Crew.kickoff()`` is called, which this test never does.
"""

from __future__ import annotations

from pydantic import SecretStr

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.crews.technical_planning import create_technical_planning_crew
from buildwise.domain.enums import CapabilityType, SpecialistType
from buildwise.flows.state import FlowRuntimeLimits
from buildwise.planning.planner import SpecialistPlanner
from fixtures.planning import build_product_planning_inputs, build_sensitive_data_requirement


def _offline_settings() -> Settings:
    """Build Settings with a fake OpenAI key so Agent construction succeeds offline."""

    return Settings(
        openai_api_key=SecretStr("sk-test-not-a-real-key"),
        crewai_tracing_enabled=False,
    )


def test_technical_planning_crew_matches_specialist_plan() -> None:
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

    selected_specialists = {recommendation.specialist for recommendation in plan.recommendations}
    assert selected_specialists == {
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    }

    settings = _offline_settings()
    agent_factory = AgentFactory(settings=settings)

    crew = create_technical_planning_crew(
        requirements=product_planning.requirements,
        specialist_plan=plan,
        agent_factory=agent_factory,
        settings=settings,
    )

    assert len(crew.tasks) == len(selected_specialists)
    assert len(crew.agents) == len(selected_specialists)
    assert crew.tracing is False


def test_technical_planning_crew_excludes_unselected_specialists() -> None:
    discovery, product_planning = build_product_planning_inputs()

    plan = SpecialistPlanner().create_execution_plan(
        discovery=discovery,
        product_planning=product_planning,
        limits=FlowRuntimeLimits(),
    )

    selected_specialists = {recommendation.specialist for recommendation in plan.recommendations}
    assert selected_specialists == {SpecialistType.SOLUTION_ARCHITECTURE}

    settings = _offline_settings()
    agent_factory = AgentFactory(settings=settings)

    crew = create_technical_planning_crew(
        requirements=product_planning.requirements,
        specialist_plan=plan,
        agent_factory=agent_factory,
        settings=settings,
    )

    assert len(crew.tasks) == 1
    assert len(crew.agents) == 1
