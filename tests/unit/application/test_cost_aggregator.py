from __future__ import annotations

from decimal import Decimal

from buildwise.application.cost_aggregator import aggregate_project_costs
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import CostEstimate, CostRange, MoneyAmount
from buildwise.domain.enums import CostCategory, CostFrequency, RevisionTarget
from buildwise.domain.security import SecurityArchitecture, SecurityCostEstimate
from buildwise.domain.technical_planning import TechnicalPlanningResult
from fixtures.planning import build_product_planning_inputs


def _range_cost(
    *,
    name: str,
    category: CostCategory,
    minimum: str,
    expected: str,
    maximum: str,
) -> CostEstimate:
    return CostEstimate(
        category=category,
        name=name,
        description=f"Directional {name} implementation estimate.",
        frequency=CostFrequency.MONTHLY,
        range=CostRange(
            minimum=MoneyAmount(amount=Decimal(minimum), currency="USD"),
            expected=MoneyAmount(amount=Decimal(expected), currency="USD"),
            maximum=MoneyAmount(amount=Decimal(maximum), currency="USD"),
        ),
    )


def test_project_costs_are_normalized_and_totaled_by_frequency() -> None:
    _, product = build_product_planning_inputs()
    product_definition = product.product_definition.model_copy(
        update={
            "product_cost_estimates": [
                _range_cost(
                    name="Product operations",
                    category=CostCategory.PRODUCT,
                    minimum="100",
                    expected="150",
                    maximum="200",
                )
            ]
        }
    )
    product = product.model_copy(update={"product_definition": product_definition})
    solution = SolutionArchitecture.model_construct(
        session_id=product.session_id,
        requirements_specification_id=product.requirements.id,
        architecture_cost_estimates=[
            _range_cost(
                name="Cloud platform",
                category=CostCategory.INFRASTRUCTURE,
                minimum="200",
                expected="300",
                maximum="500",
            )
        ],
    )
    security = SecurityArchitecture.model_construct(
        estimated_costs=[
            SecurityCostEstimate(
                item="Security scanning",
                estimated_cost=50,
                frequency=CostFrequency.MONTHLY,
                justification="Continuous dependency and image scanning.",
            )
        ]
    )
    technical = TechnicalPlanningResult.model_construct(
        session_id=product.session_id,
        solution_architecture=solution,
        security_architecture=security,
        ai_architecture=None,
        qa_evaluation=None,
    )

    summary = aggregate_project_costs(
        product_planning=product,
        technical_planning=technical,
    )

    assert [estimate.source for estimate in summary.estimates] == [
        RevisionTarget.PRODUCT_DEFINITION,
        RevisionTarget.SOLUTION_ARCHITECTURE,
        RevisionTarget.SECURITY_ARCHITECTURE,
    ]
    assert len(summary.totals) == 1
    assert summary.totals[0].minimum == Decimal("350")
    assert summary.totals[0].expected == Decimal("500")
    assert summary.totals[0].maximum == Decimal("750")
    assert summary.totals[0].estimate_count == 3


def test_project_costs_do_not_combine_different_frequencies() -> None:
    _, product = build_product_planning_inputs()
    product_definition = product.product_definition.model_copy(
        update={
            "product_cost_estimates": [
                _range_cost(
                    name="Monthly service",
                    category=CostCategory.PRODUCT,
                    minimum="10",
                    expected="20",
                    maximum="30",
                ).model_copy(update={"frequency": CostFrequency.MONTHLY}),
                _range_cost(
                    name="Initial implementation",
                    category=CostCategory.PRODUCT,
                    minimum="100",
                    expected="200",
                    maximum="300",
                ).model_copy(update={"frequency": CostFrequency.ONE_TIME}),
            ]
        }
    )
    product = product.model_copy(update={"product_definition": product_definition})
    technical = TechnicalPlanningResult.model_construct(
        session_id=product.session_id,
        solution_architecture=SolutionArchitecture.model_construct(
            session_id=product.session_id,
            requirements_specification_id=product.requirements.id,
            architecture_cost_estimates=[],
        ),
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
    )

    summary = aggregate_project_costs(
        product_planning=product,
        technical_planning=technical,
    )

    assert {total.frequency for total in summary.totals} == {
        CostFrequency.MONTHLY,
        CostFrequency.ONE_TIME,
    }
