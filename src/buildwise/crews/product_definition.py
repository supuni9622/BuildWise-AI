"""Product Definition Crew factory.

Combines the Product Manager agent with the Product Definition task into a
single, focused, native CrewAI Crew that produces a ``ProductDefinition``.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import AgentType
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.product_definition import create_product_definition_task


def create_product_definition_crew(
    *,
    discovery_result: DiscoveryResult,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the Product Definition Crew.

    The supplied ``discovery_result`` must already be approved (or approved
    with documented limitations) by the Flow before this Crew is invoked.

    Args:
        discovery_result: The completed DiscoveryResult from the Discovery
            Crew.
        agent_factory: Factory used to construct the native Product Manager
            agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer, when this Crew is being rerun to fix a specific
            issue rather than generate a first draft.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``ProductDefinition``.
    """

    agent = agent_factory.create(AgentType.PRODUCT_MANAGER)

    task = create_product_definition_task(
        agent=agent,
        discovery_result=discovery_result,
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
