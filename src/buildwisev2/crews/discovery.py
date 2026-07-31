"""Discovery Crew: one Product Discovery Analyst, one Discovery Task."""

from __future__ import annotations

from crewai import Crew, Process

from buildwisev2.agents import AgentFactory, AgentType
from buildwisev2.config import Settings, get_settings
from buildwisev2.domain.intake import ProductIdeaContext, ProductIdeaRequest
from buildwisev2.tasks.discovery import create_discovery_task


def create_discovery_crew(
    *,
    agent_factory: AgentFactory,
    settings: Settings | None = None,
) -> Crew:
    """Convert a product idea and optional clarification answers into a
    structured ``DiscoveryResult``. Does not call ``kickoff`` — the Flow
    invokes execution and reads ``CrewOutput.pydantic``.
    """

    settings = settings or get_settings()
    agent = agent_factory.create(AgentType.PRODUCT_DISCOVERY_ANALYST)
    task = create_discovery_task(
        agent=agent,
        guardrail_max_retries=settings.max_retries_per_operation,
    )
    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=settings.crew_cache,
        memory=settings.crew_memory,
    )


def build_discovery_kickoff_inputs(
    *,
    product_idea: ProductIdeaRequest,
    clarification_context: ProductIdeaContext | None = None,
) -> dict[str, str]:
    """Build the ``crew.kickoff(inputs=...)`` dict expected by the Discovery Task."""

    return {
        "product_idea": product_idea.model_dump_json(indent=2),
        "clarification_context": (
            clarification_context.model_dump_json(indent=2)
            if clarification_context is not None
            else "None yet."
        ),
    }
