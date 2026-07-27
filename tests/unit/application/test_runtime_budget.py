import pytest

from buildwise.application.runtime_budget import (
    RuntimeBudgetController,
    RuntimeBudgetExceeded,
)
from buildwise.domain.usage import UsageSummary
from buildwise.flows.state import FlowRuntimeLimits


def test_runtime_budget_rejects_additional_agent_execution() -> None:
    summary = UsageSummary(agent_execution_count=2)
    controller = RuntimeBudgetController(
        summary=summary,
        limits=FlowRuntimeLimits(maximum_agent_executions=2),
    )

    with pytest.raises(RuntimeBudgetExceeded, match="agent execution"):
        controller.require_crew_capacity(agent_executions=1)


def test_runtime_budget_records_tool_usage_and_enforces_limit() -> None:
    summary = UsageSummary()
    controller = RuntimeBudgetController(
        summary=summary,
        limits=FlowRuntimeLimits(maximum_tool_calls=1),
    )

    controller.require_tool_capacity()
    controller.record_tool_call(tool_name="web_search", duration_ms=12)

    assert summary.tool_call_count == 1
    assert summary.execution_duration_ms == 12
    with pytest.raises(RuntimeBudgetExceeded, match="tool call"):
        controller.require_tool_capacity()


def test_runtime_budget_enforces_elapsed_execution_duration() -> None:
    controller = RuntimeBudgetController(
        summary=UsageSummary(execution_duration_ms=60_001),
        limits=FlowRuntimeLimits(maximum_execution_seconds=60),
    )

    with pytest.raises(RuntimeBudgetExceeded, match="execution time"):
        controller.require_totals_within_limits()
