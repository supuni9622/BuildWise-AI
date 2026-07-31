"""Application service gluing the REST contract to ``ConsultingFlow``.

Owns: translating the frontend's intake shape into ``ProductIdeaRequest``,
running the Flow in a background thread so HTTP requests return
immediately, and mapping ``ConsultingFlowState`` to the response schemas
the frontend expects.
"""

from __future__ import annotations

import threading
from uuid import uuid4

from buildwisev2.api.schemas import (
    BlueprintSchema,
    BlueprintSectionSchema,
    ClarificationSubmission,
    ConsultationResponse,
    IntakeRequest,
    QuestionSchema,
)
from buildwisev2.api.store import STORE, ConsultationSession
from buildwisev2.domain.blueprint import ProductBlueprint
from buildwisev2.domain.intake import ClarificationAnswer, ProductIdeaContext, ProductIdeaRequest
from buildwisev2.flows.state import FlowStage

_STAGE_LABELS: dict[FlowStage, str] = {
    FlowStage.STARTED: "intake",
    FlowStage.DISCOVERY: "discovery",
    FlowStage.AWAITING_CLARIFICATION: "clarification",
    FlowStage.PRODUCT_PLANNING: "product_definition",
    FlowStage.SPECIALIST_PLANNING: "specialist_planning",
    FlowStage.TECHNICAL_PLANNING: "specialist_execution",
    FlowStage.LEAD_REVIEW: "lead_review",
    FlowStage.REVISION: "lead_review",
    FlowStage.COMPLETED: "completed",
    FlowStage.COMPLETED_WITH_LIMITATIONS: "completed",
    FlowStage.FAILED: "failed",
    FlowStage.REJECTED: "failed",
}

_ACTIVE_OPERATION_MESSAGES: dict[FlowStage, str] = {
    FlowStage.STARTED: "Preparing your consultation.",
    FlowStage.DISCOVERY: "Interpreting your product idea.",
    FlowStage.PRODUCT_PLANNING: "Defining the product and requirements.",
    FlowStage.SPECIALIST_PLANNING: "Selecting the specialists this product needs.",
    FlowStage.TECHNICAL_PLANNING: "Designing the technical architecture.",
    FlowStage.LEAD_REVIEW: "Running the final cross-specialist review.",
    FlowStage.REVISION: "Applying targeted revisions.",
}


def start_consultation(request: IntakeRequest) -> ConsultationResponse:
    session_id = uuid4()
    product_idea = ProductIdeaRequest(
        session_id=session_id,
        title=request.title,
        raw_idea=_compose_idea_text(request),
        target_users=", ".join(request.target_users) if request.target_users else None,
        known_constraints=_compose_constraints(request),
    )

    flow = STORE.new_flow()
    flow.state.id = str(session_id)
    flow.state.product_idea = product_idea

    session = ConsultationSession(consultation_id=str(session_id), flow=flow)
    STORE.register(session)
    _run_in_background(session)
    return _to_response(session)


def get_consultation(consultation_id: str) -> ConsultationResponse | None:
    session = STORE.get(consultation_id)
    if session is None:
        return None
    return _to_response(session)


def submit_clarifications(
    consultation_id: str,
    submission: ClarificationSubmission,
) -> ConsultationResponse | None:
    session = STORE.get(consultation_id)
    if session is None:
        return None

    with session.lock:
        existing = session.flow.state.clarification_context
        answers = list(existing.clarification_answers) if existing is not None else []
        for answer in submission.answers:
            question_text = session.pending_questions.get(answer.question_id, answer.question_id)
            answers.append(ClarificationAnswer(question=question_text, answer=str(answer.answer)))

        session.flow.state.clarification_context = ProductIdeaContext(
            session_id=session.flow.state.product_idea.session_id,
            clarification_answers=answers,
            clarification_round=submission.clarification_round + 1,
        )
        session.error = None

    _run_in_background(session)
    return _to_response(session)


