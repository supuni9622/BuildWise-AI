"""Integration test: SpecialistPlanner output feeds the Technical Planning Crew.

No live LLM call is made. Building a native ``crewai.Crew`` only assembles
local ``Agent``/``Task`` objects; no network request happens until
``Crew.kickoff()`` is called, which this test never does.
"""

from __future__ import annotations

from crewai.tasks.task_output import TaskOutput
from pydantic import SecretStr

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.crews.technical_planning import create_technical_planning_crew
from buildwise.domain.artifact_drafts import AIArchitectureDraft, SolutionArchitectureDraft
from buildwise.domain.enums import CapabilityType, SpecialistType
from buildwise.domain.security import SecurityArchitecture
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
    assert all(agent.reasoning is False for agent in crew.agents)
    assert all(agent.max_iter == 1 for agent in crew.agents)
    assert all(agent.max_retry_limit == 0 for agent in crew.agents)


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


def test_same_crew_execution_compresses_context_instead_of_raw_task_output() -> None:
    """The default execution path chains all 4 specialists in one Crew.

    Before this only matters when it stays wired through the whole chain:
    every downstream description must start out holding a placeholder (not
    the full raw upstream draft), and each placeholder must resolve to the
    compact projection once its source task actually completes — mirroring
    exactly what Process.sequential does at real kickoff time.
    """

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

    settings = _offline_settings()
    agent_factory = AgentFactory(settings=settings)

    crew = create_technical_planning_crew(
        requirements=product_planning.requirements,
        specialist_plan=plan,
        agent_factory=agent_factory,
        settings=settings,
    )

    solution_task, ai_task, security_task, qa_task = crew.tasks

    for downstream in (ai_task, security_task, qa_task):
        assert "<<" in downstream.description, (
            f"{downstream.name} description should hold an unresolved "
            "placeholder before its upstream task runs."
        )
        assert downstream.context == [], (
            f"{downstream.name}.context must be an explicit []: CrewAI "
            "injects context independently of description (and its "
            "NOT_SPECIFIED default aggregates every prior task's raw "
            "output, not just the immediate upstream one), so anything "
            "other than [] re-adds the full raw output this wiring exists "
            "to avoid, on top of the compact projection."
        )

    solution_draft = SolutionArchitectureDraft.model_construct(
        architecture_style="microservices",
        architecture_style_rationale="scales independently",
        components=[],
        connections=[],
        deployment_units=[],
        data_architecture_summary="s",
        integration_architecture_summary="s",
        deployment_summary="s",
        operational_summary="s",
    )
    solution_task.callback(
        TaskOutput(description="d", raw="{}", agent="a", pydantic=solution_draft)
    )

    assert "<<SOLUTION_ARCHITECTURE_COMPACT_CONTEXT>>" not in ai_task.description
    assert "<<SOLUTION_ARCHITECTURE_COMPACT_CONTEXT>>" not in security_task.description
    assert "<<SOLUTION_ARCHITECTURE_COMPACT_CONTEXT>>" not in qa_task.description
    assert '"architecture_style":"microservices"' in ai_task.description
    # Full draft JSON (hundreds of unrelated fields) must not have leaked in raw.
    assert solution_draft.model_dump_json() not in ai_task.description

    ai_draft = AIArchitectureDraft.model_construct(
        capabilities=[],
        tool_policies=[],
        agent_workflows=[],
        rag_designs=[],
        guardrails=[],
        evaluation_metrics=[],
        human_oversight_strategy="s",
        fallback_strategy="s",
        privacy_strategy="s",
        security_boundary_summary="s",
    )
    ai_task.callback(TaskOutput(description="d", raw="{}", agent="a", pydantic=ai_draft))

    assert "<<AI_ARCHITECTURE_COMPACT_CONTEXT>>" not in security_task.description
    assert "<<AI_ARCHITECTURE_COMPACT_CONTEXT>>" not in qa_task.description

    security_architecture = SecurityArchitecture.model_construct(
        executive_summary="s",
        controls=[],
        security_requirements=[],
        validations=[],
        assumptions=[],
        recommendations=[],
        notes=None,
    )
    security_task.callback(
        TaskOutput(description="d", raw="{}", agent="a", pydantic=security_architecture)
    )

    assert "<<SECURITY_ARCHITECTURE_COMPACT_CONTEXT>>" not in qa_task.description
    assert "<<" not in qa_task.description, "every placeholder in the final task must be resolved"
