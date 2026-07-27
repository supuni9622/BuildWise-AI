"""Mocked end-to-end coverage for the native BuildWise consulting Flow."""

from __future__ import annotations

from typing import Any

from crewai import CrewOutput
from pydantic import SecretStr

import buildwise.flows.consulting_flow as flow_module
from buildwise.config.settings import Settings
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.discovery import (
    ClarificationQuestion,
    ClarificationQuestionSet,
    CompletenessResult,
    DiscoveryResult,
    Unknown,
)
from buildwise.domain.enums import ReviewDecision, SessionStatus
from buildwise.domain.intake import ClarificationAnswer, ProductIdeaRequest
from buildwise.domain.review import LeadReview
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.flows.consulting_flow import BuildWiseConsultingFlow
from buildwise.flows.state import BuildWiseFlowState
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
            usage_summary={},
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


def test_mocked_consulting_flow_completes(monkeypatch: Any) -> None:
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

    flow = BuildWiseConsultingFlow(
        initial_state=state,
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
    assert flow.state.product_planning_result is product
    assert flow.state.technical_planning_result is technical
    assert flow.state.lead_review is review


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
