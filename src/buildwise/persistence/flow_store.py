"""CrewAI FlowPersistence adapter for the BuildWise MVP schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from crewai.flow.persistence.base import FlowPersistence
from pydantic import BaseModel, Field, PrivateAttr
from pydantic_core import to_jsonable_python
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from buildwise.persistence.models import Base
from buildwise.persistence.repositories import (
    ArtifactRepository,
    ClarificationRoundRepository,
    ConsultationRepository,
    RevisionRepository,
    UsageRepository,
)

_ARTIFACT_FIELDS = {
    "discovery_result": "discovery",
    "product_planning_result": "product_planning",
    "specialist_execution_plan": "specialist_plan",
    "technical_planning_result": "technical_planning",
    "lead_review": "lead_review",
    "product_blueprint": "blueprint",
}


class BuildWiseFlowStore(FlowPersistence):
    """Persist CrewAI Flow checkpoints into the BuildWise consultation tables."""

    persistence_type: str = Field(default="BuildWiseFlowStore")
    _engine: Engine = PrivateAttr()
    _session_factory: sessionmaker[Session] = PrivateAttr()

    def __init__(self, engine: Engine, /, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._engine = engine
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        self.init_db()

    def init_db(self) -> None:
        Base.metadata.create_all(self._engine)

    def save_state(
        self,
        flow_uuid: str,
        method_name: str,
        state_data: dict[str, Any] | BaseModel,
    ) -> None:
        del method_name
        state = self._state_dict(state_data)
        consultation_id = str(state.get("session_id") or flow_uuid)
        intake = self._mapping(state.get("intake_request"))
        title = str(intake.get("title") or "Untitled consultation")
        status = str(state.get("status", "created"))
        stage = str(state.get("stage", "intake"))
        completed_at = self._datetime(state.get("completed_at"))
        stored_state = {**state, "_flow_uuid": flow_uuid}

        with self._session_factory.begin() as session:
            ConsultationRepository(session).save_state(
                consultation_id=consultation_id,
                title=title,
                status=status,
                stage=stage,
                initial_idea=intake,
                flow_state=stored_state,
                completed_at=completed_at,
            )
            self._save_artifacts(session, consultation_id, state)
            self._save_clarification(session, consultation_id, state)
            self._save_revisions(session, consultation_id, state)
            UsageRepository(session).save(
                consultation_id=consultation_id,
                usage=self._mapping(state.get("usage")),
            )

    def load_state(self, flow_uuid: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            record = ConsultationRepository(session).find_by_flow_uuid(flow_uuid)
            if record is None:
                return None
            return self._public_state(record.flow_state_json)

    def load_consultation_state(self, consultation_id: str) -> dict[str, Any] | None:
        """Load Flow state by the public consultation identifier."""

        with self._session_factory() as session:
            record = ConsultationRepository(session).get(consultation_id)
            if record is None:
                return None
            return self._public_state(record.flow_state_json)

    def save_consultation_state(
        self,
        consultation_id: str,
        *,
        method_name: str,
        state_data: dict[str, Any] | BaseModel,
    ) -> None:
        """Checkpoint an API mutation using the consultation's current Flow UUID."""

        with self._session_factory() as session:
            record = ConsultationRepository(session).get(consultation_id)
            if record is None:
                raise LookupError(f"Consultation '{consultation_id}' was not found.")
            flow_uuid = str(record.flow_state_json.get("_flow_uuid") or consultation_id)
        self.save_state(flow_uuid, method_name, state_data)

    @staticmethod
    def _public_state(state_data: dict[str, Any]) -> dict[str, Any]:
        state = dict(state_data)
        state.pop("_flow_uuid", None)
        return state

    @staticmethod
    def _state_dict(state_data: dict[str, Any] | BaseModel) -> dict[str, Any]:
        if isinstance(state_data, BaseModel):
            return state_data.model_dump(mode="json")
        if isinstance(state_data, dict):
            result = to_jsonable_python(state_data)
            if isinstance(result, dict):
                return result
        raise TypeError("state_data must be a Pydantic model or dictionary.")

    @staticmethod
    def _mapping(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _datetime(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return None

    def _save_artifacts(
        self,
        session: Session,
        consultation_id: str,
        state: dict[str, Any],
    ) -> None:
        repository = ArtifactRepository(session)
        for field_name, artifact_type in _ARTIFACT_FIELDS.items():
            artifact = state.get(field_name)
            if isinstance(artifact, dict):
                repository.save_version(
                    consultation_id=consultation_id,
                    artifact_type=artifact_type,
                    artifact=artifact,
                )

    def _save_clarification(
        self,
        session: Session,
        consultation_id: str,
        state: dict[str, Any],
    ) -> None:
        questions = state.get("clarification_question_set")
        round_number = int(state.get("clarification_round", 0))
        if not isinstance(questions, dict) or round_number < 1:
            return
        answers_value = state.get("clarification_answers")
        all_answers = (
            [dict(answer) for answer in answers_value if isinstance(answer, dict)]
            if isinstance(answers_value, list)
            else []
        )
        question_values = questions.get("questions")
        active_question_ids = (
            {
                str(question.get("id"))
                for question in question_values
                if isinstance(question, dict) and question.get("id") is not None
            }
            if isinstance(question_values, list)
            else set()
        )
        answers = [
            answer
            for answer in all_answers
            if str(answer.get("question_id")) in active_question_ids
        ]
        ClarificationRoundRepository(session).save(
            consultation_id=consultation_id,
            round_number=round_number,
            questions=questions,
            answers=answers,
            status="answered" if answers else "pending",
            answered_at=self._datetime(answers[-1].get("answered_at")) if answers else None,
        )

    def _save_revisions(
        self,
        session: Session,
        consultation_id: str,
        state: dict[str, Any],
    ) -> None:
        revisions = state.get("revision_history")
        if not isinstance(revisions, list):
            return
        repository = RevisionRepository(session)
        round_number = max(1, int(state.get("revision_count", 0)))
        for revision in revisions:
            if not isinstance(revision, dict):
                continue
            changes = revision.get("requested_changes", [])
            repository.save(
                consultation_id=consultation_id,
                revision_target=str(revision.get("target", "unknown")),
                reason=str(revision.get("reason", "Revision requested.")),
                requested_changes=(
                    [str(change) for change in changes if isinstance(change, str)]
                    if isinstance(changes, list)
                    else []
                ),
                round_number=round_number,
                status="requested",
            )
