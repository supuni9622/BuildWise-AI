"""Aggregate result models produced by the Product Planning and Technical Planning Crews.

These exist because a Crew executes several Tasks, each with its own
structured output, but the Flow needs one canonical artifact per Crew
execution to store in Flow state and pass to downstream Crews.
"""

from __future__ import annotations

from uuid import UUID

from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.common import BuildWiseModel
from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.qa import QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.security_architecture import SecurityArchitecture


class ProductPlanningResult(BuildWiseModel):
    """Aggregate output of the Product Planning Crew."""

    session_id: UUID
    market_and_gtm: MarketAndGTMStrategy | None = None
    product_definition: ProductDefinition
    requirements: RequirementsSpecification


class TechnicalPlanningResult(BuildWiseModel):
    """Aggregate output of the Technical Planning Crew."""

    session_id: UUID
    solution_architecture: SolutionArchitecture
    ai_architecture: AIArchitecture | None = None
    security_architecture: SecurityArchitecture | None = None
    qa_evaluation: QAEvaluationPlan | None = None
