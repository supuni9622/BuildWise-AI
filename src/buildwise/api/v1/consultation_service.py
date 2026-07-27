"""Application service connecting HTTP consultation operations to CrewAI Flow."""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock

import structlog
from crewai.flow.persistence.base import FlowPersistence

from buildwise.application.error_normalizer import normalize_session_error
from buildwise.application.input_guardrail import InputGuardrailProcessor
from buildwise.config.settings import get_settings
from buildwise.domain.api import (
    ConsultationResponse,
    ConsultationResultResponse,
    StartConsultationRequest,
    SubmitClarificationsRequest,
)
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.enums import SessionStatus
from buildwise.domain.exceptions import ActiveSessionLimitExceeded
from buildwise.domain.session import SessionError
from buildwise.flows.consulting_flow import BuildWiseConsultingFlow
from buildwise.flows.state import BuildWiseFlowState
from buildwise.persistence.flow_store import BuildWiseFlowStore

FlowFactory = Callable[[BuildWiseFlowState, FlowPersistence], BuildWiseConsultingFlow]

_COMPLETED_STATUSES = {
    SessionStatus.COMPLETED,
    SessionStatus.COMPLETED_WITH_LIMITATIONS,
}
logger = structlog.get_logger(__name__)


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
        input_guardrail: InputGuardrailProcessor | None = None,
        maximum_active_consultations: int | None = None,
    ) -> None:
        self._flow_store = flow_store
        self._flow_factory = flow_factory
        self._input_guardrail = input_guardrail or InputGuardrailProcessor()
        self._maximum_active_consultations = (
            maximum_active_consultations
            if maximum_active_consultations is not None
            else get_settings().max_active_consultations
        )
        self._active_consultations: set[str] = set()
        self._active_lock = Lock()

    def enqueue_start(self, request: StartConsultationRequest) -> ConsultationResponse:
        """Persist a new consultation before background execution begins."""

        self._input_guardrail.require_allowed(request)
        state = BuildWiseFlowState(intake_request=request)
        consultation_id = str(state.session_id)
        self._reserve_execution(consultation_id)
        try:
            self._flow_store.save_state(
                consultation_id,
                method_name="consultation_queued",
                state_data=state,
            )
        except Exception:
            self._release_execution(consultation_id)
            raise
        return self._response(state)

    def enqueue_clarifications(
        self,
        consultation_id: str,
        request: SubmitClarificationsRequest,
    ) -> ConsultationResponse:
        self._input_guardrail.require_allowed(request)
        state = self._load_state(consultation_id)
        if state.status is not SessionStatus.AWAITING_USER_INPUT:
            raise ValueError("The consultation is not awaiting clarification answers.")
        if request.clarification_round != state.clarification_round:
            raise ValueError(
                "clarification_round does not match the active clarification round."
            )

        self._reserve_execution(consultation_id)
        try:
            flow = self._flow_factory(state, self._flow_store)
            flow.submit_clarification_answers(request.answers)
            self._flow_store.save_consultation_state(
                consultation_id,
                method_name="submit_clarification_answers",
                state_data=flow.state,
            )
        except Exception:
            self._release_execution(consultation_id)
            raise
        return self._response(flow.state)

    def run(self, consultation_id: str) -> None:
        """Execute one queued or resumed Flow outside the HTTP response path."""

        self._reserve_execution(consultation_id, allow_existing=True)
        try:
            state = self._load_state(consultation_id)
            flow = self._flow_factory(state, self._flow_store)
            try:
                flow.kickoff()
            except Exception as error:
                logger.exception(
                    "background_consultation_failed",
                    consultation_id=consultation_id,
                )
                failed_state = self._load_state(consultation_id)
                if not failed_state.is_terminal:
                    failed_state.mark_failed(
                        error=normalize_session_error(
                            error,
                            stage=failed_state.stage,
                        )
                    )
                    self._flow_store.save_consultation_state(
                        consultation_id,
                        method_name="background_execution_failed",
                        state_data=failed_state,
                    )
        finally:
            self._release_execution(consultation_id)

    def get(self, consultation_id: str) -> ConsultationResponse:
        state = self._load_state(consultation_id)
        if state.status in {
            SessionStatus.PROCESSING,
            SessionStatus.RESUMING,
            SessionStatus.REVIEWING,
        }:
            with self._active_lock:
                is_active = consultation_id in self._active_consultations
            if not is_active:
                state.mark_failed(
                    error=SessionError(
                        code="background_execution_interrupted",
                        message=(
                            "Background execution was interrupted by an application "
                            "restart. Start a new consultation."
                        ),
                        stage=state.stage,
                    )
                )
                self._flow_store.save_consultation_state(
                    consultation_id,
                    method_name="background_execution_interrupted",
                    state_data=state,
                )
        return self._response(state)

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

    def _reserve_execution(
        self,
        consultation_id: str,
        *,
        allow_existing: bool = False,
    ) -> None:
        with self._active_lock:
            if allow_existing and consultation_id in self._active_consultations:
                return
            if len(self._active_consultations) >= self._maximum_active_consultations:
                raise ActiveSessionLimitExceeded(
                    "The service is at its active consultation limit. Please retry later."
                )
            self._active_consultations.add(consultation_id)

    def _release_execution(self, consultation_id: str) -> None:
        with self._active_lock:
            self._active_consultations.discard(consultation_id)

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
            active_operation=ConsultationService._active_operation(state),
        )

    @staticmethod
    def _active_operation(state: BuildWiseFlowState) -> str | None:
        if state.status is SessionStatus.CREATED:
            return "Queued for discovery"
        if state.status is SessionStatus.RESUMING:
            return "Re-evaluating discovery"
        if state.status is SessionStatus.AWAITING_USER_INPUT:
            return "Waiting for clarification answers"
        if state.status in _COMPLETED_STATUSES or state.status is SessionStatus.FAILED:
            return None
        operations = {
            "intake": "Preparing consultation",
            "discovery": "Analyzing product discovery",
            "product_definition": "Defining product and MVP scope",
            "requirements": "Writing requirements",
            "specialist_planning": "Selecting specialists",
            "specialist_execution": "Designing solution architecture",
            "lead_review": "Performing lead review",
            "refinement": "Applying review revisions",
            "blueprint_assembly": "Assembling product blueprint",
        }
        return operations.get(state.stage.value, "Processing consultation")
