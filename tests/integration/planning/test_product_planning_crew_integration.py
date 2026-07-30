"""Integration test: same-Crew execution wires compact context, not raw drafts.

No live LLM call is made. Building a native ``crewai.Crew`` only assembles
local ``Agent``/``Task`` objects; no network request happens until
``Crew.kickoff()`` is called, which this test never does.

This mirrors ``test_technical_planning_crew_integration.py``'s coverage for
the Product Planning Crew (Product Manager -> Business Analyst -> Market and
GTM Strategist), which previously had no dedicated crew-wiring test at all
despite always running same-Crew on every first-pass consultation.
"""

from __future__ import annotations

from crewai.tasks.task_output import TaskOutput
from pydantic import SecretStr

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.crews.product_planning import create_product_planning_crew
from buildwise.domain.artifact_drafts import ProductDefinitionDraft, RequirementsSpecificationDraft
from buildwise.domain.common import generate_uuid
from fixtures.planning import build_product_planning_inputs


def _offline_settings() -> Settings:
    """Build Settings with a fake OpenAI key so Agent construction succeeds offline."""

    return Settings(
        openai_api_key=SecretStr("sk-test-not-a-real-key"),
        crewai_tracing_enabled=False,
    )


def test_product_planning_crew_includes_market_and_gtm_when_requested() -> None:
    discovery, _ = build_product_planning_inputs()

    settings = _offline_settings()
    agent_factory = AgentFactory(settings=settings)

    crew = create_product_planning_crew(
        discovery_result=discovery,
        include_market_and_gtm=True,
        agent_factory=agent_factory,
        settings=settings,
    )

    assert len(crew.tasks) == 3
    assert len(crew.agents) == 3
    assert [task.name for task in crew.tasks] == [
        "product_definition",
        "requirements_specification",
        "market_and_gtm_strategy",
    ]


def test_same_crew_execution_compresses_context_instead_of_raw_task_output() -> None:
    """Requirements and Market/GTM must hold unresolved placeholders up front.

    Each placeholder must resolve to the compact projection once its source
    task actually completes, mirroring exactly what Process.sequential does
    at real kickoff time — with no raw full-artifact JSON ever appearing in
    a downstream prompt.
    """

    discovery, _ = build_product_planning_inputs()

    settings = _offline_settings()
    agent_factory = AgentFactory(settings=settings)

    crew = create_product_planning_crew(
        discovery_result=discovery,
        include_market_and_gtm=True,
        agent_factory=agent_factory,
        settings=settings,
    )

    product_definition_task, requirements_task, market_and_gtm_task = crew.tasks

    for downstream in (requirements_task, market_and_gtm_task):
        assert "<<" in downstream.description, (
            f"{downstream.name} description should hold an unresolved "
            "placeholder before its upstream task runs."
        )
        assert downstream.context is None or downstream.context == [], (
            f"{downstream.name}.context must stay empty: CrewAI injects "
            "context independently of description, so setting it here "
            "would inject the full raw upstream draft on top of the "
            "compact projection wired through the placeholder."
        )

    product_definition_draft = ProductDefinitionDraft.model_construct(
        product_name="Scheduler",
        vision="v",
        value_proposition="vp",
        problem_statement="p",
        goals=[],
        personas=[],
        features=[],
        roadmap=[],
        product_principles=["ship small"],
        success_metrics=["m"],
        decision="approved",
        decision_rationale="r",
    )
    product_definition_task.callback(
        TaskOutput(description="d", raw="{}", agent="a", pydantic=product_definition_draft)
    )

    assert "<<PRODUCT_DEFINITION_COMPACT_CONTEXT>>" not in requirements_task.description
    assert "<<PRODUCT_DEFINITION_COMPACT_CONTEXT>>" not in market_and_gtm_task.description
    assert '"product_name":"Scheduler"' in requirements_task.description
    # Full draft JSON (roadmap/decision/etc. the downstream tasks don't need)
    # must not have leaked in raw.
    assert product_definition_draft.model_dump_json() not in requirements_task.description
    assert product_definition_draft.model_dump_json() not in market_and_gtm_task.description

    requirements_draft = RequirementsSpecificationDraft.model_construct(
        id=generate_uuid(),
        title="Requirements",
        summary="s",
        scope="s",
        functional_requirements=[],
        non_functional_requirements=[],
    )
    requirements_task.callback(
        TaskOutput(description="d", raw="{}", agent="a", pydantic=requirements_draft)
    )

    assert "<<" not in market_and_gtm_task.description, (
        "every placeholder in the final task must be resolved"
    )
    assert requirements_draft.model_dump_json() not in market_and_gtm_task.description
