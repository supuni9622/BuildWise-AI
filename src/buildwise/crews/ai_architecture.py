"""AI Architecture Crew factory.

Combines the AI Architect agent with the AI Architecture task into a single,
focused, native CrewAI Crew that produces an ``AIArchitecture``. The Flow
invokes this Crew only when specialist planning selects AI architecture.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.enums import AgentType
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.ai_architecture import create_ai_architecture_task


def create_ai_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the AI Architecture Crew.

    The Flow must not invoke this Crew without an approved
    SolutionArchitecture: the AI design must fit into the already-approved
    general architecture rather than redesigning it.

    Args:
        requirements: The approved RequirementsSpecification.
        solution_architecture: The approved SolutionArchitecture.
        agent_factory: Factory used to construct the native AI Architect
            agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing an
        ``AIArchitecture``.
    """

    agent = agent_factory.create(AgentType.AI_ARCHITECT)

    task = create_ai_architecture_task(
        agent=agent,
        requirements=requirements,
        solution_architecture=solution_architecture,
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
