"""Market and GTM Crew factory.

Combines the Market and GTM Strategist agent with the Market and GTM task
into a single, focused, native CrewAI Crew that produces a
``MarketAndGTMStrategy``. The agent's web_search and web_scraper tools are
attached by the Agent Factory from the agent contract; this Crew does not
instantiate or restrict them.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentType
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.market_and_gtm import create_market_and_gtm_task


def create_market_and_gtm_crew(
    *,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the Market and GTM Crew.

    This Crew may run independently once Product Definition and Requirements
    are available; the Flow decides whether to run it concurrently with the
    technical specialist Crews.

    Args:
        product_definition: The approved ProductDefinition.
        requirements: The approved RequirementsSpecification.
        agent_factory: Factory used to construct the native Market and GTM
            Strategist agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``MarketAndGTMStrategy``.
    """

    agent = agent_factory.create(AgentType.MARKET_AND_GTM_STRATEGIST)

    task = create_market_and_gtm_task(
        agent=agent,
        product_definition=product_definition,
        requirements=requirements,
        revision_request=revision_request,
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
