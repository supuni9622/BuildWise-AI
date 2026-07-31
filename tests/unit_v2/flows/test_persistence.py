"""Unit tests for ConsultingFlow's SQLite checkpointing. No live LLM calls."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from crewai import Crew
from crewai.crews.crew_output import CrewOutput
from crewai.flow.persistence import SQLiteFlowPersistence
from crewai.tasks.task_output import TaskOutput

from buildwisev2.domain.common import FlowRuntimeLimits
from buildwisev2.domain.discovery import (
    CapabilityClassification,
    CompletenessAssessment,
    DiscoveryDecision,
    DiscoveryResult,
)
from buildwisev2.domain.intake import ProductIdeaRequest
from buildwisev2.flows.consulting_flow import ConsultingFlow
from buildwisev2.flows.state import ConsultingFlowState, FlowStage

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


def _task_output(name: str, pydantic_output: object) -> TaskOutput:
    return TaskOutput(description="test", agent="test-agent", name=name, pydantic=pydantic_output)


def _crew_output(*, pydantic_output: object | None = None) -> CrewOutput:
    return CrewOutput(pydantic=pydantic_output, tasks_output=[])


def test_checkpoint_is_a_noop_without_persistence() -> None:
    flow = ConsultingFlow()
    # Must not raise even though there is no persistence backend configured.
    flow._checkpoint("test_method")  # exercising the private helper directly


def test_run_discovery_checkpoints_state_to_sqlite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session_id = uuid4()
    db_path = tmp_path / "flows.db"
    persistence = SQLiteFlowPersistence(str(db_path))

    def fake_kickoff(self: Crew, inputs: dict[str, str] | None = None) -> CrewOutput:
        discovery = DiscoveryResult(
            session_id=session_id,
            interpreted_idea="An idea.",
            capability_classification=CapabilityClassification(),
            completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
            decision=DiscoveryDecision.CLARIFICATION_REQUIRED,
            clarification_questions=["What platform?"],
            confidence=0.5,
        )
        return _crew_output(pydantic_output=discovery)

    monkeypatch.setattr(Crew, "kickoff", fake_kickoff)

    flow = ConsultingFlow(persistence=persistence)
    flow.state.product_idea = ProductIdeaRequest(session_id=session_id, raw_idea="An idea.")
    flow.state.limits = FlowRuntimeLimits()
    flow.kickoff()

    assert flow.state.stage == FlowStage.AWAITING_CLARIFICATION

    stored = persistence.load_state(flow.state.id)
    assert stored is not None
    restored = ConsultingFlowState.model_validate(stored)
    assert restored.discovery_result is not None
    assert restored.discovery_result.clarification_questions == ["What platform?"]
    assert restored.stage == FlowStage.AWAITING_CLARIFICATION
