"""Technical Planning Crew: Solution Architect -> optional AI/Security/QA specialists.

Composition is entirely dynamic, driven by ``SpecialistExecutionPlan`` from
``buildwisev2.planning`` — this Crew never decides which specialists run.

Revision-aware composition follows the same cascade rule as the Product
Planning Crew: a task regenerates only when its own ``RevisionTarget`` was
requested, or an upstream dependency within this Crew is also
regenerating. Non-regenerating tasks are skipped; their prior artifact
(from ``prior_result``) is reused as static context for whatever does run.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from buildwisev2.agents import AgentFactory, AgentType
from buildwisev2.config import Settings, get_settings
from buildwisev2.crews._shared import find_revision
from buildwisev2.domain.common import SpecialistType
from buildwisev2.domain.planning_results import TechnicalPlanningResult
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.review import RevisionRequest, RevisionTarget
from buildwisev2.domain.specialist_planning import SpecialistExecutionPlan
from buildwisev2.tasks.ai_architecture import create_ai_architecture_task
from buildwisev2.tasks.qa_evaluation import create_qa_evaluation_task
from buildwisev2.tasks.security_architecture import create_security_architecture_task
from buildwisev2.tasks.solution_architecture import create_solution_architecture_task


def create_technical_planning_crew(
    *,
    specialist_plan: SpecialistExecutionPlan,
    agent_factory: AgentFactory,
    settings: Settings | None = None,
    revision_requests: list[RevisionRequest] | None = None,
    prior_result: TechnicalPlanningResult | None = None,
) -> Crew:
    """Compose Solution Architecture plus every conditionally selected specialist.

    ``prior_result`` is required whenever ``revision_requests`` is
    non-empty, so tasks that are not being regenerated this round have a
    prior artifact to reuse.
    """

    settings = settings or get_settings()
    selected = specialist_plan.selected_specialists()

    if SpecialistType.SOLUTION_ARCHITECTURE not in selected:
        raise ValueError(
            "SpecialistExecutionPlan does not select Solution Architecture; "
            "the Technical Planning Crew cannot be constructed without it."
        )
    if revision_requests and prior_result is None:
        raise ValueError("prior_result is required when revision_requests is supplied.")

    targets = {request.target for request in (revision_requests or [])}
    regenerate_solution = not revision_requests or RevisionTarget.SOLUTION_ARCHITECTURE in targets
    regenerate_ai = SpecialistType.AI_ARCHITECTURE in selected and (
        not revision_requests or RevisionTarget.AI_ARCHITECTURE in targets or regenerate_solution
    )
    regenerate_security = SpecialistType.SECURITY_ARCHITECTURE in selected and (
        not revision_requests
        or RevisionTarget.SECURITY_ARCHITECTURE in targets
        or regenerate_solution
        or regenerate_ai
    )
    regenerate_qa = SpecialistType.QA_AND_EVALUATION in selected and (
        not revision_requests
        or RevisionTarget.QA_EVALUATION in targets
        or regenerate_solution
        or regenerate_ai
        or regenerate_security
    )

    agents: list[Agent] = []
    tasks: list[Task] = []

    solution_task: Task | None = None
    if regenerate_solution:
        solution_architect = agent_factory.create(AgentType.SOLUTION_ARCHITECT)
        solution_task = create_solution_architecture_task(
            agent=solution_architect,
            revision_request=find_revision(revision_requests, RevisionTarget.SOLUTION_ARCHITECTURE),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(solution_architect)
        tasks.append(solution_task)
    prior_solution = prior_result.solution_architecture if prior_result is not None else None

    ai_task: Task | None = None
    if regenerate_ai:
        ai_architect = agent_factory.create(AgentType.AI_ARCHITECT)
        ai_task = create_ai_architecture_task(
            agent=ai_architect,
            solution_architecture_task=solution_task,
            prior_solution_architecture=None if solution_task is not None else prior_solution,
            revision_request=find_revision(revision_requests, RevisionTarget.AI_ARCHITECTURE),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(ai_architect)
        tasks.append(ai_task)
    prior_ai = (
        prior_result.ai_architecture
        if prior_result is not None and SpecialistType.AI_ARCHITECTURE in selected
        else None
    )

    security_task: Task | None = None
    if regenerate_security:
        security_architect = agent_factory.create(AgentType.SECURITY_ARCHITECT)
        security_task = create_security_architecture_task(
            agent=security_architect,
            solution_architecture_task=solution_task,
            prior_solution_architecture=None if solution_task is not None else prior_solution,
            ai_architecture_task=ai_task,
            prior_ai_architecture=None if ai_task is not None else prior_ai,
            revision_request=find_revision(revision_requests, RevisionTarget.SECURITY_ARCHITECTURE),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(security_architect)
        tasks.append(security_task)
    prior_security = (
        prior_result.security_architecture
        if prior_result is not None and SpecialistType.SECURITY_ARCHITECTURE in selected
        else None
    )

    if regenerate_qa:
        qa_architect = agent_factory.create(AgentType.QA_AND_EVALUATION_ARCHITECT)
        qa_task = create_qa_evaluation_task(
            agent=qa_architect,
            solution_architecture_task=solution_task,
            prior_solution_architecture=None if solution_task is not None else prior_solution,
            ai_architecture_task=ai_task,
            prior_ai_architecture=None if ai_task is not None else prior_ai,
            security_architecture_task=security_task,
            prior_security_architecture=None if security_task is not None else prior_security,
            revision_request=find_revision(revision_requests, RevisionTarget.QA_EVALUATION),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(qa_architect)
        tasks.append(qa_task)

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=settings.crew_cache,
        memory=settings.crew_memory,
    )


def build_technical_planning_kickoff_inputs(
    *,
    requirements: RequirementsSpecification,
    prior_result: TechnicalPlanningResult | None = None,
) -> dict[str, str]:
    """Build the ``crew.kickoff(inputs=...)`` dict for the Technical Planning Crew.

    Always includes the prior-artifact placeholders when ``prior_result``
    is supplied — harmless when the selected Tasks this round don't
    reference them, and required when they do.
    """

    inputs = {"requirements": requirements.model_dump_json(indent=2)}
    if prior_result is not None:
        inputs["solution_architecture_context"] = (
            prior_result.solution_architecture.model_dump_json(indent=2)
        )
        inputs["ai_architecture_context"] = (
            prior_result.ai_architecture.model_dump_json(indent=2)
            if prior_result.ai_architecture is not None
            else "Not selected."
        )
        inputs["security_architecture_context"] = (
            prior_result.security_architecture.model_dump_json(indent=2)
            if prior_result.security_architecture is not None
            else "Not selected."
        )
    return inputs
