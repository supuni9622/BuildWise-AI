"""Discovery task factory.

Creates the native CrewAI Task assigned to the Product Discovery Analyst. The
task turns a raw ``ProductIdeaRequest`` (and any prior clarification answers)
into a structured ``DiscoveryResult``: known facts, assumptions, unknowns,
preliminary risks, capability classification, and a completeness assessment.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.common import SessionId
from buildwise.domain.discovery import DiscoveryRefinement, DiscoveryResult
from buildwise.domain.intake import ProductIdeaContext, ProductIdeaRequest
from buildwise.tasks.guardrails import compose_guardrails, require_pydantic_output

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_discovery_task(
    *,
    agent: Agent,
    session_id: SessionId,
    product_idea: ProductIdeaRequest,
    clarification_context: ProductIdeaContext | None = None,
    maximum_clarification_rounds: int = 3,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Discovery task for the Product Discovery Analyst.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.PRODUCT_DISCOVERY_ANALYST``.
        session_id: Authoritative Flow session identifier.
        product_idea: Raw intake payload submitted by the user.
        clarification_context: Prior clarification answers, when Discovery
            is re-run after the Flow resumed from a clarification pause.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``DiscoveryResult``.
    """

    if agent is None:
        raise ValueError("create_discovery_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    context_lines = [f"ProductIdeaRequest: {product_idea.model_dump_json()}"]
    context_lines.insert(0, f"Authoritative session_id: {session_id}")

    if clarification_context is not None:
        context_lines.append(
            f"ProductIdeaContext (prior clarification): {clarification_context.model_dump_json()}"
        )

    description = (
        "Objective: Interpret the submitted product idea and produce a "
        "structured Discovery assessment.\n\n"
        "Available structured context:\n" + "\n".join(context_lines) + "\n\n"
        f"Clarification limit: at most {maximum_clarification_rounds} rounds. "
        "Never generate a question-set round_number above this limit.\n\n"
        "Required decisions:\n"
        "- Separate evidence-backed known facts from working assumptions.\n"
        "- Identify unknowns, marking which are blocking versus non-blocking.\n"
        "- Identify early product, business, market, technical, and "
        "AI-related risks.\n"
        "- Classify the product capabilities present in the idea (for "
        "example standard software, AI-assisted, AI-core, RAG, agentic "
        "workflow, sensitive data, or regulated).\n"
        "- Assess intake completeness and decide whether clarification is "
        "required before continuing.\n"
        "- Keep all cross-field decisions internally consistent:\n"
        "  * For every unknown, set recommended_assumption to a non-null "
        "string only when can_proceed_with_assumption=true; set it to null "
        "when can_proceed_with_assumption=false.\n"
        "  * If blocking_unknown_keys is non-empty, set can_continue=false "
        "and clarification_required=true.\n"
        "  * Every blocking unknown must have clarification_required=true.\n"
        "  * If completeness.clarification_required=true, provide "
        "clarification_questions and set recommended_next_step to "
        "request_clarification.\n"
        "  * Set percentage to exactly score multiplied by 100.\n\n"
        "  * For each known fact whose source_type is user_provided or "
        "clarification_answer, include at least one source_reference_id that "
        "matches an entry in source_metadata.\n"
        "  * For free_text, boolean, integer, and decimal clarification "
        "questions, set options=[] and allow_other=false. Choice questions "
        "must contain at least two unique options.\n\n"
        "Required output: A schema-valid DiscoveryResult containing "
        "known_facts, assumptions, unknowns, risks, completeness, "
        "capability_classification, and recommended_next_step.\n\n"
        "Important boundaries:\n"
        "- Copy the authoritative session_id exactly into DiscoveryResult.session_id, "
        "idea_context.session_id, idea_context.validated_idea.session_id, and "
        "clarification_questions.session_id when clarification questions are present.\n"
        "- Do not ask the user questions directly; only populate "
        "clarification_questions when completeness requires them.\n"
        "- Do not select downstream specialists or make architecture "
        "decisions.\n"
        "- Do not fabricate facts; unresolved information must be recorded "
        "as an assumption or an unknown.\n\n"
        "Failure or uncertainty handling: When information is missing, "
        "record it as an assumption with requires_validation=true or as an "
        "unknown, and let the completeness assessment drive whether "
        "clarification is required."
    )

    expected_output = (
        "A schema-valid DiscoveryResult JSON object matching the "
        "DiscoveryResult Pydantic model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(require_pydantic_output(DiscoveryResult))

    return Task(
        name="product_discovery",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=DiscoveryResult,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )


def create_discovery_refinement_task(
    *,
    agent: Agent,
    session_id: SessionId,
    previous_discovery: DiscoveryResult,
    clarification_context: ProductIdeaContext,
    maximum_clarification_rounds: int,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Create a compact task that revisits only unresolved Discovery decisions."""

    at_round_limit = (
        clarification_context.clarification_round >= maximum_clarification_rounds
    )
    unresolved = [unknown.model_dump(mode="json") for unknown in previous_discovery.unknowns]
    description = (
        "Objective: refine only the unresolved Discovery decisions using the newly "
        "submitted clarification answers. Do not regenerate known facts, risks, "
        "capability classification, interpretations, or source metadata; those are "
        "merged deterministically from the prior accepted artifact.\n\n"
        f"Authoritative session_id: {session_id}\n"
        f"Clarification round: {clarification_context.clarification_round} of "
        f"{maximum_clarification_rounds}\n"
        f"Prior unresolved unknowns: {unresolved}\n"
        "Accumulated clarification context: "
        f"{clarification_context.model_dump_json()}\n\n"
        "Return only a DiscoveryRefinement. Remove unknowns resolved by the answers, "
        "update the completeness evidence and routing consistently, and generate questions only "
        "for material unknowns that remain unresolved. If questions are returned, "
        "their round_number must be the current round plus one and their session_id "
        "must equal the authoritative session_id. "
        "Completeness percentage and decision booleans are intentionally absent; "
        "the application derives them deterministically from score, threshold, and "
        "blocking_unknown_keys. If blocking_unknown_keys is non-empty, return "
        "clarification_questions and recommended_next_step='request_clarification'. "
        "If it is empty, return clarification_questions=null and never request "
        "clarification; use 'continue_with_limitations' when limitations remain, "
        "otherwise use 'continue_to_product_definition'. "
    )
    if at_round_limit:
        description += (
            "The maximum clarification round has been reached. Do not request more "
            "clarification, set clarification_questions=null, and leave "
            "blocking_unknown_keys empty. Convert responsibly assumable residual "
            "items to non-blocking unknowns with documented limitations; otherwise "
            "fail Discovery explicitly."
        )

    return Task(
        name="refine_product_discovery",
        description=description,
        expected_output=(
            "A schema-valid DiscoveryRefinement JSON object with no additional prose."
        ),
        agent=agent,
        output_pydantic=DiscoveryRefinement,
        guardrails=compose_guardrails(require_pydantic_output(DiscoveryRefinement)),
        guardrail_max_retries=guardrail_max_retries,
    )
