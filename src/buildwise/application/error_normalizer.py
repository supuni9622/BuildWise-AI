"""Convert runtime exceptions into stable, non-sensitive session errors."""

from __future__ import annotations

from buildwise.application.runtime_budget import RuntimeBudgetExceeded
from buildwise.domain.enums import SessionStage
from buildwise.domain.exceptions import CrewExecutionError
from buildwise.domain.session import SessionError
from buildwise.tools.sanitizer import ToolExecutionError


def normalize_session_error(
    error: Exception,
    *,
    stage: SessionStage,
    task_name: str | None = None,
) -> SessionError:
    """Map known failures without persisting raw provider/tool exception text."""

    if isinstance(error, RuntimeBudgetExceeded):
        return SessionError(
            code="runtime_budget_exceeded",
            message=str(error),
            stage=stage,
            recoverable=False,
            retryable=False,
            task_name=task_name,
            exception_type=type(error).__name__,
            details={"limit_name": error.limit_name},
        )
    if isinstance(error, CrewExecutionError):
        return SessionError(
            code="crew_execution_failed",
            message=(
                "A specialist crew could not produce a valid result for "
                f"the '{error.stage}' stage, most commonly because a "
                "generated output failed validation after its retry "
                "budget was exhausted. Resubmitting the same idea may "
                "succeed, since this is usually a one-off generation issue "
                "rather than a persistent one."
            ),
            stage=stage,
            recoverable=False,
            retryable=True,
            task_name=task_name,
            exception_type=type(error).__name__,
            details={"crew_stage": error.stage},
        )
    if isinstance(error, ToolExecutionError):
        return SessionError(
            code="tool_execution_failed",
            message="An external research tool could not complete safely.",
            stage=stage,
            recoverable=True,
            retryable=error.category in {"timeout", "execution_failed"},
            task_name=task_name,
            tool_name=error.tool_name,
            exception_type=type(error).__name__,
            details={"category": error.category},
        )
    if isinstance(error, TimeoutError):
        return SessionError(
            code="operation_timeout",
            message="An external operation timed out.",
            stage=stage,
            recoverable=True,
            retryable=True,
            task_name=task_name,
            exception_type=type(error).__name__,
        )
    if isinstance(error, ValueError):
        return SessionError(
            code="invalid_runtime_output",
            message="A workflow component returned inconsistent structured data.",
            stage=stage,
            recoverable=False,
            retryable=False,
            task_name=task_name,
            exception_type=type(error).__name__,
        )
    return SessionError(
        code="background_execution_failed",
        message="Background consultation execution failed safely.",
        stage=stage,
        recoverable=False,
        retryable=False,
        task_name=task_name,
        exception_type=type(error).__name__,
    )
