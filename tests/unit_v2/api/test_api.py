"""End-to-end API tests against a mocked ``crewai.Crew.kickoff``.

Exercises the real FastAPI routes, the real background-thread execution,
and the real ``ConsultingFlow`` graph — without any live LLM call.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from uuid import UUID

import pytest
from crewai import Crew
from crewai.crews.crew_output import CrewOutput
from crewai.tasks.task_output import TaskOutput
from fastapi.testclient import TestClient

from buildwisev2.api import service as service_module
from buildwisev2.api.app import app
from buildwisev2.api.store import ConsultationStore
from buildwisev2.config.settings import Settings
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
from buildwisev2.domain.requirements import RequirementsDecision, RequirementsSpecification
from buildwisev2.domain.review import LeadReview, ReviewDecision

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


def _task_output(name: str, pydantic_output: object) -> TaskOutput:
    return TaskOutput(description="test", agent="test-agent", name=name, pydantic=pydantic_output)


def _crew_output(*, pydantic_output=None, tasks_output=None) -> CrewOutput:
    return CrewOutput(pydantic=pydantic_output, tasks_output=tasks_output or [])


def _happy_path_kickoff(self: Crew, inputs: dict[str, str] | None = None) -> CrewOutput:
    names = [t.name for t in self.tasks]
    assert inputs is not None

    if names == ["product_discovery"]:
        session_id = json.loads(inputs["product_idea"])["session_id"]
        discovery = DiscoveryResult(
            session_id=session_id,
            interpreted_idea="A scheduling tool.",
            capability_classification=CapabilityClassification(),
            completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
            decision=DiscoveryDecision.CONTINUE,
            confidence=0.9,
        )
        return _crew_output(pydantic_output=discovery)

    if "product_definition" in names:
        session_id = json.loads(inputs["discovery_result"])["session_id"]
        product_definition = ProductDefinition(
            session_id=session_id,
            vision="v",
            value_proposition="vp",
            goals=["g"],
            personas=[],
            features=[],
            mvp_feature_ids=[],
            decision=ProductDefinitionDecision.APPROVED,
        )
        requirements = RequirementsSpecification(
            session_id=session_id,
            functional_requirements=[],
            non_functional_requirements=[],
            decision=RequirementsDecision.APPROVED,
        )
        return _crew_output(
            tasks_output=[
                _task_output("product_definition", product_definition),
                _task_output("requirements", requirements),
            ]
        )

    if names == ["solution_architecture"]:
        session_id = json.loads(inputs["requirements"])["session_id"]
        solution = SolutionArchitecture(
            session_id=session_id,
            system_context="c",
            components=[],
            deployment=DeploymentView(description="d"),
            scalability_strategy="s",
            reliability_strategy="r",
            observability_strategy="o",
            decision=SolutionArchitectureDecision.APPROVED,
        )
        return _crew_output(tasks_output=[_task_output("solution_architecture", solution)])

    if names == ["lead_review"]:
        session_id = json.loads(inputs["requirements"])["session_id"]
        review = LeadReview(
            session_id=session_id,
            implementation_readiness_score=0.9,
            decision=ReviewDecision.APPROVED,
            approved_for_blueprint=True,
        )
        return _crew_output(
            pydantic_output=review,
            tasks_output=[_task_output("lead_review", review)],
        )

    raise AssertionError(f"Unexpected crew task composition: {names}")


def _clarify_then_approve_kickoff_factory():
    """First Discovery pass asks a clarification question; second approves."""

    state = {"discovery_calls": 0}

    def _kickoff(self: Crew, inputs: dict[str, str] | None = None) -> CrewOutput:
        names = [t.name for t in self.tasks]
        assert inputs is not None
        if names == ["product_discovery"]:
            state["discovery_calls"] += 1
            session_id = json.loads(inputs["product_idea"])["session_id"]
            if state["discovery_calls"] == 1:
                discovery = DiscoveryResult(
                    session_id=session_id,
                    interpreted_idea="A tool.",
                    capability_classification=CapabilityClassification(),
                    completeness=CompletenessAssessment(can_continue=False, completeness_score=0.4),
                    decision=DiscoveryDecision.CLARIFICATION_REQUIRED,
                    clarification_questions=["Who is the target user?"],
                    confidence=0.4,
                )
            else:
                discovery = DiscoveryResult(
                    session_id=session_id,
                    interpreted_idea="A tool for field technicians.",
                    capability_classification=CapabilityClassification(),
                    completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
                    decision=DiscoveryDecision.CONTINUE,
                    confidence=0.9,
                )
            return _crew_output(pydantic_output=discovery)
        return _happy_path_kickoff(self, inputs)

    return _kickoff


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    settings = Settings(flow_persistence_db_path=str(tmp_path / "flows.db"))
    store = ConsultationStore(settings=settings)
    monkeypatch.setattr(service_module, "STORE", store)
    return TestClient(app)


def _wait_for_terminal_status(
    client: TestClient, consultation_id: str, timeout: float = 5.0
) -> dict:
    deadline = time.monotonic() + timeout
    body: dict = {}
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/consultations/{consultation_id}")
        body = response.json()
        if body["status"] in {
            "completed",
            "completed_with_limitations",
            "failed",
            "awaiting_user_input",
        }:
            return body
        time.sleep(0.05)
    raise AssertionError(f"Consultation did not reach a terminal status in time: {body}")


def test_full_happy_path_via_http(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(Crew, "kickoff", _happy_path_kickoff)

    create_response = client.post(
        "/api/v1/consultations",
        json={"idea": "An internal scheduling tool for field technicians."},
    )
    assert create_response.status_code == 200
    body = create_response.json()
    consultation_id = body["consultation_id"]
    UUID(consultation_id)  # consultation_id must be a valid UUID string

    final = _wait_for_terminal_status(client, consultation_id)
    assert final["status"] == "completed"
    assert final["stage"] == "completed"

    result_response = client.get(f"/api/v1/consultations/{consultation_id}/result")
    assert result_response.status_code == 200
    result = result_response.json()["result"]
    assert result["sections"]
    assert result["generated_markdown"].startswith("#")


def test_clarification_round_trip_via_http(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    monkeypatch.setattr(Crew, "kickoff", _clarify_then_approve_kickoff_factory())

    create_response = client.post(
        "/api/v1/consultations",
        json={"idea": "A tool that helps with something important for a business."},
    )
    consultation_id = create_response.json()["consultation_id"]

    awaiting = _wait_for_terminal_status(client, consultation_id)
    assert awaiting["status"] == "awaiting_user_input"
    assert len(awaiting["questions"]) == 1
    question_id = awaiting["questions"][0]["id"]

    answer_response = client.post(
        f"/api/v1/consultations/{consultation_id}/clarifications",
        json={
            "clarification_round": awaiting["clarification_round"],
            "answers": [{"question_id": question_id, "answer": "Field technicians."}],
        },
    )
    assert answer_response.status_code == 200

    final = _wait_for_terminal_status(client, consultation_id)
    assert final["status"] == "completed"


def test_unknown_consultation_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/consultations/does-not-exist")
    assert response.status_code == 404


def test_result_before_completion_returns_404(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    def _hang_forever(self: Crew, inputs: dict[str, str] | None = None) -> CrewOutput:
        session_id = json.loads(inputs["product_idea"])["session_id"] if inputs else None
        return _crew_output(
            pydantic_output=DiscoveryResult(
                session_id=session_id,
                interpreted_idea="x",
                capability_classification=CapabilityClassification(),
                completeness=CompletenessAssessment(can_continue=False, completeness_score=0.1),
                decision=DiscoveryDecision.CLARIFICATION_REQUIRED,
                clarification_questions=["q"],
                confidence=0.1,
            )
        )

    monkeypatch.setattr(Crew, "kickoff", _hang_forever)

    create_response = client.post(
        "/api/v1/consultations",
        json={"idea": "An idea that needs more detail before it can proceed."},
    )
    consultation_id = create_response.json()["consultation_id"]
    _wait_for_terminal_status(client, consultation_id)

    result_response = client.get(f"/api/v1/consultations/{consultation_id}/result")
    assert result_response.status_code == 404


def test_intake_rejects_too_short_idea(client: TestClient) -> None:
    response = client.post("/api/v1/consultations", json={"idea": "too short"})
    assert response.status_code == 422
