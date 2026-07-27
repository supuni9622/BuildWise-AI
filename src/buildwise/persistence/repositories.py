"""Repository operations for the minimal BuildWise persistence schema."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from buildwise.domain.common import utc_now
from buildwise.persistence.models import (
    ArtifactRecord,
    BlueprintReportMetadataRecord,
    ClarificationRoundRecord,
    ConsultationRecord,
    RevisionRecord,
    UsageRecord,
)

JsonObject = dict[str, Any]


class ConsultationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, consultation_id: str) -> ConsultationRecord | None:
        return self._session.get(ConsultationRecord, consultation_id)

    def find_by_flow_uuid(self, flow_uuid: str) -> ConsultationRecord | None:
        """Find a consultation by CrewAI's state ID stored inside its JSON."""

        direct = self.get(flow_uuid)
        if direct is not None:
            return direct
        records = self._session.scalars(select(ConsultationRecord)).all()
        return next(
            (
                record
                for record in records
                if str(record.flow_state_json.get("_flow_uuid", "")) == flow_uuid
            ),
            None,
        )

    def save_state(
        self,
        *,
        consultation_id: str,
        title: str,
        status: str,
        stage: str,
        initial_idea: Mapping[str, Any],
        flow_state: Mapping[str, Any],
        completed_at: datetime | None,
    ) -> ConsultationRecord:
        record = self.get(consultation_id)
        now = utc_now()
        if record is None:
            record = ConsultationRecord(
                id=consultation_id,
                title=title,
                status=status,
                stage=stage,
                initial_idea_json=dict(initial_idea),
                flow_state_json=dict(flow_state),
                created_at=now,
                updated_at=now,
                completed_at=completed_at,
            )
            self._session.add(record)
        else:
            record.title = title
            record.status = status
            record.stage = stage
            record.initial_idea_json = dict(initial_idea)
            record.flow_state_json = dict(flow_state)
            record.updated_at = now
            record.completed_at = completed_at
        self._session.flush()
        return record


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def latest(self, consultation_id: str, artifact_type: str) -> ArtifactRecord | None:
        statement = (
            select(ArtifactRecord)
            .where(
                ArtifactRecord.consultation_id == consultation_id,
                ArtifactRecord.artifact_type == artifact_type,
            )
            .order_by(desc(ArtifactRecord.version))
            .limit(1)
        )
        return self._session.scalar(statement)

    def save_version(
        self,
        *,
        consultation_id: str,
        artifact_type: str,
        artifact: Mapping[str, Any],
    ) -> ArtifactRecord:
        latest = self.latest(consultation_id, artifact_type)
        artifact_json = dict(artifact)
        if latest is not None and latest.artifact_json == artifact_json:
            return latest
        record = ArtifactRecord(
            id=str(uuid4()),
            consultation_id=consultation_id,
            artifact_type=artifact_type,
            artifact_json=artifact_json,
            version=1 if latest is None else latest.version + 1,
        )
        self._session.add(record)
        self._session.flush()
        return record


class ClarificationRoundRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        *,
        consultation_id: str,
        round_number: int,
        questions: Mapping[str, Any],
        answers: list[JsonObject],
        status: str,
        answered_at: datetime | None,
    ) -> ClarificationRoundRecord:
        statement = select(ClarificationRoundRecord).where(
            ClarificationRoundRecord.consultation_id == consultation_id,
            ClarificationRoundRecord.round_number == round_number,
        )
        record = self._session.scalar(statement)
        if record is None:
            record = ClarificationRoundRecord(
                id=str(uuid4()),
                consultation_id=consultation_id,
                round_number=round_number,
                questions_json=dict(questions),
                answers_json=answers,
                status=status,
                answered_at=answered_at,
            )
            self._session.add(record)
        else:
            record.questions_json = dict(questions)
            record.answers_json = answers
            record.status = status
            record.answered_at = answered_at
        self._session.flush()
        return record


class RevisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        *,
        consultation_id: str,
        revision_target: str,
        reason: str,
        requested_changes: list[str],
        round_number: int,
        status: str,
    ) -> RevisionRecord:
        statement = select(RevisionRecord).where(
            RevisionRecord.consultation_id == consultation_id,
            RevisionRecord.revision_target == revision_target,
            RevisionRecord.reason == reason,
        )
        record = self._session.scalar(statement)
        if record is None:
            record = RevisionRecord(
                id=str(uuid4()),
                consultation_id=consultation_id,
                revision_target=revision_target,
                reason=reason,
                requested_changes_json=requested_changes,
                round_number=round_number,
                status=status,
            )
            self._session.add(record)
        else:
            record.requested_changes_json = requested_changes
            record.status = status
        self._session.flush()
        return record


class UsageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, *, consultation_id: str, usage: Mapping[str, Any]) -> UsageRecord:
        record = self._session.get(UsageRecord, consultation_id)
        if record is None:
            record = UsageRecord(
                consultation_id=consultation_id,
                usage_json=dict(usage),
            )
            self._session.add(record)
        else:
            record.usage_json = dict(usage)
            record.updated_at = utc_now()
        self._session.flush()
        return record


class BlueprintReportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        *,
        consultation_id: str,
        blueprint_version: int,
        s3_key: str,
        generated_at: datetime,
        lead_review_id: str,
    ) -> BlueprintReportMetadataRecord:
        identity = (consultation_id, blueprint_version)
        record = self._session.get(BlueprintReportMetadataRecord, identity)
        if record is None:
            record = BlueprintReportMetadataRecord(
                consultation_id=consultation_id,
                blueprint_version=blueprint_version,
                s3_key=s3_key,
                generated_at=generated_at,
                lead_review_id=lead_review_id,
            )
            self._session.add(record)
        else:
            record.s3_key = s3_key
            record.generated_at = generated_at
            record.lead_review_id = lead_review_id
        self._session.flush()
        return record
