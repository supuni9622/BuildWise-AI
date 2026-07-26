from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.common import (
    ConfidenceLevel,
    CostCategory,
    CostFrequency,
)
from buildwise.domain.enums import (
    RiskLikelihood,
    RiskSeverity,
)

# =============================================================================
# Test Strategy
# =============================================================================


class TestStrategy(BaseModel):
    """
    High-level testing strategy for the proposed solution.
    """

    model_config = ConfigDict(extra="forbid")

    objective: str

    testing_levels: list[str] = Field(
        default_factory=list,
        description="Unit, Integration, E2E, Load, Security etc.",
    )

    automation_percentage: Annotated[
        int,
        Field(
            ge=0,
            le=100,
        ),
    ] = 80

    continuous_testing: bool = True

    notes: str | None = None


# =============================================================================
# Test Suite
# =============================================================================


class TestSuite(BaseModel):
    """
    Logical collection of related test scenarios.
    """

    model_config = ConfigDict(extra="forbid")

    name: str

    purpose: str

    priority: RiskSeverity

    automated: bool = True

    scenarios: list[str] = Field(
        default_factory=list,
    )

    owner: str


# =============================================================================
# Test Scenario
# =============================================================================


class TestScenario(BaseModel):
    """
    Describes an end-to-end business scenario.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    title: str

    description: str

    preconditions: list[str] = Field(
        default_factory=list,
    )

    execution_steps: list[str] = Field(
        default_factory=list,
    )

    expected_result: str

    priority: RiskSeverity

    automated: bool = False


# =============================================================================
# Acceptance Test
# =============================================================================


class AcceptanceTest(BaseModel):
    """
    Business acceptance criteria verification.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    feature: str

    acceptance_criteria: list[str] = Field(
        default_factory=list,
    )

    validation_method: str

    expected_outcome: str

    owner: str

    notes: str | None = None


# =============================================================================
# Evaluation Metrics
# =============================================================================


class EvaluationMetric(BaseModel):
    """
    Defines a measurable quality metric.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Metric name.",
        examples=[
            "Response Time",
            "Availability",
            "Accuracy",
            "Latency",
            "Task Success Rate",
        ],
    )

    description: str

    target_value: str = Field(
        description="Desired target.",
        examples=[
            "< 300ms",
            "> 99.9%",
            "> 90%",
        ],
    )

    measurement_method: str

    owner: str

    notes: str | None = None


# =============================================================================
# Quality Requirements
# =============================================================================


class QualityRequirement(BaseModel):
    """
    Quality attribute that must be satisfied.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    title: str

    description: str

    rationale: str

    verification_method: str

    mandatory: bool = True


# =============================================================================
# Performance Requirements
# =============================================================================


class PerformanceRequirement(BaseModel):
    """
    Defines expected system performance.
    """

    model_config = ConfigDict(extra="forbid")

    maximum_response_time_ms: Annotated[
        int,
        Field(gt=0),
    ]

    expected_concurrent_users: Annotated[
        int,
        Field(gt=0),
    ]

    expected_requests_per_second: Annotated[
        int,
        Field(gt=0),
    ]

    availability_target: str = Field(
        examples=[
            "99%",
            "99.9%",
            "99.99%",
        ]
    )

    scalability_notes: str | None = None


# =============================================================================
# Reliability Requirements
# =============================================================================


class ReliabilityRequirement(BaseModel):
    """
    Reliability expectations for the system.
    """

    model_config = ConfigDict(extra="forbid")

    backup_required: bool = True

    disaster_recovery_required: bool = True

    recovery_time_objective: str = Field(
        description="RTO",
        examples=[
            "30 minutes",
            "2 hours",
        ],
    )

    recovery_point_objective: str = Field(
        description="RPO",
        examples=[
            "5 minutes",
            "30 minutes",
        ],
    )

    failover_supported: bool = False

    monitoring_required: bool = True

    notes: str | None = None


# =============================================================================
# Quality Risks
# =============================================================================


class QualityRisk(BaseModel):
    """
    Risk that could impact software quality.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    title: str

    description: str

    likelihood: RiskLikelihood

    severity: RiskSeverity

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    mitigation: str

    owner: str

    accepted: bool = False

    notes: str | None = None


# =============================================================================
# Release Gates
# =============================================================================


class ReleaseGate(BaseModel):
    """
    Defines a quality gate that must pass before release.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Release gate name.",
        examples=[
            "Architecture Review",
            "Security Review",
            "Regression Tests",
            "Performance Validation",
        ],
    )

    description: str

    mandatory: bool = True

    pass_criteria: list[str] = Field(
        default_factory=list,
        description="Conditions required to pass this gate.",
    )

    owner: str

    notes: str | None = None


# =============================================================================
# QA Cost Estimate
# =============================================================================


class QualityCostEstimate(BaseModel):
    """
    Estimated cost associated with QA and validation.
    """

    model_config = ConfigDict(extra="forbid")

    category: CostCategory = CostCategory.QA

    item: str

    estimated_cost: float = Field(
        ge=0,
    )

    frequency: CostFrequency

    justification: str

    optional: bool = False


# =============================================================================
# QA Evaluation Plan
# =============================================================================


class QAEvaluationPlan(BaseModel):
    """
    Complete QA and evaluation strategy produced by the
    QA & Evaluation Architect.
    """

    model_config = ConfigDict(extra="forbid")

    executive_summary: str

    test_strategy: TestStrategy

    test_suites: list[TestSuite] = Field(
        default_factory=list,
    )

    test_scenarios: list[TestScenario] = Field(
        default_factory=list,
    )

    acceptance_tests: list[AcceptanceTest] = Field(
        default_factory=list,
    )

    quality_requirements: list[QualityRequirement] = Field(
        default_factory=list,
    )

    performance_requirements: PerformanceRequirement

    reliability_requirements: ReliabilityRequirement

    evaluation_metrics: list[EvaluationMetric] = Field(
        default_factory=list,
    )

    release_gates: list[ReleaseGate] = Field(
        default_factory=list,
    )

    quality_risks: list[QualityRisk] = Field(
        default_factory=list,
    )

    estimated_costs: list[QualityCostEstimate] = Field(
        default_factory=list,
    )

    implementation_phases: list[str] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    overall_quality_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    notes: str | None = None
