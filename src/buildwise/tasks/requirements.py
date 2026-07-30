"""Requirements task factory.

Creates the native CrewAI Task assigned to the Business Analyst. The task
converts a validated ``ProductDefinition`` into a structured
``RequirementsSpecification``: functional and non-functional requirements,
business rules, data and integration requirements, user journeys, user
stories, and edge cases.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.artifact_drafts import RequirementsSpecificationDraft
from buildwise.domain.product import ProductDefinition
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.guardrails import compose_guardrails, require_pydantic_output
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_requirements_task(
    *,
    agent: Agent,
    product_definition_task: Task | None = None,
    product_definition: ProductDefinition | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Requirements task for the Business Analyst.

    Exactly one of ``product_definition_task`` or ``product_definition`` must
    be supplied, following the same same-Crew-context versus cross-Crew-input
    pattern used by ``create_product_definition_task``.

    Args:
        agent: Native CrewAI agent created for ``AgentType.BUSINESS_ANALYST``.
        product_definition_task: The Product Definition task, when executing
            in the same Crew.
        product_definition: The completed ProductDefinition, when Product
            Definition ran in a separate Crew.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``RequirementsSpecification``.
    """

    if agent is None:
        raise ValueError("create_requirements_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    if product_definition_task is None and product_definition is None:
        raise ValueError(
            "create_requirements_task requires either "
            "product_definition_task or product_definition."
        )

    if product_definition_task is not None and product_definition is not None:
        raise ValueError(
            "create_requirements_task accepts only one of "
            "product_definition_task or product_definition, not both."
        )

    context_section = (
        "Available structured context: the completed Product Definition "
        "task output is provided as native task context."
        if product_definition_task is not None
        else (
            f"Available structured context:\n{product_definition.model_dump_json()}"  # type: ignore[union-attr]
        )
    )

    description = (
        "Objective: Convert the approved product definition into a testable, "
        "traceable requirements specification.\n\n"
        f"{context_section}\n\n"
        "Required decisions:\n"
        "- Define functional requirements traced to product features and "
        "personas, each with at least one acceptance criterion.\n"
        "- Define non-functional (quality) requirements with a measurable "
        "metric and target.\n"
        "- Define business rules, data requirements, and integration "
        "requirements that the features imply.\n"
        "- Define user journeys and user stories covering the must-have "
        "functional requirements.\n"
        "- Identify edge cases the product must handle.\n\n"
        "Required output: A schema-valid RequirementsSpecificationDraft with "
        "every reference (feature, persona, goal, requirement) resolving to "
        "an identifier that actually exists in the supplied context.\n\n"
        "Do not emit top-level ownership, timestamps, or source metadata; "
        "the application adds them deterministically.\n\n"
        "Important boundaries:\n"
        "- Do not make technical architecture or technology decisions.\n"
        "- Do not select an AI model or design prompts.\n"
        "- Do not persist data or contact any system.\n\n"
        "Failure or uncertainty handling: If the product definition cannot "
        "be responsibly converted into requirements, set decision to "
        "'requires_clarification' or 'cannot_proceed' with the required "
        "open_questions or limitations."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid RequirementsSpecificationDraft JSON object matching "
        "the compact draft model exactly, with no "
        "additional prose."
    )

    guardrails = compose_guardrails(require_pydantic_output(RequirementsSpecificationDraft))

    task_kwargs: dict[str, object] = {
        "name": "requirements_specification",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "output_pydantic": RequirementsSpecificationDraft,
        "guardrails": guardrails,
        "guardrail_max_retries": guardrail_max_retries,
    }

    if product_definition_task is not None:
        task_kwargs["context"] = [product_definition_task]

    return Task(**task_kwargs)
