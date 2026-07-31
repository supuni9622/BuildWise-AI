"""Unit tests for deterministic blueprint assembly. No LLM calls."""

from __future__ import annotations

from uuid import uuid4

from buildwisev2.domain.architecture import (
    DeploymentView,
    SolutionArchitecture,
    SolutionArchitectureDecision,
)
from buildwisev2.domain.discovery import (
    CapabilityClassification,
    CompletenessAssessment,
    DiscoveryDecision,
    DiscoveryResult,
)
from buildwisev2.domain.product import ProductDefinition, ProductDefinitionDecision
from buildwisev2.domain.qa import QAEvaluationDecision, QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsDecision, RequirementsSpecification
from buildwisev2.domain.review import LeadReview, ReviewDecision
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    BudgetDecisionType,
    SpecialistExecutionPlan,
)
from buildwisev2.reporting.blueprint_builder import _derive_title, build_blueprint


def _base_artifacts(session_id):
    discovery = DiscoveryResult(
        session_id=session_id,
        interpreted_idea="A scheduling tool.",
        known_facts=["Used by field technicians."],
        capability_classification=CapabilityClassification(),
        completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
        decision=DiscoveryDecision.CONTINUE,
        confidence=0.9,
        limitations=["Discovery limitation."],
    )
    product_definition = ProductDefinition(
        session_id=session_id,
        vision="Help technicians schedule visits easily.",
        value_proposition="Removes manual dispatch.",
        goals=["g"],
        personas=[],
        features=[],
        mvp_feature_ids=[],
        open_questions=["What is the rollout timeline?"],
        decision=ProductDefinitionDecision.APPROVED,
    )
    requirements = RequirementsSpecification(
        session_id=session_id,
        functional_requirements=[],
        non_functional_requirements=[],
        decision=RequirementsDecision.APPROVED,
    )
    solution_architecture = SolutionArchitecture(
        session_id=session_id,
        system_context="A scheduling tool.",
        components=[],
        deployment=DeploymentView(description="single region"),
        scalability_strategy="n/a",
        reliability_strategy="n/a",
        observability_strategy="n/a",
        decision=SolutionArchitectureDecision.APPROVED,
    )
    lead_review = LeadReview(
        session_id=session_id,
        implementation_readiness_score=0.85,
        decision=ReviewDecision.APPROVED,
        approved_for_blueprint=True,
    )
    specialist_plan = SpecialistExecutionPlan(
        recommendations=[],
        execution_groups=[],
        dependencies=[],
        budget=BudgetDecision(decision=BudgetDecisionType.APPROVED, explanation="ok"),
        execution_summary="summary",
    )
    return (
        discovery,
        product_definition,
        requirements,
        solution_architecture,
        lead_review,
        specialist_plan,
    )


def test_build_blueprint_without_optional_specialists_omits_their_sections() -> None:
    session_id = uuid4()
    discovery, pd, req, sol, review, plan = _base_artifacts(session_id)

    blueprint = build_blueprint(
        discovery=discovery,
        product_definition=pd,
        requirements=req,
        specialist_plan=plan,
        solution_architecture=sol,
        lead_review=review,
    )

    section_names = [s.section for s in blueprint.sections]
    assert section_names == [
        "discovery",
        "product_definition",
        "requirements",
        "solution_architecture",
        "lead_review",
    ]
    assert blueprint.session_id == session_id
    assert "Discovery limitation." in blueprint.limitations
    assert "What is the rollout timeline?" in blueprint.open_questions
    assert blueprint.generated_markdown.startswith(f"# {blueprint.title}")


def test_build_blueprint_with_qa_evaluation_includes_its_section() -> None:
    session_id = uuid4()
    discovery, pd, req, sol, review, plan = _base_artifacts(session_id)
    qa = QAEvaluationPlan(
        session_id=session_id,
        quality_objectives=["Ship reliably."],
        test_strategy="Automated regression suite.",
        test_suites=[],
        performance_validation="Load test at 2x expected traffic.",
        reliability_validation="Chaos test dependency failures.",
        release_gates=[],
        decision=QAEvaluationDecision.APPROVED,
    )

    blueprint = build_blueprint(
        discovery=discovery,
        product_definition=pd,
        requirements=req,
        specialist_plan=plan,
        solution_architecture=sol,
        lead_review=review,
        qa_evaluation=qa,
    )

    section_names = [s.section for s in blueprint.sections]
    assert "qa_evaluation" in section_names
    assert section_names.index("solution_architecture") < section_names.index("qa_evaluation")
    assert section_names.index("qa_evaluation") < section_names.index("lead_review")


def test_derive_title_uses_first_sentence_when_short() -> None:
    assert _derive_title("Help technicians schedule visits. More detail follows.") == (
        "Help technicians schedule visits"
    )


def test_derive_title_caps_length_when_vision_has_no_early_sentence_break() -> None:
    # Reproduces a real agent behavior observed live: echoing a long,
    # unpunctuated brief back as the "vision" instead of synthesizing one.
    vision = (
        "I want to build an AI consulting platform that transforms vague software "
        "product ideas into implementation-ready technical blueprints Users should "
        "describe their idea in natural language and the platform should identify "
        "missing information automatically without any human intervention at all"
    )

    title = _derive_title(vision)

    assert len(title) <= 91  # _MAX_TITLE_LENGTH + ellipsis char
    assert title.endswith("…")
    assert not title[:-1].endswith(" ")
