"""QA and Evaluation Crew factory.

Combines the QA and Evaluation Architect agent with the QA and Evaluation
task into a single, focused, native CrewAI Crew that produces a
``QAEvaluationPlan``.
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
from buildwise.domain.security import SecurityArchitecture
from buildwise.tasks.qa_evaluation import create_qa_evaluation_task


def create_qa_evaluation_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None,
    security_architecture: SecurityArchitecture | None,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    """Build the QA and Evaluation Crew.

    The Flow should run this Crew after every selected architecture Crew it
    must validate; do not run it concurrently with Security when the QA plan
    needs the final Security output.

    Args:
        requirements: The approved RequirementsSpecification.
        solution_architecture: The approved SolutionArchitecture.
        ai_architecture: The approved AIArchitecture, when selected.
            ``None`` when it was not.
        security_architecture: The approved SecurityArchitecture, when
            selected. ``None`` when it was not.
        agent_factory: Factory used to construct the native QA and
            Evaluation Architect agent.
        settings: Application settings supplying retry and verbosity policy.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``QAEvaluationPlan``.
    """

    agent = agent_factory.create(AgentType.QA_AND_EVALUATION_ARCHITECT)

    task = create_qa_evaluation_task(
        agent=agent,
        requirements=requirements,
        solution_architecture=solution_architecture,
        ai_architecture=ai_architecture,
        security_architecture=security_architecture,
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
