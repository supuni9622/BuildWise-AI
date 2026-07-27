"""HTTP coverage for durable consultation clarification and resume."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from buildwise.api.v1.consultation_service import ConsultationService
from buildwise.api.v1.consultations import get_consultation_service
from buildwise.domain.api import (
    StartConsultationRequest,
    SubmitClarificationsRequest,
)
from buildwise.domain.blueprint import ProductBlueprint, UsageSummary
from buildwise.domain.common import generate_uuid
from buildwise.domain.discovery import ClarificationQuestion, ClarificationQuestionSet
from buildwise.domain.enums import SessionStatus
from buildwise.domain.intake import ClarificationAnswer
from buildwise.flows.consulting_flow import BuildWiseConsultingFlow
from buildwise.flows.state import BuildWiseFlowState
from buildwise.main import create_app
from buildwise.persistence.flow_store import BuildWiseFlowStore
from buildwise.persistence.models import ClarificationRoundRecord


class _FakeConsultingFlow:
    """Deterministic Flow double that pauses once and then completes."""

    def __init__(self, state: BuildWiseFlowState, persistence: BuildWiseFlowStore) -> None:
        self.state = state
        self._persistence = persistence

    def kickoff(self) -> BuildWiseFlowState | ProductBlueprint:
        if self.state.status is SessionStatus.CREATED:
            self.state.start_flow()
            question = ClarificationQuestion(
                key="target_customer",
                category="target_users",
                question="Which small shops should the first release serve?",
                rationale="The initial segment determines the product scope.",
                related_unknown_ids=[generate_uuid()],
                affected_areas=["product"],
            )
            self.state.request_clarification(
                question_set=ClarificationQuestionSet(
                    session_id=self.state.session_id,
                    round_number=1,
                    questions=[question],
                    summary="The initial customer segment needs clarification.",
                    blocking=True,
                )
            )
            result: BuildWiseFlowState | ProductBlueprint = self.state
        elif self.state.status is SessionStatus.RESUMING:
            blueprint = ProductBlueprint(
                title="Small-shop AI platform",
                executive_summary="A build-ready plan for the selected shop segment.",
                usage_summary=UsageSummary(),
                generated_markdown="# Small-shop AI platform",
            )
            self.state.product_blueprint = blueprint
            self.state.mark_completed(
                blueprint_artifact_id=generate_uuid(),
                review_artifact_id=generate_uuid(),
            )
            result = blueprint
        else:
            raise ValueError("Unexpected fake Flow state.")

        self._persistence.save_state("fake-flow-uuid", "kickoff", self.state)
        return result

    def submit_clarification_answers(self, answers: list[Any]) -> None:
        self.state.receive_clarification_answers(answers=answers)


def _service(tmp_path: Path) -> tuple[ConsultationService, Engine]:
    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}")
    store = BuildWiseFlowStore(engine)

    def flow_factory(
        state: BuildWiseFlowState,
        persistence: Any,
    ) -> BuildWiseConsultingFlow:
        assert isinstance(persistence, BuildWiseFlowStore)
        return cast(BuildWiseConsultingFlow, _FakeConsultingFlow(state, persistence))

    service = ConsultationService(
        flow_store=store,
        flow_factory=flow_factory,
    )
    return service, engine


def test_consultation_http_lifecycle(tmp_path: Path) -> None:
    service, engine = _service(tmp_path)
    app = create_app()
    app.dependency_overrides[get_consultation_service] = lambda: service

    with TestClient(app) as client:
        started = client.post(
            "/api/v1/consultations",
            json={"idea": "I want to build an AI platform that helps small shops."},
        )

        assert started.status_code == 202
        start_payload = started.json()
        consultation_id = start_payload["consultation_id"]
        assert start_payload["status"] == "created"
        assert start_payload["active_operation"] == "Queued for discovery"

        status_response = client.get(f"/api/v1/consultations/{consultation_id}")
        assert status_response.status_code == 200
        status_payload = status_response.json()
        question_id = status_payload["questions"][0]["id"]
        assert status_payload["status"] == "awaiting_user_input"
        assert status_payload["clarification_round"] == 1

        pending_result = client.get(f"/api/v1/consultations/{consultation_id}/result")
        assert pending_result.status_code == 409

        wrong_round = client.post(
            f"/api/v1/consultations/{consultation_id}/clarifications",
            json={
                "clarification_round": 2,
                "answers": [{"question_id": question_id, "answer": "Independent grocers."}],
            },
        )
        assert wrong_round.status_code == 409

        resumed = client.post(
            f"/api/v1/consultations/{consultation_id}/clarifications",
            json={
                "clarification_round": 1,
                "answers": [{"question_id": question_id, "answer": "Independent grocers."}],
            },
        )
        assert resumed.status_code == 202
        assert resumed.json()["status"] == "resuming"
        assert resumed.json()["questions"] == []

        completed = client.get(f"/api/v1/consultations/{consultation_id}")
        assert completed.json()["status"] == "completed"
        result = client.get(f"/api/v1/consultations/{consultation_id}/result")
        assert result.status_code == 200
        assert result.json()["result"]["title"] == "Small-shop AI platform"

    with Session(engine) as session:
        clarification = session.query(ClarificationRoundRecord).one()
        assert clarification.status == "answered"
        assert clarification.answers_json[0]["question_id"] == question_id


def test_consultation_endpoints_return_not_found(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    app = create_app()
    app.dependency_overrides[get_consultation_service] = lambda: service

    with TestClient(app) as client:
        status_response = client.get("/api/v1/consultations/missing")
        result_response = client.get("/api/v1/consultations/missing/result")
        answers_response = client.post(
            "/api/v1/consultations/missing/clarifications",
            json={
                "clarification_round": 1,
                "answers": [{"question_id": str(generate_uuid()), "answer": "Retail shops."}],
            },
        )

    assert status_response.status_code == 404
    assert result_response.status_code == 404
    assert answers_response.status_code == 404


def test_service_rejects_answers_outside_active_question_set(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    started = service.enqueue_start(
        StartConsultationRequest(
            idea="I want to build an AI platform that helps small shops."
        )
    )
    service.run(started.consultation_id)

    request = SubmitClarificationsRequest(
        clarification_round=1,
        answers=[
            ClarificationAnswer(
                question_id=generate_uuid(),
                answer="Independent grocers.",
            )
        ],
    )

    with pytest.raises(ValueError, match="outside the active set"):
        service.enqueue_clarifications(started.consultation_id, request)
