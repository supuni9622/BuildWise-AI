"""Discovery task factory.

Creates the native CrewAI Task assigned to the Product Discovery Analyst. The
task turns a raw ``ProductIdeaRequest`` (and any prior clarification answers)
into a compact ``DiscoveryDraft``. The application later adds operational
metadata and derives redundant routing fields deterministically.
"""

from __future__ import annotations

from typing import Any

from crewai import Agent, Task
from crewai.tasks.task_output import TaskOutput

from buildwise.domain.common import SessionId
from buildwise.domain.discovery import DiscoveryRefinement, DiscoveryResult
from buildwise.domain.discovery_draft import DiscoveryDraft
from buildwise.domain.intake import ProductIdeaContext, ProductIdeaRequest
from buildwise.tasks.guardrails import compose_guardrails, require_pydantic_output

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def _validate_discovery_semantic_consistency(task_output: TaskOutput) -> tuple[bool, Any]:
    """Re-check the cross-field business rules ``discovery_draft.py`` no
    longer enforces at parse time (see the docstrings on ``AssumptionDraft``,
    ``UnknownDraft``, ``ClarificationQuestionDraft``, and ``DiscoveryDraft``
    itself). Those checks moved here so a violation becomes retryable
    guardrail feedback instead of a raw parse-time crash — the same
    reasoning as ``require_self_consistent_draft``, applied by hand because
    this draft predates that shared mechanism and has a different shape
    than the 5 artifacts it covers.
    """

    draft = task_output.pydantic

    if not isinstance(draft, DiscoveryDraft):
        return (True, task_output)

    for assumption in draft.assumptions:
        if assumption.requires_validation and assumption.validation_question is None:
            return (
                False,
                (
                    f"Assumption '{assumption.key}' has requires_validation=true "
                    "but no validation_question. Provide one, or set "
                    "requires_validation=false."
                ),
            )
        if not assumption.requires_validation and assumption.validation_question is not None:
            return (
                False,
                (
                    f"Assumption '{assumption.key}' has requires_validation=false "
                    "but still provides a validation_question. Remove it, or set "
                    "requires_validation=true."
                ),
            )

    for unknown in draft.unknowns:
        if unknown.can_proceed_with_assumption and unknown.recommended_assumption is None:
            return (
                False,
                (
                    f"Unknown '{unknown.key}' has can_proceed_with_assumption=true "
                    "but no recommended_assumption. Provide one, or set "
                    "can_proceed_with_assumption=false."
                ),
            )
        if not unknown.can_proceed_with_assumption and unknown.recommended_assumption is not None:
            return (
                False,
                (
                    f"Unknown '{unknown.key}' has can_proceed_with_assumption=false "
                    "but still provides a recommended_assumption. Remove it, or set "
                    "can_proceed_with_assumption=true."
                ),
            )

    unknown_keys = [unknown.key for unknown in draft.unknowns]
    if len(unknown_keys) != len(set(unknown_keys)):
        return (False, "Unknown keys must be unique.")

    fact_keys = {fact.key for fact in draft.known_facts}
    assumption_keys = {assumption.key for assumption in draft.assumptions}
    if overlap := fact_keys.intersection(assumption_keys):
        return (
            False,
            "A key cannot be both a known fact and an assumption: " + ", ".join(sorted(overlap)),
        )

    if draft.clarification_questions is not None:
        for question in draft.clarification_questions.questions:
            is_choice = question.question_type in {"single_choice", "multiple_choice"}
            if is_choice and len(question.options) < 2:
                return (
                    False,
                    f"Clarification question '{question.key}' is a choice question "
                    "but has fewer than two options.",
                )
            if not is_choice and (question.options or question.allow_other):
                return (
                    False,
                    f"Clarification question '{question.key}' is not a choice "
                    "question but sets options or allow_other.",
                )

        referenced = {
            key
            for question in draft.clarification_questions.questions
            for key in question.related_unknown_keys
        }
        missing = referenced.difference(unknown_keys)
        if missing:
            return (
                False,
                "Clarification questions reference unknown keys that do not "
                "exist in unknowns: " + ", ".join(sorted(missing)),
            )

    return (True, task_output)


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
        A native ``crewai.Task`` producing a compact ``DiscoveryDraft``.
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
        "  * If any unknown is blocking, provide clarification_questions.\n"
        "  * For free_text, boolean, integer, and decimal clarification "
        "questions, set options=[] and allow_other=false. Choice questions "
        "must contain at least two unique options.\n\n"
        "Required output: A schema-valid DiscoveryDraft containing "
        "known_facts, assumptions, unknowns, risks, completeness, "
        "capability_signals, and clarification questions when needed.\n\n"
        "Important boundaries:\n"
        "- Do not generate IDs, timestamps, percentages, session ownership, "
        "source-reference IDs, routing booleans, or a recommended route. The "
        "application derives those fields deterministically.\n"
        "- Link clarification questions to unknowns by related_unknown_keys.\n"
        "- Do not ask the user questions directly; only populate "
        "clarification_questions when blocking unknowns require them.\n"
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
        "A schema-valid DiscoveryDraft JSON object matching the compact "
        "DiscoveryDraft Pydantic model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(DiscoveryDraft),
        _validate_discovery_semantic_consistency,
    )

    return Task(
        name="product_discovery",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=DiscoveryDraft,
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

    at_round_limit = clarification_context.clarification_round >= maximum_clarification_rounds
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
