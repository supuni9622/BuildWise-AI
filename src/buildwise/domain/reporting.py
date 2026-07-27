"""Domain records for persisted blueprint reports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from buildwise.domain.common import ArtifactId, BuildWiseModel, SessionId, utc_now


class BlueprintReportRecord(BuildWiseModel):
    """Storage metadata for one immutable blueprint report version."""

    consultation_id: SessionId
    blueprint_version: int = Field(default=1, ge=1)
    s3_key: str = Field(min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    lead_review_id: ArtifactId
    storage_backend: Literal["filesystem", "s3"]
