"""Lightweight aggregation of provider-reported Crew usage."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from crewai.types.usage_metrics import UsageMetrics

from buildwise.domain.usage import UsageRecord, UsageSummary


class UsageAggregator:
    """Append one Crew execution's metrics and update its running summary."""

    def append(
        self,
        *,
        summary: UsageSummary,
        metrics: UsageMetrics,
        task_name: str,
        execution_duration_ms: int,
        provider_metadata: Mapping[str, Any] | None = None,
    ) -> UsageRecord:
        if execution_duration_ms < 0:
            raise ValueError("execution_duration_ms cannot be negative.")

        metadata = provider_metadata or {}
        estimated_cost = _optional_non_negative_float(
            metadata.get("estimated_cost_usd"),
            field_name="estimated_cost_usd",
        )
        record = UsageRecord(
            provider=_optional_string(metadata.get("provider")),
            model=_optional_string(metadata.get("model")),
            task_name=task_name,
            input_tokens=metrics.prompt_tokens,
            output_tokens=metrics.completion_tokens,
            total_tokens=metrics.total_tokens,
            estimated_cost_usd=estimated_cost,
            request_count=metrics.successful_requests,
            execution_duration_ms=execution_duration_ms,
        )
        summary.records.append(record)
        summary.input_tokens += record.input_tokens
        summary.output_tokens += record.output_tokens
        summary.total_tokens += record.total_tokens
        summary.request_count += record.request_count
        summary.agent_execution_count += record.agent_execution_count
        summary.tool_call_count += record.tool_call_count
        summary.retry_count += record.retry_count
        summary.execution_duration_ms += record.execution_duration_ms
        summary.estimated_cost_usd = _complete_cost_total(summary.records)
        return record


def aggregate_usage(
    *,
    summary: UsageSummary,
    metrics: UsageMetrics,
    task_name: str,
    execution_duration_ms: int,
    provider_metadata: Mapping[str, Any] | None = None,
) -> UsageRecord:
    """Functional wrapper for callers that do not need an aggregator instance."""

    return UsageAggregator().append(
        summary=summary,
        metrics=metrics,
        task_name=task_name,
        execution_duration_ms=execution_duration_ms,
        provider_metadata=provider_metadata,
    )


def _complete_cost_total(records: list[UsageRecord]) -> float | None:
    costs = [record.estimated_cost_usd for record in records]
    if not costs or any(cost is None for cost in costs):
        return None
    return sum(cost for cost in costs if cost is not None)


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _optional_non_negative_float(value: Any, *, field_name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric when supplied.")
    normalized = float(value)
    if normalized < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return normalized
