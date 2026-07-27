"""Mocked end-to-end coverage for the native BuildWise consulting Flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from crewai import CrewOutput
from pydantic import SecretStr
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import buildwise.flows.consulting_flow as flow_module
from buildwise.config.settings import Settings
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.blueprint import UsageSummary as BlueprintUsageSummary
from buildwise.domain.discovery import (
    ClarificationQuestion,
    ClarificationQuestionSet,
    CompletenessResult,
    DiscoveryResult,
    Unknown,
)
from buildwise.domain.enums import ReviewDecision, RevisionTarget, SessionStatus
from buildwise.domain.intake import ClarificationAnswer, ProductIdeaRequest
from buildwise.domain.review import LeadReview, RevisionRequest
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.flows.consulting_flow import BuildWiseConsultingFlow
from buildwise.flows.routing import FlowRoute, route_after_review
from buildwise.flows.state import BuildWiseFlowState
from buildwise.persistence.flow_store import BuildWiseFlowStore
from buildwise.persistence.models import ArtifactRecord, ConsultationRecord
from fixtures.planning import build_discovery_result, build_product_planning_inputs


class _FakeCrew:
    def __init__(self, output: CrewOutput) -> None:
        self._output = output

    def kickoff(self) -> CrewOutput:
        return self._output


class _BlueprintBuilder:
    def build(self, **_: Any) -> ProductBlueprint:
        return ProductBlueprint.model_construct(
            title="TeamSync blueprint",
            executive_summary="Build-ready plan.",
            sections=[],
            implementation_phases=[],
            assumptions=[],
            risks=[],
            recommendations=[],
            limitations=[],
            usage_summary=BlueprintUsageSummary(),
            generated_markdown="# TeamSync",
            version="1.0",
        )


def _settings() -> Settings:
    return Settings(
        debug=False,
        crewai_tracing_enabled=False,
        crewai_verbose=False,
        openai_api_key=SecretStr("sk-test"),
    )


def test_consulting_flow_uses_native_crewai_tracing_setting() -> None:
    enabled = BuildWiseConsultingFlow(
        initial_state=BuildWiseFlowState(),
        settings=Settings(crewai_tracing_enabled=True),
    )
    disabled = BuildWiseConsultingFlow(
        initial_state=BuildWiseFlowState(),
        settings=Settings(crewai_tracing_enabled=False),
    )

    assert enabled.tracing is True
    assert disabled.tracing is False


def test_mocked_consulting_flow_completes(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    state = BuildWiseFlowState(
        intake_request=ProductIdeaRequest(
            idea="A scheduling product for distributed teams across time zones."
        )
    )
    discovery, product = build_product_planning_inputs(session_id=state.session_id)
    solution = SolutionArchitecture.model_construct(
        id=product.requirements.id,
        session_id=state.session_id,
        requirements_specification_id=product.requirements.id,
    )
    technical = TechnicalPlanningResult.model_construct(
        session_id=state.session_id,
        solution_architecture=solution,
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
    )
    review = LeadReview(
        executive_summary="The plan is internally consistent.",
        decision=ReviewDecision.APPROVED,
        approved_for_blueprint=True,
    )

    monkeypatch.setattr(
        flow_module,
        "assemble_product_planning_result",
        lambda *_args, **_kwargs: product,
    )
    monkeypatch.setattr(
        flow_module,
        "assemble_technical_planning_result",
        lambda *_args, **_kwargs: technical,
    )

    engine = create_engine(f"sqlite:///{tmp_path / 'flow.db'}")
    flow = BuildWiseConsultingFlow(
        initial_state=state,
        settings=_settings(),
        blueprint_builder=_BlueprintBuilder(),
        discovery_crew_factory=lambda **_: _FakeCrew(CrewOutput(pydantic=discovery)),
        product_planning_crew_factory=lambda **_: _FakeCrew(CrewOutput()),
        technical_planning_crew_factory=lambda **_: _FakeCrew(CrewOutput()),
        lead_review_crew_factory=lambda **_: _FakeCrew(CrewOutput(pydantic=review)),
        persistence=BuildWiseFlowStore(engine),
    )

    result = flow.kickoff()

    assert isinstance(result, ProductBlueprint)
    assert flow.state.status is SessionStatus.COMPLETED
    assert flow.state.product_planning_result is product
    assert flow.state.technical_planning_result is technical
    assert flow.state.lead_review is review
    with Session(engine) as session:
        assert session.get(ConsultationRecord, str(state.session_id)) is not None
        artifact_types = set(session.scalars(select(ArtifactRecord.artifact_type)).all())
    assert artifact_types == {
        "blueprint",
        "discovery",
        "lead_review",
        "product_planning",
        "specialist_plan",
        "technical_planning",
    }


def test_created_flow_requires_intake() -> None:
    flow = BuildWiseConsultingFlow(
        initial_state=BuildWiseFlowState(),
        settings=_settings(),
    )

    try:
        flow.kickoff()
    except ValueError as error:
        assert "intake_request" in str(error)
    else:
        raise AssertionError("Flow kickoff unexpectedly accepted missing intake.")


def test_clarification_pauses_and_accepts_structured_answers() -> None:
    state = BuildWiseFlowState(
        intake_request=ProductIdeaRequest(
            idea="A scheduling product for distributed teams across time zones."
        )
    )
    base = build_discovery_result(session_id=state.session_id)
    unknown = Unknown(
        key="target_customer",
        description="The first target customer segment is unknown.",
        reason_missing="The intake does not identify the initial segment.",
        impact_areas=["product"],
        blocking=True,
        can_proceed_with_assumption=False,
        clarification_required=True,
    )
    question = ClarificationQuestion(
        key="target_customer",
        category="target_users",
        question="Which customer segment should the initial release serve?",
        rationale="The initial customer segment determines the MVP scope.",
        related_unknown_ids=[unknown.id],
        affected_areas=["product"],
    )
    question_set = ClarificationQuestionSet(
        session_id=state.session_id,
        round_number=1,
        questions=[question],
        summary="The target customer must be clarified.",
        blocking=True,
    )
    discovery = DiscoveryResult.model_validate(
        {
            **base.model_dump(),
            "unknowns": [unknown],
            "completeness": CompletenessResult(
                score=0.4,
                percentage=40,
                is_complete=False,
                can_continue=False,
                clarification_required=True,
                blocking_unknown_keys=[unknown.key],
                rationale="A blocking customer-segment unknown remains.",
            ),
            "clarification_questions": question_set,
            "recommended_next_step": "request_clarification",
        }
    )
    flow = BuildWiseConsultingFlow(
        initial_state=state,
        settings=_settings(),
        discovery_crew_factory=lambda **_: _FakeCrew(CrewOutput(pydantic=discovery)),
    )

    result = flow.kickoff()

    assert isinstance(result, BuildWiseFlowState)
    assert flow.state.status is SessionStatus.AWAITING_USER_INPUT
    flow.submit_clarification_answers(
        [
            ClarificationAnswer(
                question_id=question.id,
                answer="Small distributed software teams.",
            )
        ]
    )
    assert flow.state.status is SessionStatus.RESUMING
    assert flow.state.clarification_answers[0].question_id == question.id


def test_discovery_fixture_matches_flow_session() -> None:
    state = BuildWiseFlowState()
    discovery = build_discovery_result(session_id=state.session_id)

    assert discovery.session_id == state.session_id


@pytest.mark.parametrize(
    ("decision", "approved_for_blueprint", "revision_requests", "expected"),
    [
        (ReviewDecision.APPROVED, True, [], FlowRoute.ASSEMBLE_BLUEPRINT),
        (
            ReviewDecision.APPROVED_WITH_LIMITATIONS,
            True,
            [],
            FlowRoute.ASSEMBLE_BLUEPRINT,
        ),
        (
            ReviewDecision.REVISION_REQUIRED,
            False,
            [
                RevisionRequest(
                    target=RevisionTarget.REQUIREMENTS,
                    reason="Requirements need another pass.",
                )
            ],
            FlowRoute.RUN_TARGETED_REVISION,
        ),
        (ReviewDecision.REJECTED, False, [], FlowRoute.FAIL_FLOW),
    ],
)
def test_review_decisions_route_without_duplicate_booleans(
    decision: ReviewDecision,
    approved_for_blueprint: bool,
    revision_requests: list[RevisionRequest],
    expected: FlowRoute,
) -> None:
    review = LeadReview(
        executive_summary="Deterministic review-routing fixture.",
        decision=decision,
        approved_for_blueprint=approved_for_blueprint,
        revision_requests=revision_requests,
    )

    assert route_after_review(review) is expected


def test_revision_decision_requires_a_target() -> None:
    review = LeadReview(
        executive_summary="Revision is requested without actionable targets.",
        decision=ReviewDecision.REVISION_REQUIRED,
        approved_for_blueprint=False,
    )

    with pytest.raises(ValueError, match="revision requests"):
        route_after_review(review)


def test_revision_limit_routes_to_failure() -> None:
    state = BuildWiseFlowState(
        revision_count=2,
        lead_review=LeadReview(
            executive_summary="Another requirements revision is needed.",
            decision=ReviewDecision.REVISION_REQUIRED,
            revision_requests=[
                RevisionRequest(
                    target=RevisionTarget.REQUIREMENTS,
                    reason="Requirements remain inconsistent.",
                )
            ],
        ),
    )
    flow = BuildWiseConsultingFlow(initial_state=state, settings=_settings())

    assert flow.execute_targeted_revision() == FlowRoute.FAIL_FLOW.value


def test_serialized_clarification_state_resumes_through_completion(
    monkeypatch: Any,
) -> None:
    session_id = build_discovery_result().session_id
    discovery, product = build_product_planning_inputs(session_id=session_id)
    resuming_state = BuildWiseFlowState(
        session_id=session_id,
        intake_request=ProductIdeaRequest(
            idea="A scheduling product for distributed teams across time zones."
        ),
        status=SessionStatus.RESUMING,
        stage="clarification",
        product_context=build_discovery_result(session_id=session_id).idea_context,
        clarification_round=1,
        clarification_answers=[
            ClarificationAnswer(
                question_id=product.product_definition.id,
                answer="Small distributed software teams.",
            )
        ],
    )
    restored_state = BuildWiseFlowState.model_validate(resuming_state.model_dump(mode="json"))
    solution = SolutionArchitecture.model_construct(
        id=product.requirements.id,
        session_id=session_id,
        requirements_specification_id=product.requirements.id,
    )
    technical = TechnicalPlanningResult.model_construct(
        session_id=session_id,
        solution_architecture=solution,
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
    )
    review = LeadReview(
        executive_summary="The resumed plan is ready.",
        decision=ReviewDecision.APPROVED,
        approved_for_blueprint=True,
    )
    monkeypatch.setattr(
        flow_module,
        "assemble_product_planning_result",
        lambda *_args, **_kwargs: product,
    )
    monkeypatch.setattr(
        flow_module,
        "assemble_technical_planning_result",
        lambda *_args, **_kwargs: technical,
    )
    flow = BuildWiseConsultingFlow(
        initial_state=restored_state,
        settings=_settings(),
        blueprint_builder=_BlueprintBuilder(),
        discovery_crew_factory=lambda **_: _FakeCrew(CrewOutput(pydantic=discovery)),
        product_planning_crew_factory=lambda **_: _FakeCrew(CrewOutput()),
        technical_planning_crew_factory=lambda **_: _FakeCrew(CrewOutput()),
        lead_review_crew_factory=lambda **_: _FakeCrew(CrewOutput(pydantic=review)),
    )

    result = flow.kickoff()

    assert isinstance(result, ProductBlueprint)
    assert flow.state.status is SessionStatus.COMPLETED
