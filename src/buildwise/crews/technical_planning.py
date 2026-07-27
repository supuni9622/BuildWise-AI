"""Technical Planning Crew factory.

Combines the Solution Architect with the conditionally selected AI
Architect, Security Architect, and QA & Evaluation Architect into one
collaborative native CrewAI Crew that produces the complete technical
implementation plan for the specialists chosen by the deterministic
specialist planner.

Task order always follows the dependency chain:

    Solution Architecture -> AI Architecture -> Security Architecture -> QA
"""

from __future__ import annotations

from crewai import Agent, Crew, CrewOutput, Process, Task

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import SessionId
from buildwise.domain.enums import AgentType, RevisionTarget, SpecialistType
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.tasks.ai_architecture import create_ai_architecture_task
from buildwise.tasks.qa_evaluation import create_qa_evaluation_task
from buildwise.tasks.security_architecture import create_security_architecture_task
from buildwise.tasks.solution_architecture import create_solution_architecture_task

_TECHNICAL_SPECIALISTS = {
    SpecialistType.SOLUTION_ARCHITECTURE,
    SpecialistType.AI_ARCHITECTURE,
    SpecialistType.SECURITY_ARCHITECTURE,
    SpecialistType.QA_AND_EVALUATION,
}


def create_technical_planning_crew(
    *,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_requests: list[RevisionRequest] | None = None,
    revision_specialists: set[SpecialistType] | None = None,
    previous_result: TechnicalPlanningResult | None = None,
) -> Crew:
    """Build the Technical Planning Crew.

    Only the specialists selected by ``specialist_plan`` are created. AI
    Architecture, Security Architecture, and QA & Evaluation each depend on
    Solution Architecture running first inside this same Crew, so the plan
    must include Solution Architecture whenever any of them are selected.

    Args:
        requirements: The approved RequirementsSpecification.
        specialist_plan: The deterministic specialist selection plan
            produced after Product Planning.
        agent_factory: Factory used to construct native specialist agents.
        settings: Application settings supplying retry and verbosity policy.
        revision_requests: Bounded revision requests from the Lead Reviewer.
            Each request is routed only to the task it targets
            (``solution_architecture``, ``ai_architecture``,
            ``security_architecture``, or ``qa_and_evaluation``); at most
            one request per target is supported in a single Crew run.

    Returns:
        A native ``crewai.Crew`` whose task outputs are, in dependency
        order, the ``SolutionArchitecture`` and any selected
        ``AIArchitecture``, ``SecurityArchitecture``, and
        ``QAEvaluationPlan``.
    """

    selected = _selected_specialists(specialist_plan)
    selected_technical = selected.intersection(_TECHNICAL_SPECIALISTS)
    executing = selected_technical if revision_specialists is None else revision_specialists

    if not executing or not executing.issubset(selected_technical):
        raise ValueError("Revision specialists must be a non-empty subset of the selected plan.")

    if not selected_technical:
        raise ValueError(
            "SpecialistExecutionPlan does not select any technical "
            "specialist for the Technical Planning Crew."
        )

    include_solution = SpecialistType.SOLUTION_ARCHITECTURE in executing
    include_ai = SpecialistType.AI_ARCHITECTURE in executing
    include_security = SpecialistType.SECURITY_ARCHITECTURE in executing
    include_qa = SpecialistType.QA_AND_EVALUATION in executing

    partial_without_context = (
        (include_ai or include_security or include_qa)
        and not include_solution
        and previous_result is None
    )
    if partial_without_context:
        raise ValueError("A partial technical revision requires the previous technical result.")

    agents: list[Agent] = []
    tasks: list[Task] = []

    solution_task: Task | None = None
    ai_task: Task | None = None
    security_task: Task | None = None

    if include_solution:
        solution_agent = agent_factory.create(AgentType.SOLUTION_ARCHITECT)
        solution_task = create_solution_architecture_task(
            agent=solution_agent,
            requirements=requirements,
            revision_request=_find_revision(
                revision_requests, RevisionTarget.SOLUTION_ARCHITECTURE
            ),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(solution_agent)
        tasks.append(solution_task)

    if include_ai:
        ai_agent = agent_factory.create(AgentType.AI_ARCHITECT)
        ai_task = create_ai_architecture_task(
            agent=ai_agent,
            requirements=requirements,
            solution_architecture_task=solution_task,
            solution_architecture=(
                previous_result.solution_architecture
                if solution_task is None and previous_result
                else None
            ),
            revision_request=_find_revision(revision_requests, RevisionTarget.AI_ARCHITECTURE),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(ai_agent)
        tasks.append(ai_task)

    if include_security:
        security_agent = agent_factory.create(AgentType.SECURITY_ARCHITECT)
        security_task = create_security_architecture_task(
            agent=security_agent,
            requirements=requirements,
            solution_architecture_task=solution_task,
            solution_architecture=(
                previous_result.solution_architecture
                if solution_task is None and previous_result
                else None
            ),
            ai_architecture_task=ai_task,
            ai_architecture=(
                previous_result.ai_architecture
                if ai_task is None and previous_result is not None
                else None
            ),
            revision_request=_find_revision(
                revision_requests, RevisionTarget.SECURITY_ARCHITECTURE
            ),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(security_agent)
        tasks.append(security_task)

    if include_qa:
        qa_agent = agent_factory.create(AgentType.QA_AND_EVALUATION_ARCHITECT)
        qa_task = create_qa_evaluation_task(
            agent=qa_agent,
            requirements=requirements,
            solution_architecture_task=solution_task,
            solution_architecture=(
                previous_result.solution_architecture
                if solution_task is None and previous_result
                else None
            ),
            ai_architecture_task=ai_task,
            ai_architecture=(
                previous_result.ai_architecture
                if ai_task is None and previous_result is not None
                else None
            ),
            security_architecture_task=security_task,
            security_architecture=(
                previous_result.security_architecture
                if security_task is None and previous_result is not None
                else None
            ),
            revision_request=_find_revision(revision_requests, RevisionTarget.QA_AND_EVALUATION),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(qa_agent)
        tasks.append(qa_task)

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
        tracing=settings.crewai_tracing_enabled,
    )


def _selected_specialists(plan: SpecialistExecutionPlan) -> set[SpecialistType]:
    """Return the unique set of specialists selected by a plan.

    Raises:
        ValueError: If the plan lists the same specialist more than once.
    """

    specialists = [recommendation.specialist for recommendation in plan.recommendations]

    if len(specialists) != len(set(specialists)):
        raise ValueError("SpecialistExecutionPlan.recommendations contains duplicate specialists.")

    return set(specialists)


def _find_revision(
    revision_requests: list[RevisionRequest] | None,
    target: RevisionTarget,
) -> RevisionRequest | None:
    """Return the single revision request targeting one RevisionTarget, if any."""

    if not revision_requests:
        return None

    matches = [request for request in revision_requests if request.target is target]

    if not matches:
        return None

    if len(matches) > 1:
        raise ValueError(
            f"Multiple revision requests target '{target.value}'; only one "
            "revision request per target is supported in a single Crew run."
        )

    return matches[0]


def assemble_technical_planning_result(
    crew_output: CrewOutput,
    *,
    session_id: SessionId,
    previous_result: TechnicalPlanningResult | None = None,
) -> TechnicalPlanningResult:
    """Assemble a ``TechnicalPlanningResult`` from a completed Crew run.

    Matches each task output by its structured type rather than by
    position, so this works regardless of which optional specialists were
    selected. The Flow should call this immediately after
    ``crew.kickoff()`` for a Crew built by
    ``create_technical_planning_crew``, then call
    ``TechnicalPlanningResult.validate_specialist_selection`` to cross-check
    the result against the ``SpecialistExecutionPlan`` that built the Crew.

    Args:
        crew_output: The native ``CrewOutput`` returned by
            ``Crew.kickoff()``.
        session_id: The consulting session that owns these artifacts.

    Returns:
        A schema-valid ``TechnicalPlanningResult``.

    Raises:
        ValueError: If the required SolutionArchitecture task output is
            missing, or a task produced an output of an unexpected type.
    """

    solution_architecture = previous_result.solution_architecture if previous_result else None
    ai_architecture = previous_result.ai_architecture if previous_result else None
    security_architecture = previous_result.security_architecture if previous_result else None
    qa_evaluation = previous_result.qa_evaluation if previous_result else None

    for task_output in crew_output.tasks_output:
        output = task_output.pydantic

        if isinstance(output, SolutionArchitecture):
            solution_architecture = output
        elif isinstance(output, AIArchitecture):
            ai_architecture = output
        elif isinstance(output, SecurityArchitecture):
            security_architecture = output
        elif isinstance(output, QAEvaluationPlan):
            qa_evaluation = output
        else:
            raise ValueError(
                "Technical Planning Crew produced an unexpected task output "
                f"type: {type(output).__name__}."
            )

    if solution_architecture is None:
        raise ValueError(
            "Technical Planning Crew output is missing a SolutionArchitecture task output."
        )

    return TechnicalPlanningResult(
        session_id=session_id,
        solution_architecture=solution_architecture,
        ai_architecture=ai_architecture,
        security_architecture=security_architecture,
        qa_evaluation=qa_evaluation,
    )
