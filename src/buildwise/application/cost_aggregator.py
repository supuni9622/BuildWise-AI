"""Deterministic aggregation of implementation-project cost estimates."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from buildwise.domain.common import CostEstimate, SessionId
from buildwise.domain.costs import (
    CostSummary,
    ProjectCostEstimate,
    calculate_project_cost_totals,
)
from buildwise.domain.enums import RevisionTarget
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.qa import QualityCostEstimate
from buildwise.domain.security import SecurityCostEstimate
from buildwise.domain.technical_planning import TechnicalPlanningResult


class ProjectCostAggregator:
    """Normalize distributed planning estimates without pricing inference."""

    def aggregate(
        self,
        *,
        product_planning: ProductPlanningResult,
        technical_planning: TechnicalPlanningResult,
    ) -> CostSummary:
        if product_planning.session_id != technical_planning.session_id:
            raise ValueError("Product and technical planning sessions must match.")

        estimates: list[ProjectCostEstimate] = []
        estimates.extend(
            _normalize_ranges(
                product_planning.product_definition.product_cost_estimates,
                RevisionTarget.PRODUCT_DEFINITION,
            )
        )
        if product_planning.market_and_gtm is not None:
            estimates.extend(
                _normalize_ranges(
                    product_planning.market_and_gtm.gtm_cost_estimates,
                    RevisionTarget.MARKET_AND_GTM,
                )
            )
        technical = technical_planning
        estimates.extend(
            _normalize_ranges(
                technical.solution_architecture.architecture_cost_estimates,
                RevisionTarget.SOLUTION_ARCHITECTURE,
            )
        )
        if technical.ai_architecture is not None:
            estimates.extend(
                _normalize_ranges(
                    technical.ai_architecture.ai_cost_estimates,
                    RevisionTarget.AI_ARCHITECTURE,
                )
            )
        if technical.security_architecture is not None:
            estimates.extend(
                _normalize_points(
                    technical.security_architecture.estimated_costs,
                    RevisionTarget.SECURITY_ARCHITECTURE,
                    technical.session_id,
                )
            )
        if technical.qa_evaluation is not None:
            estimates.extend(
                _normalize_points(
                    technical.qa_evaluation.estimated_costs,
                    RevisionTarget.QA_AND_EVALUATION,
                    technical.session_id,
                )
            )
        return CostSummary(
            session_id=product_planning.session_id,
            estimates=estimates,
            totals=calculate_project_cost_totals(estimates),
        )


def aggregate_project_costs(
    *,
    product_planning: ProductPlanningResult,
    technical_planning: TechnicalPlanningResult,
) -> CostSummary:
    return ProjectCostAggregator().aggregate(
        product_planning=product_planning,
        technical_planning=technical_planning,
    )


def _normalize_ranges(
    estimates: list[CostEstimate],
    source: RevisionTarget,
) -> list[ProjectCostEstimate]:
    return [
        ProjectCostEstimate(
            id=estimate.id,
            source=source,
            category=estimate.category,
            name=estimate.name,
            description=estimate.description,
            frequency=estimate.frequency,
            currency=estimate.range.expected.currency,
            minimum=estimate.range.minimum.amount,
            expected=estimate.range.expected.amount,
            maximum=estimate.range.maximum.amount,
            assumptions=estimate.assumptions,
            exclusions=estimate.exclusions,
        )
        for estimate in estimates
    ]


def _normalize_points(
    estimates: Sequence[SecurityCostEstimate | QualityCostEstimate],
    source: RevisionTarget,
    session_id: SessionId,
) -> list[ProjectCostEstimate]:
    normalized: list[ProjectCostEstimate] = []
    for index, estimate in enumerate(estimates):
        item = estimate.item
        amount = Decimal(str(estimate.estimated_cost))
        frequency = estimate.frequency
        category = estimate.category
        justification = estimate.justification
        optional = estimate.optional
        stable_id = uuid5(
            NAMESPACE_URL,
            f"buildwise:{session_id}:{source.value}:{index}:{item}:{frequency}:{amount}",
        )
        normalized.append(
            ProjectCostEstimate(
                id=stable_id,
                source=source,
                category=category,
                name=item,
                description=justification,
                frequency=frequency,
                minimum=amount,
                expected=amount,
                maximum=amount,
                optional=optional,
            )
        )
    return normalized
