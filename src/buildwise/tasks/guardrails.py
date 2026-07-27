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
from pydantic import BaseModel

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
