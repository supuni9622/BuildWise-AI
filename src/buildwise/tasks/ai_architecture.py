"""AI Architecture task factory.

Creates the native CrewAI Task assigned to the AI Architect. The task is only
created when specialist planning selects AI architecture: it defines AI
capabilities, model strategy, prompts, tools, agent designs, RAG, guardrails,
evaluation, and observability for the approved solution architecture.

The task supports two input modes for ``solution_architecture``: same-Crew
native task context (when composed inside the Technical Planning Crew right
after the Solution Architecture task) or a literal structured value (when
Solution Architecture already completed in a separate Crew).
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.artifact_drafts import AIArchitectureDraft
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.planning.specialist_context import AIArchitectContext, RequirementsProjection
from buildwise.tasks.context_wiring import SOLUTION_CONTEXT_PLACEHOLDER
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    require_self_consistent_draft,
)
from buildwise.tasks.instructions import IDENTIFIER_RULES
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_ai_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture_task: Task | None = None,
    solution_architecture: SolutionArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the AI Architecture task for the AI Architect.

    Only create this task when specialist planning selects AI architecture.
    Exactly one of ``solution_architecture_task`` or ``solution_architecture``
    must be supplied. Pass the task when Solution Architecture executes in
    the same Crew immediately before this task; pass the structured value
    when Solution Architecture already completed in a separate Crew.

    Args:
        agent: Native CrewAI agent created for ``AgentType.AI_ARCHITECT``.
        requirements: The approved RequirementsSpecification.
        solution_architecture_task: The Solution Architecture task, when
            executing in the same Crew.
        solution_architecture: The completed SolutionArchitecture, when it
            ran in a separate Crew.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing an ``AIArchitecture``.
    """

    if agent is None:
        raise ValueError("create_ai_architecture_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    if solution_architecture_task is None and solution_architecture is None:
        raise ValueError(
            "create_ai_architecture_task requires either "
            "solution_architecture_task or solution_architecture."
        )

    if solution_architecture_task is not None and solution_architecture is not None:
        raise ValueError(
            "create_ai_architecture_task accepts only one of "
            "solution_architecture_task or solution_architecture, not both."
        )

    architecture_section = (
        f"Requirements: {RequirementsProjection.from_artifact(requirements).model_dump_json()}\n"
        f"SolutionArchitecture: {SOLUTION_CONTEXT_PLACEHOLDER}"
        if solution_architecture_task is not None
        else AIArchitectContext.build(
            requirements,
            solution_architecture,  # type: ignore[arg-type]
        ).model_dump_json()
    )

    description = (
        "Objective: Design the AI-specific architecture for the AI "
        "capabilities identified in the approved requirements and solution "
        "architecture.\n\n"
        "Available structured context:\n"
        f"{architecture_section}\n\n"
        "Required decisions:\n"
        "- Identify every AI capability the product requires and justify "
        "why a deterministic, non-AI approach is insufficient.\n"
        "- Define model requirements and model selections for every "
        "capability, including a model strategy and rationale.\n"
        "- Define prompt contracts, tool policies, agent designs, and agent "
        "workflows for agentic capabilities.\n"
        "- Define a RAG design for every RAG capability.\n"
        "- Define AI guardrails covering every capability and agent design.\n"
        "- Define evaluation metrics, datasets, and evaluation requirements "
        "covering every capability.\n"
        "- Define AI observability requirements, human oversight, fallback, "
        "cost control, and privacy strategy.\n"
        "- Identify AI-specific risks and AI-owned cost estimates.\n\n"
        "Required output: A schema-valid AIArchitectureDraft where every "
        "AI capability has both model-requirement coverage and evaluation "
        "coverage.\n\n"
        f"{IDENTIFIER_RULES}\n"
        "Important boundaries:\n"
        "- Do not redefine general application components, deployment "
        "topology, or non-AI technology choices; those belong to "
        "SolutionArchitecture.\n"
        "- Do not design the full security architecture or QA strategy.\n\n"
        "Failure or uncertainty handling: If an AI capability cannot be "
        "responsibly designed yet, set decision to 'requires_clarification' "
        "or 'cannot_proceed' with the required open_questions or "
        "limitations."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid AIArchitectureDraft JSON object matching the compact "
        "draft model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(AIArchitectureDraft),
        require_self_consistent_draft(AIArchitectureDraft, AIArchitecture),
    )

    task_kwargs: dict[str, object] = {
        "name": "ai_architecture",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "output_pydantic": AIArchitectureDraft,
        "guardrails": guardrails,
        "guardrail_max_retries": guardrail_max_retries,
        # See tasks/context_wiring.py: context is always fully embedded in
        # description above, so this must be an explicit [], not left
        # unset, or CrewAI's NOT_SPECIFIED default injects raw output from
        # every other task the Crew has run so far.
        "context": [],
    }

    return Task(**task_kwargs)