def get_result(consultation_id: str) -> BlueprintSchema | None:
    session = STORE.get(consultation_id)
    if session is None or session.flow.state.blueprint is None:
        return None
    return _blueprint_to_schema(session.flow.state.blueprint)


def _run_in_background(session: ConsultationSession) -> None:
    def _worker() -> None:
        try:
            session.flow.kickoff()
        except Exception as exc:  # surfaced to the caller via status, never crashes the server
            with session.lock:
                session.error = str(exc)

    thread = threading.Thread(target=_worker, daemon=True)
    session.thread = thread
    thread.start()


def _compose_idea_text(request: IntakeRequest) -> str:
    lines = [request.idea.strip()]
    if request.known_features:
        lines.append("Known desired features: " + ", ".join(request.known_features) + ".")
    if request.target_platforms:
        lines.append("Target platform(s): " + ", ".join(request.target_platforms) + ".")
    if request.delivery_expectation:
        lines.append(f"Delivery expectation: {request.delivery_expectation}.")
    if request.requests_ai_capabilities is not None:
        verb = "does" if request.requests_ai_capabilities else "does not"
        lines.append(f"The user indicates this product {verb} require AI capabilities.")
    if request.handles_sensitive_data is not None:
        verb = "does" if request.handles_sensitive_data else "does not"
        lines.append(f"The user indicates this product {verb} handle sensitive data.")
    return "\n".join(lines)


def _compose_constraints(request: IntakeRequest) -> list[str]:
    constraints = []
    if request.preferred_timeline:
        constraints.append(f"Preferred timeline: {request.preferred_timeline}")
    if request.estimated_budget:
        constraints.append(f"Estimated budget: {request.estimated_budget}")
    return constraints


def _build_questions(raw_questions: list[str]) -> list[QuestionSchema]:
    return [
        QuestionSchema(
            id=f"q{index + 1}",
            category="discovery",
            question=text,
            question_type="free_text",
            rationale="This helps BuildWise sharpen scope before continuing.",
            required=True,
        )
        for index, text in enumerate(raw_questions)
    ]


def _map_status(session: ConsultationSession) -> str:
    if session.error is not None:
        return "failed"
    stage = session.flow.state.stage
    if stage == FlowStage.AWAITING_CLARIFICATION:
        return "awaiting_user_input"
    if stage == FlowStage.COMPLETED:
        return "completed"
    if stage == FlowStage.COMPLETED_WITH_LIMITATIONS:
        return "completed_with_limitations"
    if stage in (FlowStage.FAILED, FlowStage.REJECTED):
        return "failed"
    return "running"


def _to_response(session: ConsultationSession) -> ConsultationResponse:
    state = session.flow.state
    status = _map_status(session)
    stage_label = _STAGE_LABELS.get(state.stage, "discovery")

    questions: list[QuestionSchema] = []
    if state.stage == FlowStage.AWAITING_CLARIFICATION and state.discovery_result is not None:
        questions = _build_questions(state.discovery_result.clarification_questions)
        with session.lock:
            session.pending_questions = {q.id: q.question for q in questions}

    active_operation = _ACTIVE_OPERATION_MESSAGES.get(state.stage)
    if session.error is not None:
        active_operation = session.error

    return ConsultationResponse(
        consultation_id=session.consultation_id,
        status=status,
        stage=stage_label,
        clarification_round=(
            state.clarification_context.clarification_round
            if state.clarification_context is not None
            else 0
        ),
        questions=questions,
        active_operation=active_operation,
    )


def _blueprint_to_schema(blueprint: ProductBlueprint) -> BlueprintSchema:
    return BlueprintSchema(
        title=blueprint.title,
        executive_summary=blueprint.executive_summary,
        sections=[
            BlueprintSectionSchema(
                section=section.section,
                title=section.title,
                summary=section.summary,
                markdown=section.markdown,
            )
            for section in blueprint.sections
        ],
        open_questions=blueprint.open_questions,
        limitations=blueprint.limitations,
        generated_markdown=blueprint.generated_markdown,
        version=blueprint.version,
    )
