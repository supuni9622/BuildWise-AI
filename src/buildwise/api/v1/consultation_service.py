"""Application service connecting HTTP consultation operations to CrewAI Flow."""

from __future__ import annotations

from collections.abc import Callable

from crewai.flow.persistence.base import FlowPersistence

from buildwise.domain.api import (
    ConsultationResponse,
    ConsultationResultResponse,
    StartConsultationRequest,
    SubmitClarificationsRequest,
)
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.enums import SessionStatus
from buildwise.flows.consulting_flow import BuildWiseConsultingFlow
from buildwise.flows.state import BuildWiseFlowState
from buildwise.persistence.flow_store import BuildWiseFlowStore

FlowFactory = Callable[[BuildWiseFlowState, FlowPersistence], BuildWiseConsultingFlow]

_COMPLETED_STATUSES = {
    SessionStatus.COMPLETED,
    SessionStatus.COMPLETED_WITH_LIMITATIONS,
}


def _default_flow_factory(
    state: BuildWiseFlowState,
    persistence: FlowPersistence,
) -> BuildWiseConsultingFlow:
    return BuildWiseConsultingFlow(initial_state=state, persistence=persistence)


class ConsultationService:
    """Run and reconstruct durable consulting Flows."""

    def __init__(
        self,
        *,
        flow_store: BuildWiseFlowStore,
        flow_factory: FlowFactory = _default_flow_factory,
    ) -> None:
        self._flow_store = flow_store
        self._flow_factory = flow_factory

    def start(self, request: StartConsultationRequest) -> ConsultationResponse:
        state = BuildWiseFlowState(intake_request=request)
        flow = self._flow_factory(state, self._flow_store)
        flow.kickoff()
        return self._response(flow.state)

    def submit_clarifications(
        self,
        consultation_id: str,
        request: SubmitClarificationsRequest,
    ) -> ConsultationResponse:
        state = self._load_state(consultation_id)
        if state.status is not SessionStatus.AWAITING_USER_INPUT:
            raise ValueError("The consultation is not awaiting clarification answers.")
        if request.clarification_round != state.clarification_round:
            raise ValueError(
                "clarification_round does not match the active clarification round."
            )

        flow = self._flow_factory(state, self._flow_store)
        flow.submit_clarification_answers(request.answers)
        self._flow_store.save_consultation_state(
            consultation_id,
            method_name="submit_clarification_answers",
            state_data=flow.state,
        )
        flow.kickoff()
        return self._response(flow.state)

    def get(self, consultation_id: str) -> ConsultationResponse:
        return self._response(self._load_state(consultation_id))

    def get_result(self, consultation_id: str) -> ConsultationResultResponse:
        state = self._load_state(consultation_id)
        if state.status not in _COMPLETED_STATUSES:
            raise ValueError("The consultation result is not available yet.")
        if not isinstance(state.product_blueprint, ProductBlueprint):
            raise ValueError("The completed consultation does not contain a product blueprint.")
        return ConsultationResultResponse(
            consultation_id=str(state.session_id),
            status=state.status,
            stage=state.stage,
            result=state.product_blueprint,
        )

    def _load_state(self, consultation_id: str) -> BuildWiseFlowState:
        state_data = self._flow_store.load_consultation_state(consultation_id)
        if state_data is None:
            raise LookupError(f"Consultation '{consultation_id}' was not found.")
        return BuildWiseFlowState.model_validate(state_data)

    @staticmethod
    def _response(state: BuildWiseFlowState) -> ConsultationResponse:
        question_set = state.clarification_question_set
        questions = (
            list(question_set.questions)
            if state.status is SessionStatus.AWAITING_USER_INPUT and question_set is not None
            else []
        )
        return ConsultationResponse(
            consultation_id=str(state.session_id),
            status=state.status,
            stage=state.stage,
            clarification_round=state.clarification_round,
            questions=questions,
        )
