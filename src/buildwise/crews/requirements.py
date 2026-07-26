"""Requirements Crew factory.

Combines the Business Analyst agent with the Requirements task into a
single, focused, native CrewAI Crew that produces a
``RequirementsSpecification``.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentType
from buildwise.domain.product import ProductDefinition
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.requirements import create_requirements_task


def create_requirements_crew(
    *,
    product_definition: ProductDefinition,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the Requirements Crew.

    Args:
        product_definition: The completed ProductDefinition from the Product
            Definition Crew.
        agent_factory: Factory used to construct the native Business Analyst
            agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``RequirementsSpecification``.
    """

    agent = agent_factory.create(AgentType.BUSINESS_ANALYST)

    task = create_requirements_task(
        agent=agent,
        product_definition=product_definition,
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
