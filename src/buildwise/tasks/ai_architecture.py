"""AI Architecture task factory.

Creates the native CrewAI Task assigned to the AI Architect. The task is only
created when specialist planning selects AI architecture: it defines AI
capabilities, model strategy, prompts, tools, agent designs, RAG, guardrails,
evaluation, and observability for the approved solution architecture.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    run_domain_validator,
)
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_ai_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the AI Architecture task for the AI Architect.

    Only create this task when specialist planning selects AI architecture.
    The task depends on the completed SolutionArchitecture, so it runs after
    the Solution Architecture Crew.

    Args:
        agent: Native CrewAI agent created for ``AgentType.AI_ARCHITECT``.
        requirements: The approved RequirementsSpecification.
        solution_architecture: The approved SolutionArchitecture.
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

    description = (
        "Objective: Design the AI-specific architecture for the AI "
        "capabilities identified in the approved requirements and solution "
        "architecture.\n\n"
        "Available structured context:\n"
        f"RequirementsSpecification: {requirements.model_dump_json()}\n"
        f"SolutionArchitecture: {solution_architecture.model_dump_json()}\n\n"
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
        "Required output: A schema-valid AIArchitecture referencing this "
        "RequirementsSpecification by requirements_specification_id and "
        "this SolutionArchitecture by solution_architecture_id, where every "
        "AI capability has both model-requirement coverage and evaluation "
        "coverage.\n\n"
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
        "A schema-valid AIArchitecture JSON object matching the "
        "AIArchitecture Pydantic model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(AIArchitecture),
        run_domain_validator(
            lambda output: AIArchitecture.validate_requirements_ownership(
                ai_architecture=output,
                requirements_specification=requirements,
            )
        ),
        run_domain_validator(
            lambda output: AIArchitecture.validate_architecture_ownership(
                ai_architecture=output,
                solution_architecture=solution_architecture,
            )
        ),
    )

    return Task(
        name="ai_architecture",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=AIArchitecture,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )
