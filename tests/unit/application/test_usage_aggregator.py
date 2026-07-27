from __future__ import annotations

import pytest
from crewai.types.usage_metrics import UsageMetrics

from buildwise.application.usage_aggregator import UsageAggregator
from buildwise.domain.usage import UsageSummary


def test_aggregator_appends_and_totals_crew_usage() -> None:
    summary = UsageSummary()
    aggregator = UsageAggregator()

    record = aggregator.append(
        summary=summary,
        metrics=UsageMetrics(
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
            successful_requests=2,
        ),
        task_name="discovery",
        execution_duration_ms=125,
    )

    assert summary.records == [record]
    assert summary.input_tokens == 100
    assert summary.output_tokens == 40
    assert summary.total_tokens == 140
    assert summary.request_count == 2
    assert summary.execution_duration_ms == 125
    assert summary.estimated_cost_usd is None


def test_aggregator_uses_explicit_provider_cost_without_pricing_logic() -> None:
    summary = UsageSummary()
    aggregator = UsageAggregator()
    metrics = UsageMetrics(total_tokens=10, successful_requests=1)

    aggregator.append(
        summary=summary,
        metrics=metrics,
        task_name="product_planning",
        execution_duration_ms=20,
        provider_metadata={
            "provider": "openai",
            "model": "gpt-test",
            "estimated_cost_usd": 0.012,
        },
    )
    aggregator.append(
        summary=summary,
        metrics=metrics,
        task_name="technical_planning",
        execution_duration_ms=30,
        provider_metadata={"estimated_cost_usd": 0.008},
    )

    assert summary.estimated_cost_usd == pytest.approx(0.02)
    assert summary.request_count == 2
    assert summary.execution_duration_ms == 50


def test_unknown_record_makes_aggregate_cost_unknown() -> None:
    summary = UsageSummary()
    aggregator = UsageAggregator()
    metrics = UsageMetrics()
    aggregator.append(
        summary=summary,
        metrics=metrics,
        task_name="known",
        execution_duration_ms=1,
        provider_metadata={"estimated_cost_usd": 0.01},
    )

    aggregator.append(
        summary=summary,
        metrics=metrics,
        task_name="unknown",
        execution_duration_ms=1,
    )

    assert summary.estimated_cost_usd is None


def test_negative_duration_is_rejected() -> None:
    with pytest.raises(ValueError, match="duration"):
        UsageAggregator().append(
            summary=UsageSummary(),
            metrics=UsageMetrics(),
            task_name="invalid",
            execution_duration_ms=-1,
        )
