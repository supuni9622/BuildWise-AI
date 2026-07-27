"""Minimal SQLAlchemy schema for BuildWise consulting sessions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from buildwise.domain.common import utc_now


class Base(DeclarativeBase):
    """Base class for the BuildWise MVP persistence schema."""


class ConsultationRecord(Base):
    __tablename__ = "consultations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), index=True)
    stage: Mapped[str] = mapped_column(String(50), index=True)
    initial_idea_json: Mapped[dict[str, object]] = mapped_column(JSON)
    flow_state_json: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ArtifactRecord(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            "artifact_type",
            "version",
            name="uq_artifact_consultation_type_version",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    consultation_id: Mapped[str] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50), index=True)
    artifact_json: Mapped[dict[str, object]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ClarificationRoundRecord(Base):
    __tablename__ = "clarification_rounds"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            "round_number",
            name="uq_clarification_consultation_round",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    consultation_id: Mapped[str] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), index=True
    )
    round_number: Mapped[int] = mapped_column(Integer)
    questions_json: Mapped[dict[str, object]] = mapped_column(JSON)
    answers_json: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RevisionRecord(Base):
    __tablename__ = "revisions"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            "revision_target",
            "reason",
            "round_number",
            name="uq_revision_consultation_target_reason_round",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    consultation_id: Mapped[str] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), index=True
    )
    revision_target: Mapped[str] = mapped_column(String(50), index=True)
    reason: Mapped[str] = mapped_column(Text)
    requested_changes_json: Mapped[list[str]] = mapped_column(JSON)
    round_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UsageRecord(Base):
    __tablename__ = "usage"

    consultation_id: Mapped[str] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), primary_key=True
    )
    usage_json: Mapped[dict[str, object]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class BlueprintReportMetadataRecord(Base):
    __tablename__ = "blueprint_reports"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            "blueprint_version",
            name="uq_blueprint_report_consultation_version",
        ),
    )

    consultation_id: Mapped[str] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), primary_key=True
    )
    blueprint_version: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    s3_key: Mapped[str] = mapped_column(String(1024))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    lead_review_id: Mapped[str] = mapped_column(String(36), index=True)
