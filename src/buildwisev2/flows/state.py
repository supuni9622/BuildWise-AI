"""Typed state for the BuildWise v2 Consulting Flow."""

from __future__ import annotations

from enum import StrEnum

from crewai.flow.flow import FlowState
from pydantic import Field

from buildwisev2.domain.blueprint import ProductBlueprint
from buildwisev2.domain.common import FlowRuntimeLimits
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.intake import ProductIdeaContext, ProductIdeaRequest
from buildwisev2.domain.planning_results import ProductPlanningResult, TechnicalPlanningResult
from buildwisev2.domain.review import LeadReview, RevisionRequest
from buildwisev2.domain.specialist_planning import SpecialistExecutionPlan


class FlowStage(StrEnum):
    STARTED = "started"
    DISCOVERY = "discovery"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    PRODUCT_PLANNING = "product_planning"
    SPECIALIST_PLANNING = "specialist_planning"
    TECHNICAL_PLANNING = "technical_planning"
    LEAD_REVIEW = "lead_review"
    REVISION = "revision"
    COMPLETED = "completed"
    COMPLETED_WITH_LIMITATIONS = "completed_with_limitations"
    FAILED = "failed"
    REJECTED = "rejected"


class ConsultingFlowState(FlowState):
    """Canonical, structured state for one BuildWise consultation session."""

    stage: FlowStage = FlowStage.STARTED
    limits: FlowRuntimeLimits = FlowRuntimeLimits()

    product_idea: ProductIdeaRequest | None = None
    clarification_context: ProductIdeaContext | None = None

    discovery_result: DiscoveryResult | None = None
    product_planning_result: ProductPlanningResult | None = None
    specialist_plan: SpecialistExecutionPlan | None = None
    technical_planning_result: TechnicalPlanningResult | None = None
    lead_review: LeadReview | None = None
    blueprint: ProductBlueprint | None = None

    revision_history: list[RevisionRequest] = Field(default_factory=list)
    revision_count: int = 0

    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
