"""Reusable deterministic CrewAI Task guardrails.

Guardrails here must stay deterministic: no LLM calls, no database access,
no Flow-state mutation, no network calls. A guardrail either accepts the
output (``True, value``) or returns actionable feedback the agent can act
on during the bounded ``guardrail_max_retries`` retry loop.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from crewai.lite_agent_output import LiteAgentOutput
from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel

TaskGuardrail = Callable[[TaskOutput | LiteAgentOutput], tuple[bool, Any]]


def require_pydantic_output(expected_model: type[BaseModel]) -> TaskGuardrail:
    """Reject any task result that did not produce the expected structured model.

    This is the guardrail every specialist task attaches — it is the
    enforcement point for the architecture rule that raw markdown or ad
    hoc JSON is never the canonical artifact.
    """

    def _guardrail(result: TaskOutput | LiteAgentOutput) -> tuple[bool, Any]:
        pydantic_output = getattr(result, "pydantic", None)
        if pydantic_output is None:
            return (
                False,
                f"The task did not produce a {expected_model.__name__} in "
                "TaskOutput.pydantic. Return a schema-valid "
                f"{expected_model.__name__} object, not markdown or freeform JSON.",
            )
        if not isinstance(pydantic_output, expected_model):
            return (
                False,
                f"Expected structured output of type {expected_model.__name__}, "
                f"got {type(pydantic_output).__name__}. Return a schema-valid "
                f"{expected_model.__name__} object.",
            )
        return True, pydantic_output

    return _guardrail


def require_artifact_session(expected_session_id: UUID) -> TaskGuardrail:
    """Reject an artifact whose ``session_id`` does not match the current session."""

    def _guardrail(result: TaskOutput | LiteAgentOutput) -> tuple[bool, Any]:
        pydantic_output = getattr(result, "pydantic", None)
        artifact_session_id = getattr(pydantic_output, "session_id", None)
        if artifact_session_id != expected_session_id:
            return (
                False,
                "The returned artifact's session_id does not match the "
                f"expected session {expected_session_id}. Keep session_id "
                "exactly as provided in the task context.",
            )
        return True, pydantic_output

    return _guardrail


def require_non_empty(field_name: str, expected_model: type[BaseModel]) -> TaskGuardrail:
    """Reject a structured artifact whose named list/str field is empty."""

    def _guardrail(result: TaskOutput | LiteAgentOutput) -> tuple[bool, Any]:
        pydantic_output = getattr(result, "pydantic", None)
        if pydantic_output is None:
            return False, f"Expected a {expected_model.__name__} with a non-empty {field_name}."
        value = getattr(pydantic_output, field_name, None)
        if not value:
            return (
                False,
                f"{expected_model.__name__}.{field_name} must not be empty. "
                f"Populate {field_name} with at least one item before returning.",
            )
        return True, pydantic_output

    return _guardrail


def compose_guardrails(*guardrails: TaskGuardrail) -> list[TaskGuardrail]:
    """Flatten guardrail factories into the list CrewAI's ``Task.guardrails`` expects."""

    return list(guardrails)
