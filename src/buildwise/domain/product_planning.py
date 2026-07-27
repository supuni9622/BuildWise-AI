"""Aggregate result produced by the BuildWise Product Planning Crew.

This module does not redefine ProductDefinition, MarketAndGTMStrategy, or
RequirementsSpecification.

It provides one typed execution result that groups the canonical artifacts
created during the Product Planning Crew execution.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    SessionId,
    generate_uuid,
    utc_now,
)
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification


class ProductPlanningResult(BuildWiseModel):
    """Canonical aggregate output of the Product Planning Crew.

    The aggregate preserves the individual specialist artifacts rather than
    copying their fields into another model.

    Expected execution order:

        ProductDefinition
            ↓
        MarketAndGTMStrategy — optional
            ↓
        RequirementsSpecification

    MarketAndGTMStrategy is optional because market and GTM work may be omitted
    for consultations that do not require commercial analysis.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    session_id: SessionId = Field(
        description=("Consulting session that owns all Product Planning artifacts."),
    )

    product_definition: ProductDefinition = Field(
        description="Canonical output produced by the Product Manager.",
    )

    market_and_gtm: MarketAndGTMStrategy | None = Field(
        default=None,
        description=(
            "Optional market and go-to-market strategy produced after the "
            "ProductDefinition is available."
        ),
    )

    requirements: RequirementsSpecification = Field(
        description="Canonical output produced by the Business Analyst.",
    )

    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at")
    @classmethod
    def normalize_generated_at(cls, value: datetime) -> datetime:
        """Require a timezone-aware timestamp and normalize it to UTC."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware.")

        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_product_planning_result(
        self,
    ) -> ProductPlanningResult:
        """Validate ownership and references across planning artifacts."""

        if self.product_definition.session_id != self.session_id:
            raise ValueError(
                "ProductDefinition.session_id must match ProductPlanningResult.session_id."
            )

        if self.requirements.session_id != self.session_id:
            raise ValueError(
                "RequirementsSpecification.session_id must match ProductPlanningResult.session_id."
            )

        if self.requirements.product_definition_id != self.product_definition.id:
            raise ValueError(
                "RequirementsSpecification.product_definition_id must match ProductDefinition.id."
            )

        if self.market_and_gtm is not None:
            if self.market_and_gtm.session_id != self.session_id:
                raise ValueError(
                    "MarketAndGTMStrategy.session_id must match ProductPlanningResult.session_id."
                )

            if self.market_and_gtm.product_definition_id != self.product_definition.id:
                raise ValueError(
                    "MarketAndGTMStrategy.product_definition_id must match ProductDefinition.id."
                )

            MarketAndGTMStrategy.validate_product_ownership(
                market_and_gtm_strategy=self.market_and_gtm,
                product_definition=self.product_definition,
            )

        return self
