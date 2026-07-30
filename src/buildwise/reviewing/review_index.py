"""Deterministic compact index supplied to the Lead Reviewer."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import BuildWiseModel
from buildwise.domain.costs import CostSummary, ProjectCostTotal
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import SpecialistType
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.domain.specialist_planning import SpecialistExecutionPlan


class ArtifactReviewEntry(BuildWiseModel):
    name: str
    required: bool
    selected: bool
    present: bool
    decision: str | None = None
    confidence: str | None = None
    limitation_count: int = Field(ge=0)
    open_question_count: int = Field(ge=0)
    risk_count: int = Field(ge=0)


class DeterministicReviewFinding(BuildWiseModel):
    code: str
    severity: Literal["info", "warning", "blocking"]
    artifact: str
    message: str


class TraceabilityCoverage(BuildWiseModel):
    must_have_requirements: int = Field(ge=0)
    mapped_must_have_requirements: int = Field(ge=0)
    ai_capabilities: int = Field(ge=0)
    evaluated_ai_capabilities: int = Field(ge=0)
    security_threats: int = Field(ge=0)
    security_controls: int = Field(ge=0)
    qa_scenarios: int = Field(ge=0)
    release_gates: int = Field(ge=0)


class LeadReviewIndex(BuildWiseModel):
    """Small cross-artifact decision and validation summary."""

    artifacts: list[ArtifactReviewEntry]
    selected_specialists: list[SpecialistType]
    excluded_specialists: list[SpecialistType]
    unresolved_limitations: list[str]
    deterministic_findings: list[DeterministicReviewFinding]
    traceability: TraceabilityCoverage
    cost_totals: list[ProjectCostTotal]
    cost_estimate_count: int = Field(ge=0)
    revision_history: list[RevisionRequest] = Field(default_factory=list)


def build_lead_review_index(
    *,
    discovery: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    cost_summary: CostSummary,
    market_and_gtm: MarketAndGTMStrategy | None,
    solution_architecture: SolutionArchitecture | None,
    ai_architecture: AIArchitecture | None,
    security_architecture: SecurityArchitecture | None,
    qa_evaluation: QAEvaluationPlan | None,
    revision_history: list[RevisionRequest] | None,
) -> LeadReviewIndex:
    selected = {recommendation.specialist for recommendation in specialist_plan.recommendations}
    optional: list[tuple[str, SpecialistType, Any | None]] = [
        ("market_and_gtm", SpecialistType.MARKET_AND_GTM, market_and_gtm),
        (
            "solution_architecture",
            SpecialistType.SOLUTION_ARCHITECTURE,
            solution_architecture,
        ),
        ("ai_architecture", SpecialistType.AI_ARCHITECTURE, ai_architecture),
        (
            "security_architecture",
            SpecialistType.SECURITY_ARCHITECTURE,
            security_architecture,
        ),
        ("qa_and_evaluation", SpecialistType.QA_AND_EVALUATION, qa_evaluation),
    ]
    artifacts = [
        _entry("discovery", discovery, required=True, selected=True),
        _entry("product_definition", product_definition, required=True, selected=True),
        _entry("requirements", requirements, required=True, selected=True),
        *[
            _entry(
                name,
                artifact,
                required=specialist in selected
                and specialist is SpecialistType.SOLUTION_ARCHITECTURE,
                selected=specialist in selected,
            )
            for name, specialist, artifact in optional
        ],
    ]
    findings = [
        DeterministicReviewFinding(
            code="selected_artifact_missing",
            severity="blocking",
            artifact=name,
            message=f"Selected specialist artifact '{name}' is missing.",
        )
        for name, specialist, artifact in optional
        if specialist in selected and artifact is None
    ]

    must_have_ids = {
        requirement.id
        for requirement in requirements.functional_requirements
        if requirement.priority.value == "must_have"
    }
    mapped_ids = (
        {
            requirement_id
            for component in solution_architecture.components
            for requirement_id in component.related_functional_requirement_ids
        }
        if solution_architecture is not None
        else set()
    )
    missing_mappings = must_have_ids.difference(mapped_ids)
    if missing_mappings:
        findings.append(
            DeterministicReviewFinding(
                code="must_have_traceability_gap",
                severity="blocking",
                artifact="solution_architecture",
                message=(
                    f"{len(missing_mappings)} must-have functional requirements "
                    "lack component coverage."
                ),
            )
        )

    ai_capability_ids = (
        {capability.id for capability in ai_architecture.capabilities}
        if ai_architecture is not None
        else set()
    )
    evaluated_ai_ids = (
        {
            capability_id
            for metric in ai_architecture.evaluation_metrics
            for capability_id in metric.related_capability_ids
        }
        if ai_architecture is not None
        else set()
    )
    threats = (
        len(security_architecture.threat_model.threats) if security_architecture is not None else 0
    )
    controls = len(security_architecture.controls) if security_architecture else 0

    limitations = _unique(
        [
            *discovery.limitations,
            *product_definition.limitations,
            *requirements.limitations,
            *(solution_architecture.limitations if solution_architecture is not None else []),
            *(ai_architecture.limitations if ai_architecture is not None else []),
            *(security_architecture.assumptions if security_architecture else []),
            *(qa_evaluation.assumptions if qa_evaluation else []),
            *specialist_plan.budget.limitations,
        ]
    )
    return LeadReviewIndex(
        artifacts=artifacts,
        selected_specialists=sorted(selected, key=lambda item: item.value),
        excluded_specialists=sorted(
            set(SpecialistType).difference(selected),
            key=lambda item: item.value,
        ),
        unresolved_limitations=limitations,
        deterministic_findings=findings,
        traceability=TraceabilityCoverage(
            must_have_requirements=len(must_have_ids),
            mapped_must_have_requirements=len(must_have_ids.intersection(mapped_ids)),
            ai_capabilities=len(ai_capability_ids),
            evaluated_ai_capabilities=len(ai_capability_ids.intersection(evaluated_ai_ids)),
            security_threats=threats,
            security_controls=controls,
            qa_scenarios=len(qa_evaluation.test_scenarios) if qa_evaluation else 0,
            release_gates=len(qa_evaluation.release_gates) if qa_evaluation else 0,
        ),
        cost_totals=cost_summary.totals,
        cost_estimate_count=len(cost_summary.estimates),
        revision_history=revision_history or [],
    )


def _entry(
    name: str,
    artifact: Any | None,
    *,
    required: bool,
    selected: bool,
) -> ArtifactReviewEntry:
    return ArtifactReviewEntry(
        name=name,
        required=required,
        selected=selected,
        present=artifact is not None,
        decision=(
            str(getattr(artifact, "decision", None))
            if getattr(artifact, "decision", None) is not None
            else None
        ),
        confidence=_confidence(artifact),
        limitation_count=len(getattr(artifact, "limitations", []) or []),
        open_question_count=len(getattr(artifact, "open_questions", []) or []),
        risk_count=len(
            getattr(artifact, "risks", None)
            or getattr(artifact, "residual_risks", None)
            or getattr(artifact, "quality_risks", None)
            or []
        ),
    )


def _confidence(artifact: Any | None) -> str | None:
    if artifact is None:
        return None
    value = (
        getattr(artifact, "confidence", None)
        or getattr(artifact, "overall_security_posture", None)
        or getattr(artifact, "overall_quality_confidence", None)
    )
    return str(value) if value is not None else None


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
