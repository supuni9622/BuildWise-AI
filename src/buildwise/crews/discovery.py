"""Discovery Crew factory.

Combines the Product Discovery Analyst agent with the Discovery task into a
single, focused, native CrewAI Crew that produces a ``DiscoveryResult``.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentType
from buildwise.domain.intake import ProductIdeaContext, ProductIdeaRequest
from buildwise.tasks.discovery import create_discovery_task


def create_discovery_crew(
    *,
    product_idea: ProductIdeaRequest,
    agent_factory: AgentFactory,
    settings: Settings,
    clarification_context: ProductIdeaContext | None = None,
) -> Crew:
    """Build the Discovery Crew.

    Args:
        product_idea: Raw intake payload submitted by the user.
        agent_factory: Factory used to construct the native Product
            Discovery Analyst agent.
        settings: Application settings supplying retry and verbosity policy.
        clarification_context: Prior clarification answers, when Discovery
            is being re-run after the Flow resumed from a clarification
            pause.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``DiscoveryResult``.
    """

    agent = agent_factory.create(AgentType.PRODUCT_DISCOVERY_ANALYST)

    task = create_discovery_task(
        agent=agent,
        product_idea=product_idea,
        clarification_context=clarification_context,
        guardrail_max_retries=settings.max_retries_per_operation,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
    )
