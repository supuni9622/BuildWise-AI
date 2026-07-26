"""Solution Architecture task factory.

Creates the native CrewAI Task assigned to the Solution Architect. The task
maps the approved requirements to logical components, connections,
technology choices, deployment units, scalability, and observability.
"""

from __future__ import annotations

from crewai import Agent, Task

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


def create_solution_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Solution Architecture task for the Solution Architect.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.SOLUTION_ARCHITECT``.
        requirements: The approved RequirementsSpecification.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``SolutionArchitecture``.
    """

    if agent is None:
        raise ValueError("create_solution_architecture_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    description = (
        "Objective: Design a solution architecture that satisfies the "
        "approved requirements.\n\n"
        "Available structured context:\n"
        f"{requirements.model_dump_json()}\n\n"
        "Required decisions:\n"
        "- Select an architecture style and justify it against the "
        "requirements.\n"
        "- Define logical components, their responsibilities, layers, and "
        "data ownership.\n"
        "- Define connections between components, including trust "
        "boundaries and failure behavior.\n"
        "- Select and justify technology choices.\n"
        "- Define deployment units for at least the production environment, "
        "assigning every component to exactly one deployment unit.\n"
        "- Define scalability plans and observability requirements, "
        "ensuring every critical component has observability coverage.\n"
        "- Record architecture decisions, risks, and architecture-owned "
        "cost estimates.\n\n"
        "Required output: A schema-valid SolutionArchitecture referencing "
        "this RequirementsSpecification by requirements_specification_id, "
        "with every must-have functional requirement mapped to at least one "
        "component.\n\n"
        "Important boundaries:\n"
        "- Do not select AI models, design prompts, or define RAG.\n"
        "- Do not produce a full security architecture or QA strategy; "
        "record only high-level security_considerations and "
        "privacy_considerations.\n"
        "- Do not change product scope.\n\n"
        "Failure or uncertainty handling: If the requirements cannot be "
        "responsibly architected yet, set decision to "
        "'requires_clarification' or 'cannot_proceed' with the required "
        "open_questions or limitations."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid SolutionArchitecture JSON object matching the "
        "SolutionArchitecture Pydantic model exactly, with no additional "
        "prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(SolutionArchitecture),
        run_domain_validator(
            lambda output: SolutionArchitecture.validate_requirements_ownership(
                solution_architecture=output,
                requirements_specification=requirements,
            )
        ),
    )

    return Task(
        name="solution_architecture",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=SolutionArchitecture,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )
