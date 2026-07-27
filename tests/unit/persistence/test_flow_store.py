"""Tests for the minimal BuildWise persistence schema and Flow store."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from buildwise.persistence.flow_store import BuildWiseFlowStore
from buildwise.persistence.models import (
    ArtifactRecord,
    ClarificationRoundRecord,
    ConsultationRecord,
    RevisionRecord,
    UsageRecord,
)


def _state(consultation_id: str) -> dict[str, object]:
    return {
        "session_id": consultation_id,
        "status": "awaiting_user_input",
        "stage": "clarification",
        "intake_request": {
            "title": "Scheduling assistant",
            "idea": "A scheduling assistant for distributed product teams.",
        },
        "discovery_result": {
            "id": str(uuid4()),
            "session_id": consultation_id,
            "summary": "Discovery artifact.",
        },
        "product_planning_result": None,
        "specialist_execution_plan": None,
        "technical_planning_result": None,
        "lead_review": None,
        "product_blueprint": None,
        "clarification_round": 1,
        "clarification_question_set": {
            "id": str(uuid4()),
            "session_id": consultation_id,
            "round_number": 1,
            "questions": [{"id": str(uuid4()), "question": "Who is the first user?"}],
        },
        "clarification_answers": [],
        "revision_count": 1,
        "revision_history": [
            {
                "target": "requirements",
                "reason": "Clarify acceptance criteria.",
                "requested_changes": ["Add measurable acceptance criteria."],
            }
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "records": [],
        },
        "completed_at": None,
    }


def test_flow_store_creates_exact_mvp_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "buildwise.db"
    engine = create_engine(f"sqlite:///{database_path}")

    BuildWiseFlowStore(engine)

    assert set(inspect(engine).get_table_names()) == {
        "artifacts",
        "clarification_rounds",
        "consultations",
        "revisions",
        "usage",
    }


def test_flow_store_saves_and_loads_consultation_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "buildwise.db"
    engine = create_engine(f"sqlite:///{database_path}")
    store = BuildWiseFlowStore(engine)
    consultation_id = str(uuid4())
    state = _state(consultation_id)

    store.save_state("crew-flow-123", "pause_for_clarification", state)
    loaded = store.load_state("crew-flow-123")

    assert loaded is not None
    assert loaded["session_id"] == consultation_id
    assert "_flow_uuid" not in loaded

    with Session(engine) as session:
        consultation = session.get(ConsultationRecord, consultation_id)
        assert consultation is not None
        assert consultation.title == "Scheduling assistant"
        assert consultation.status == "awaiting_user_input"

        artifact = session.scalar(select(ArtifactRecord))
        assert artifact is not None
        assert artifact.artifact_type == "discovery"
        assert artifact.version == 1

        clarification = session.scalar(select(ClarificationRoundRecord))
        assert clarification is not None
        assert clarification.status == "pending"

        revision = session.scalar(select(RevisionRecord))
        assert revision is not None
        assert revision.revision_target == "requirements"

        usage = session.get(UsageRecord, consultation_id)
        assert usage is not None
        assert usage.usage_json["total_tokens"] == 150


def test_artifacts_version_only_when_payload_changes(tmp_path: Path) -> None:
    database_path = tmp_path / "buildwise.db"
    engine = create_engine(f"sqlite:///{database_path}")
    store = BuildWiseFlowStore(engine)
    consultation_id = str(uuid4())
    state = _state(consultation_id)

    store.save_state("flow-versioning", "discovery", state)
    store.save_state("flow-versioning", "routing", state)
    discovery = state["discovery_result"]
    assert isinstance(discovery, dict)
    discovery["summary"] = "Updated discovery artifact."
    store.save_state("flow-versioning", "discovery_revision", state)

    with Session(engine) as session:
        count = session.scalar(
            select(func.count())
            .select_from(ArtifactRecord)
            .where(ArtifactRecord.artifact_type == "discovery")
        )
        versions = session.scalars(
            select(ArtifactRecord.version).order_by(ArtifactRecord.version)
        ).all()

    assert count == 2
    assert versions == [1, 2]


def test_clarification_answers_and_usage_are_upserted(tmp_path: Path) -> None:
    database_path = tmp_path / "buildwise.db"
    engine = create_engine(f"sqlite:///{database_path}")
    store = BuildWiseFlowStore(engine)
    consultation_id = str(uuid4())
    state = _state(consultation_id)
    store.save_state("flow-upsert", "pause", state)

    state["clarification_answers"] = [
        {
            "question_id": str(uuid4()),
            "answer": "Product managers.",
            "answered_at": "2026-07-27T12:00:00+00:00",
        }
    ]
    usage = state["usage"]
    assert isinstance(usage, dict)
    usage["total_tokens"] = 300
    store.save_state("flow-upsert", "resume", state)

    with Session(engine) as session:
        clarification = session.scalar(select(ClarificationRoundRecord))
        usage_record = session.get(UsageRecord, consultation_id)
        clarification_count = session.scalar(
            select(func.count()).select_from(ClarificationRoundRecord)
        )

    assert clarification is not None
    assert clarification.status == "answered"
    assert clarification.answered_at is not None
    assert clarification_count == 1
    assert usage_record is not None
    assert usage_record.usage_json["total_tokens"] == 300
