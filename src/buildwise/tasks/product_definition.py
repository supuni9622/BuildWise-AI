"""Product Definition task factory.

Creates the native CrewAI Task assigned to the Product Manager. The task
converts a validated ``DiscoveryResult`` into a structured
``ProductDefinition``: vision, personas, goals, features, MVP scope, roadmap,
risks, and success metrics.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.artifact_drafts import (
    ProductDefinitionDraft,
    reconcile_product_definition_scope,
)
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.product import ProductDefinition
from buildwise.domain.review import RevisionRequest
from buildwise.planning.specialist_context import DiscoveryProjection
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    require_self_consistent_draft,
)
from buildwise.tasks.instructions import IDENTIFIER_RULES
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_product_definition_task(
    *,
    agent: Agent,
    discovery_task: Task | None = None,
    discovery_result: DiscoveryResult | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Product Definition task for the Product Manager.

    Exactly one of ``discovery_task`` or ``discovery_result`` must be
    supplied. Pass ``discovery_task`` when both tasks execute inside the same
    Crew so CrewAI can wire native task context. Pass ``discovery_result``
    when Discovery already completed in a separate Crew and its structured
    output is being supplied through Flow/Crew inputs.

    Args:
        agent: Native CrewAI agent created for ``AgentType.PRODUCT_MANAGER``.
        discovery_task: The Discovery task, when executing in the same Crew.
        discovery_result: The completed DiscoveryResult, when Discovery ran
            in a separate Crew.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer, when this Crew is being rerun to fix a specific
            issue rather than generate a first draft.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``ProductDefinition``.
    """

    if agent is None:
        raise ValueError("create_product_definition_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    if discovery_task is None and discovery_result is None:
        raise ValueError(
            "create_product_definition_task requires either discovery_task or discovery_result."
        )

    if discovery_task is not None and discovery_result is not None:
        raise ValueError(
            "create_product_definition_task accepts only one of "
            "discovery_task or discovery_result, not both."
        )

    context_section = (
        "Available structured context: the completed Discovery task output "
        "is provided as native task context."
        if discovery_task is not None
        else (
            "Available structured context:\n"
            f"{DiscoveryProjection.from_artifact(discovery_result).model_dump_json()}"  # type: ignore[arg-type]
        )
    )

    description = (
        "Objective: Convert the validated Discovery assessment into a "
        "complete product definition.\n\n"
        f"{context_section}\n\n"
        "Required decisions:\n"
        "- Define the product vision, value proposition, and problem "
        "statement.\n"
        "- Define exactly one primary user persona plus any secondary or "
        "administrative personas the evidence supports.\n"
        "- Define measurable product goals.\n"
        "- Define product features, marking which belong in the MVP and "
        "which are explicitly out of scope.\n"
        "- Define a roadmap with at least one MVP-horizon item.\n"
        "- Define product-level risks, success metrics, and any assumptions "
        "or open questions carried forward from Discovery.\n\n"
        "Required output: A schema-valid ProductDefinitionDraft. The "
        "application adds artifact ownership and provenance metadata.\n\n"
        f"{IDENTIFIER_RULES}"
        "- Do not emit top-level id, session_id, discovery_result_id, "
        "source_metadata, or generated_at fields.\n\n"
        "Risk acceptance rules:\n"
        "- When accepted=false, acceptance_rationale must be null.\n"
        "- When accepted=true, provide acceptance_rationale.\n\n"
        "Important boundaries:\n"
        "- Do not define technical or AI architecture, technology choices, "
        "or model selection.\n"
        "- Do not perform market or competitive research.\n"
        "- Do not invent facts beyond what Discovery established; carry "
        "forward assumptions and limitations instead.\n\n"
        "Failure or uncertainty handling: If Discovery left blocking "
        "unknowns or the product direction cannot be responsibly defined, "
        "set decision to 'requires_clarification' or 'cannot_proceed' with "
        "the required open_questions or limitations."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid ProductDefinitionDraft JSON object matching the "
        "compact draft model exactly, using RFC 4122 UUIDs for nested "
        "all identifiers and preserving cross-references, with no additional "
        "prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(ProductDefinitionDraft),
        require_self_consistent_draft(
            ProductDefinitionDraft,
            ProductDefinition,
            reconcile=reconcile_product_definition_scope,
        ),
    )

    task_kwargs: dict[str, object] = {
        "name": "product_definition",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "output_pydantic": ProductDefinitionDraft,
        "guardrails": guardrails,
        "guardrail_max_retries": guardrail_max_retries,
    }

    if discovery_task is not None:
        task_kwargs["context"] = [discovery_task]

    return Task(**task_kwargs)
