"""Reusable deterministic guardrails for BuildWise CrewAI tasks.

Every guardrail here validates ``TaskOutput.pydantic`` deterministically. None
of them call an LLM, touch the database, mutate Flow state, or perform a
network call. They exist to give the acting agent actionable feedback so
CrewAI's native guardrail retry loop (``guardrail_max_retries``) can correct a
malformed structured output before a Crew hands its result back to the Flow.

These guardrails intentionally do not reimplement Pydantic field validation,
enum validation, or the cross-artifact ``model_validator`` checks already
defined on BuildWise domain models. Where a domain model already exposes a
classmethod validator (for example
``SolutionArchitecture.validate_requirements_ownership``), use
``run_domain_validator`` to reuse it instead of duplicating its logic here.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel, ValidationError

from buildwise.domain.common import generate_uuid

TaskGuardrail = Callable[[TaskOutput], tuple[bool, Any]]


def require_pydantic_output(
    expected_model: type[BaseModel],
) -> TaskGuardrail:
    """Build a guardrail that requires a schema-valid structured output."""

    model_name = expected_model.__name__

    def _guardrail(task_output: TaskOutput) -> tuple[bool, Any]:
        if task_output.pydantic is None:
            return (
                False,
                (
                    f"The task did not produce a {model_name} in "
                    "TaskOutput.pydantic. Return a schema-valid "
                    f"{model_name} and do not return only markdown or "
                    "plain text."
                ),
            )

        if not isinstance(task_output.pydantic, expected_model):
            actual_name = type(task_output.pydantic).__name__
            return (
                False,
                (
                    f"The task produced '{actual_name}' instead of the "
                    f"required '{model_name}'. Return a schema-valid "
                    f"{model_name}."
                ),
            )

        return (True, task_output)

    return _guardrail


def require_self_consistent_draft(
    draft_model: type[BaseModel],
    canonical_model: type[BaseModel],
    *,
    reconcile: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> TaskGuardrail:
    """Build a guardrail that catches canonical business-rule violations early.

    ``draft_model`` (see ``domain.artifact_drafts._draft_model``) intentionally
    strips every cross-field ``model_validator``/``field_validator`` so OpenAI
    structured output only has to satisfy JSON-Schema-expressible constraints.
    That means a schema-valid draft can still be internally inconsistent in a
    way the *canonical* model would reject — for example a feature
    referencing a persona ID that does not exist anywhere else in the same
    draft.

    This guardrail catches that class of error before it can reach
    deterministic assembly (which runs outside any CrewAI Task/guardrail
    context and has no retry mechanism). It builds the canonical model using
    the draft's own data plus placeholder ownership metadata — never used for
    anything beyond this check — and turns any resulting ``ValidationError``
    into guardrail feedback so CrewAI's retry loop can ask the agent to fix it.

    Only validates rules the canonical model can check using the draft's own
    fields. Ownership rules that require a *different* artifact (for example
    ``RequirementsSpecification.validate_product_ownership`` against the real
    ``ProductDefinition``) still run later, once assembly has the real
    upstream artifact.

    Args:
        reconcile: Optional transform applied to the draft's dumped payload
            before validation, mirroring any equivalent transform the real
            ``assemble_*`` function applies (for example
            ``reconcile_product_definition_scope``). Without this, the
            guardrail would reject a draft for a field the application
            derives deterministically anyway, wasting a retry on something
            that was never going to be a real problem. Must unconditionally
            populate whichever fields it's responsible for, even given an
            empty payload — it is probed once with ``{}`` at construction
            time to determine which required fields it covers, so those are
            exempt from the placeholder-strategy check below.
    """

    reconciled_probe = reconcile({}) if reconcile is not None else {}
    missing_fields = set(canonical_model.model_fields) - set(draft_model.model_fields)
    required_placeholder_fields = [
        field_name
        for field_name in missing_fields
        if canonical_model.model_fields[field_name].is_required()
        and field_name not in reconciled_probe
    ]

    for field_name in required_placeholder_fields:
        annotation = canonical_model.model_fields[field_name].annotation
        if annotation is not UUID:
            raise TypeError(
                "require_self_consistent_draft has no placeholder strategy "
                f"for required field '{field_name}' of type {annotation!r} "
                f"on {canonical_model.__name__}. Extend the placeholder "
                "strategy or omit this guardrail for that task."
            )

    def _guardrail(task_output: TaskOutput) -> tuple[bool, Any]:
        draft = task_output.pydantic

        if not isinstance(draft, draft_model):
            # require_pydantic_output already reports this failure; avoid
            # duplicating it here.
            return (True, task_output)

        payload = draft.model_dump(mode="python")
        if reconcile is not None:
            payload = reconcile(payload)
        for field_name in required_placeholder_fields:
            payload[field_name] = generate_uuid()

        try:
            canonical_model.model_validate(payload)
        except ValidationError as exc:
            return (
                False,
                (
                    f"{canonical_model.__name__} would fail validation once "
                    f"assembled: {exc}. Fix the underlying business rule "
                    "before returning the final answer."
                ),
            )

        return (True, task_output)

    return _guardrail


def require_non_empty_collections(
    expected_model: type[BaseModel],
    *field_names: str,
) -> TaskGuardrail:
    """Build a guardrail requiring specific fields to hold non-empty values.

    This validates runtime presence of meaningful content (for example, at
    least one populated release gate). It does not replace Pydantic
    ``min_length`` field validation already enforced when the domain model
    is constructed, so only use it for fields that do not already declare
    ``min_length``.
    """

    if not field_names:
        raise ValueError("require_non_empty_collections requires at least one field name.")

    def _guardrail(task_output: TaskOutput) -> tuple[bool, Any]:
        output = task_output.pydantic

        if not isinstance(output, expected_model):
            return (
                False,
                (
                    f"Expected a {expected_model.__name__} in "
                    "TaskOutput.pydantic before validating non-empty "
                    "collections."
                ),
            )

        empty_fields = [
            field_name for field_name in field_names if not getattr(output, field_name, None)
        ]

        if empty_fields:
            formatted = ", ".join(empty_fields)
            return (
                False,
                (
                    f"{expected_model.__name__} is missing required content "
                    f"in: {formatted}. Populate these fields with concrete, "
                    "non-empty values before returning the final answer."
                ),
            )

        return (True, task_output)

    return _guardrail


def require_artifact_session(
    expected_session_id: UUID | str,
) -> TaskGuardrail:
    """Build a guardrail requiring ``pydantic.session_id`` to match a session."""

    normalized_session_id = (
        expected_session_id
        if isinstance(expected_session_id, UUID)
        else UUID(str(expected_session_id))
    )

    def _guardrail(task_output: TaskOutput) -> tuple[bool, Any]:
        output = task_output.pydantic

        if output is None:
            return (
                False,
                "No structured output is available to validate session ownership.",
            )

        actual_session_id = getattr(output, "session_id", None)

        if actual_session_id is None:
            return (
                False,
                (
                    f"{type(output).__name__} does not define session_id. "
                    "Session ownership cannot be validated."
                ),
            )

        if actual_session_id != normalized_session_id:
            return (
                False,
                (
                    f"{type(output).__name__}.session_id "
                    f"({actual_session_id}) does not match the expected "
                    f"session ({normalized_session_id}). Do not change the "
                    "session identifier."
                ),
            )

        return (True, task_output)

    return _guardrail


def require_review_consistency(task_output: TaskOutput) -> tuple[bool, Any]:
    """Validate internal decision consistency of a ``LeadReview`` output."""

    from buildwise.domain.review import LeadReview

    output = task_output.pydantic

    if not isinstance(output, LeadReview):
        return (
            False,
            (
                "The task did not produce a LeadReview in "
                "TaskOutput.pydantic. Return a schema-valid LeadReview."
            ),
        )

    try:
        output.validate_decision_consistency()
    except ValueError as exc:
        return (False, str(exc))

    return (True, task_output)


def run_domain_validator(
    validator: Callable[[Any], None],
) -> TaskGuardrail:
    """Wrap a domain validator that raises ``ValueError``/``TypeError`` on failure.

    This reuses existing cross-artifact domain validation (for example
    ``SolutionArchitecture.validate_requirements_ownership``) instead of
    duplicating that logic inside the Tasks layer.
    """

    def _guardrail(task_output: TaskOutput) -> tuple[bool, Any]:
        output = task_output.pydantic

        if output is None:
            return (False, "No structured output is available to validate.")

        try:
            validator(output)
        except (ValueError, TypeError) as exc:
            return (False, str(exc))

        return (True, task_output)

    return _guardrail


def compose_guardrails(*guardrails: TaskGuardrail) -> list[TaskGuardrail]:
    """Return an ordered, validated list of task guardrails."""

    if not guardrails:
        raise ValueError("compose_guardrails requires at least one guardrail.")

    for guardrail in guardrails:
        if not callable(guardrail):
            raise TypeError("Every guardrail passed to compose_guardrails must be callable.")

    return list(guardrails)
