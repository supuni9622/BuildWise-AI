"""Discovery domain models — output of the Discovery Crew."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel, CapabilityType


class DiscoveryDecision(StrEnum):
    CONTINUE = "continue"
    CLARIFICATION_REQUIRED = "clarification_required"
    CONTINUE_WITH_LIMITATIONS = "continue_with_limitations"
    FAILED = "failed"


class CapabilityClassification(BuildWiseModel):
    """Preliminary, non-binding capability signals used by the deterministic planner."""

    capabilities: list[CapabilityType] = Field(default_factory=list)
    ai_required: bool = False
    rag_required: bool = False
    agents_required: bool = False
    automation_required: bool = False
    sensitive_data_detected: bool = False
    regulated_domain_detected: bool = False
    real_time_processing_required: bool = False
    external_integrations_expected: bool = False
    specialist_signals: list[str] = Field(default_factory=list)


class CompletenessAssessment(BuildWiseModel):
    """Whether the submitted idea has enough information to proceed."""

    can_continue: bool
    completeness_score: float
    blocking_unknowns: list[str] = Field(default_factory=list)
    non_blocking_unknowns: list[str] = Field(default_factory=list)


class DiscoveryResult(BuildWiseModel):
    """Structured output of the Discovery Crew's Product Discovery Analyst."""

    session_id: UUID
    interpreted_idea: str
    known_facts: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    capability_classification: CapabilityClassification
    completeness: CompletenessAssessment
    clarification_questions: list[str] = Field(default_factory=list)
    decision: DiscoveryDecision
    limitations: list[str] = Field(default_factory=list)
    confidence: float
