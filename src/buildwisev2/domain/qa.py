"""QA & Evaluation domain models — output of the Technical Planning Crew
(QA & Evaluation Architect).
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class QAEvaluationDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class TestSuite(BuildWiseModel):
    name: str
    scope: str
    description: str


class CriticalScenario(BuildWiseModel):
    name: str
    description: str
    related_requirement_ids: list[str] = Field(default_factory=list)


class ReleaseGate(BuildWiseModel):
    name: str
    criteria: str
    blocking: bool = True


class AIEvaluationPlanItem(BuildWiseModel):
    capability: str
    metric: str
    dataset_description: str


class QAEvaluationPlan(BuildWiseModel):
    """Structured output of the QA & Evaluation Architect's Task."""

    session_id: UUID
    quality_objectives: list[str]
    test_strategy: str
    test_suites: list[TestSuite]
    critical_scenarios: list[CriticalScenario] = Field(default_factory=list)
    acceptance_tests: list[str] = Field(default_factory=list)
    performance_validation: str
    reliability_validation: str
    security_control_validation: list[str] = Field(default_factory=list)
    ai_evaluation: list[AIEvaluationPlanItem] = Field(default_factory=list)
    release_gates: list[ReleaseGate]
    production_quality_signals: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    implementation_phases: list[str] = Field(default_factory=list)
    cost_estimates: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: QAEvaluationDecision
