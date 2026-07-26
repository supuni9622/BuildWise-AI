"""Solution Architecture Crew factory.

Combines the Solution Architect agent with the Solution Architecture task
into a single, focused, native CrewAI Crew that produces a
``SolutionArchitecture``.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentType
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.solution_architecture import create_solution_architecture_task


def create_solution_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the Solution Architecture Crew.

    This Crew runs after Requirements and normally before the AI
    Architecture, Security Architecture, and QA & Evaluation Crews.

    Args:
        requirements: The approved RequirementsSpecification.
        agent_factory: Factory used to construct the native Solution
            Architect agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``SolutionArchitecture``.
    """

    agent = agent_factory.create(AgentType.SOLUTION_ARCHITECT)

    task = create_solution_architecture_task(
        agent=agent,
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
