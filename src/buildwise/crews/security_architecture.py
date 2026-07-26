"""Security Architecture Crew factory.

Combines the Security Architect agent with the Security Architecture task
into a single, focused, native CrewAI Crew that produces a
``SecurityArchitecture``. The Flow invokes this Crew only when specialist
planning selects security architecture.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.enums import AgentType
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.security_architecture import create_security_architecture_task


def create_security_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the Security Architecture Crew.

    Args:
        requirements: The approved RequirementsSpecification.
        solution_architecture: The approved SolutionArchitecture.
        ai_architecture: The approved AIArchitecture, when AI architecture
            was selected. ``None`` when it was not; the Crew remains fully
            valid without it.
        agent_factory: Factory used to construct the native Security
            Architect agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``SecurityArchitecture``.
    """

    agent = agent_factory.create(AgentType.SECURITY_ARCHITECT)

    task = create_security_architecture_task(
        agent=agent,
        requirements=requirements,
        solution_architecture=solution_architecture,
        ai_architecture=ai_architecture,
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
