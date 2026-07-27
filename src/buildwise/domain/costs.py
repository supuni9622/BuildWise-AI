"""Canonical aggregation models for implementation-project costs."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    CurrencyCode,
    MediumText,
    NonNegativeDecimal,
    SessionId,
    ShortText,
    generate_uuid,
    utc_now,
)
from buildwise.domain.enums import CostCategory, CostFrequency, RevisionTarget

_PROJECT_COST_SOURCES = {
    RevisionTarget.PRODUCT_DEFINITION,
    RevisionTarget.MARKET_AND_GTM,
    RevisionTarget.SOLUTION_ARCHITECTURE,
    RevisionTarget.AI_ARCHITECTURE,
    RevisionTarget.SECURITY_ARCHITECTURE,
    RevisionTarget.QA_AND_EVALUATION,
}


class ProjectCostEstimate(BuildWiseModel):
    """One normalized estimate retaining its originating planning area."""

    id: ArtifactId = Field(default_factory=generate_uuid)
    source: RevisionTarget
    category: CostCategory
    name: ShortText
    description: MediumText
    frequency: CostFrequency
    currency: CurrencyCode = "USD"
    minimum: NonNegativeDecimal
    expected: NonNegativeDecimal
    maximum: NonNegativeDecimal
    optional: bool = False
    assumptions: list[MediumText] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_project_estimate(self) -> ProjectCostEstimate:
        if self.source not in _PROJECT_COST_SOURCES:
            raise ValueError("Project costs must originate from a planning artifact.")
        if self.minimum > self.expected or self.expected > self.maximum:
            raise ValueError("Project cost values must satisfy minimum <= expected <= maximum.")
        return self


class ProjectCostTotal(BuildWiseModel):
    """A total that combines only estimates with matching currency/frequency."""

    currency: CurrencyCode
    frequency: CostFrequency
    minimum: NonNegativeDecimal = Decimal("0")
    expected: NonNegativeDecimal = Decimal("0")
    maximum: NonNegativeDecimal = Decimal("0")
    estimate_count: int = Field(ge=1)


class CostSummary(BuildWiseModel):
    """Deterministic project-cost summary produced before Lead Review."""

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId
    estimates: list[ProjectCostEstimate] = Field(default_factory=list)
    totals: list[ProjectCostTotal] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at")
    @classmethod
    def normalize_generated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware.")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_totals(self) -> CostSummary:
        expected_totals = _calculate_totals(self.estimates)
        if self.totals != expected_totals:
            raise ValueError("CostSummary totals do not match its normalized estimates.")
        return self


def calculate_project_cost_totals(
    estimates: list[ProjectCostEstimate],
) -> list[ProjectCostTotal]:
    """Public deterministic total calculation used by the aggregator."""

    return _calculate_totals(estimates)


def _calculate_totals(estimates: list[ProjectCostEstimate]) -> list[ProjectCostTotal]:
    grouped: dict[tuple[str, CostFrequency], list[ProjectCostEstimate]] = {}
    for estimate in estimates:
        grouped.setdefault((estimate.currency, estimate.frequency), []).append(estimate)
    return [
        ProjectCostTotal(
            currency=currency,
            frequency=frequency,
            minimum=sum((item.minimum for item in items), Decimal("0")),
            expected=sum((item.expected for item in items), Decimal("0")),
            maximum=sum((item.maximum for item in items), Decimal("0")),
            estimate_count=len(items),
        )
        for (currency, frequency), items in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], item[0][1].value),
        )
    ]
