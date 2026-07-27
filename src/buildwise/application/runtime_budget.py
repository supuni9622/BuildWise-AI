"""Deterministic runtime-budget checks for Crew and tool execution."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from time import perf_counter

from buildwise.domain.usage import UsageRecord, UsageSummary
from buildwise.flows.state import FlowRuntimeLimits


class RuntimeBudgetExceeded(RuntimeError):
    """Raised before additional work can exceed a configured session limit."""

    def __init__(self, limit_name: str) -> None:
        self.limit_name = limit_name
        super().__init__(f"The session {limit_name} budget was exceeded.")


@dataclass
class RuntimeBudgetController:
    """Enforce limits against the consultation's persisted usage summary."""

    summary: UsageSummary
    limits: FlowRuntimeLimits

    def require_crew_capacity(self, *, agent_executions: int) -> None:
        self._require_duration_capacity()
        if (
            self.summary.agent_execution_count + agent_executions
            > self.limits.maximum_agent_executions
        ):
            raise RuntimeBudgetExceeded("agent execution")

    def require_tool_capacity(self) -> None:
        self._require_duration_capacity()
        if self.summary.tool_call_count >= self.limits.maximum_tool_calls:
            raise RuntimeBudgetExceeded("tool call")

    def record_tool_call(
        self,
        *,
        tool_name: str,
        duration_ms: int,
        retry_count: int = 0,
    ) -> None:
        record = UsageRecord(
            tool_name=tool_name,
            tool_call_count=1,
            retry_count=retry_count,
            execution_duration_ms=max(duration_ms, 0),
        )
        self.summary.records.append(record)
        self.summary.tool_call_count += 1
        self.summary.retry_count += retry_count
        self.summary.execution_duration_ms += record.execution_duration_ms
        self._require_duration_capacity()

    def require_totals_within_limits(self) -> None:
        if self.summary.total_tokens > self.limits.maximum_session_tokens:
            raise RuntimeBudgetExceeded("token")
        if (
            self.summary.estimated_cost_usd is not None
            and self.summary.estimated_cost_usd
            > self.limits.maximum_estimated_cost_usd
        ):
            raise RuntimeBudgetExceeded("estimated cost")
        self._require_duration_capacity()

    def _require_duration_capacity(self) -> None:
        if (
            self.summary.execution_duration_ms
            > self.limits.maximum_execution_seconds * 1000
        ):
            raise RuntimeBudgetExceeded("execution time")


_ACTIVE_BUDGET: ContextVar[RuntimeBudgetController | None] = ContextVar(
    "buildwise_active_runtime_budget",
    default=None,
)


@contextmanager
def runtime_budget_scope(
    controller: RuntimeBudgetController,
) -> Iterator[RuntimeBudgetController]:
    token = _ACTIVE_BUDGET.set(controller)
    try:
        yield controller
    finally:
        _ACTIVE_BUDGET.reset(token)


def active_runtime_budget() -> RuntimeBudgetController | None:
    return _ACTIVE_BUDGET.get()


@contextmanager
def measured_tool_call(tool_name: str) -> Iterator[None]:
    controller = active_runtime_budget()
    if controller is None:
        yield
        return

    controller.require_tool_capacity()
    started_at = perf_counter()
    try:
        yield
    finally:
        duration_ms = round((perf_counter() - started_at) * 1000)
        controller.record_tool_call(tool_name=tool_name, duration_ms=duration_ms)
