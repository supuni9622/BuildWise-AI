"""S3 and local-filesystem storage for generated blueprint reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from buildwise.config.settings import Settings
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.common import ArtifactId, SessionId
from buildwise.domain.reporting import BlueprintReportRecord

BLUEPRINT_VERSION = 1


class BlueprintReportStorage(Protocol):
    """Boundary used by the Flow after deterministic blueprint generation."""

    def store(
        self,
        *,
        consultation_id: SessionId,
        blueprint: ProductBlueprint,
        lead_review_id: ArtifactId,
    ) -> BlueprintReportRecord:
        """Persist a version-1 report and return its storage metadata."""


class FilesystemBlueprintReportStorage:
    """Store blueprint reports below ``data/reports`` for local development."""

    def __init__(self, root: Path, *, store_json: bool = False) -> None:
        self._root = root
        self._store_json = store_json

    def store(
        self,
        *,
        consultation_id: SessionId,
        blueprint: ProductBlueprint,
        lead_review_id: ArtifactId,
    ) -> BlueprintReportRecord:
        consultation = _safe_consultation_id(consultation_id)
        report_directory = self._root / consultation
        report_directory.mkdir(parents=True, exist_ok=True)
        markdown_path = report_directory / "blueprint.md"
        markdown_path.write_text(blueprint.generated_markdown, encoding="utf-8")
        if self._store_json:
            (report_directory / "blueprint.json").write_text(
                blueprint.model_dump_json(indent=2),
                encoding="utf-8",
            )
        return BlueprintReportRecord(
            consultation_id=consultation_id,
            s3_key=markdown_path.as_posix(),
            lead_review_id=lead_review_id,
            storage_backend="filesystem",
        )


class S3BlueprintReportStorage:
    """Store immutable version-1 blueprint objects in an S3 bucket."""

    def __init__(
        self,
        bucket: str,
        *,
        store_json: bool = False,
        client: Any | None = None,
        region_name: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        if not bucket.strip():
            raise ValueError("S3 report storage requires a bucket name.")
        if client is None:
            import boto3  # type: ignore[import-untyped]

            client = boto3.client(
                "s3",
                region_name=region_name,
                endpoint_url=endpoint_url,
            )
        self._bucket = bucket
        self._store_json = store_json
        self._client = client

    def store(
        self,
        *,
        consultation_id: SessionId,
        blueprint: ProductBlueprint,
        lead_review_id: ArtifactId,
    ) -> BlueprintReportRecord:
        consultation = _safe_consultation_id(consultation_id)
        prefix = f"consultations/{consultation}/blueprints/v{BLUEPRINT_VERSION}"
        markdown_key = f"{prefix}/blueprint.md"
        self._client.put_object(
            Bucket=self._bucket,
            Key=markdown_key,
            Body=blueprint.generated_markdown.encode(),
            ContentType="text/markdown; charset=utf-8",
        )
        if self._store_json:
            self._client.put_object(
                Bucket=self._bucket,
                Key=f"{prefix}/blueprint.json",
                Body=blueprint.model_dump_json(indent=2).encode(),
                ContentType="application/json",
            )
        return BlueprintReportRecord(
            consultation_id=consultation_id,
            s3_key=markdown_key,
            lead_review_id=lead_review_id,
            storage_backend="s3",
        )


def create_blueprint_report_storage(settings: Settings) -> BlueprintReportStorage:
    """Create the configured report backend without requiring S3 locally."""

    if settings.report_storage_backend == "filesystem":
        return FilesystemBlueprintReportStorage(
            settings.report_storage_path,
            store_json=settings.store_blueprint_json,
        )
    if settings.s3_report_bucket is None:
        raise ValueError("S3_REPORT_BUCKET is required when report storage uses S3.")
    return S3BlueprintReportStorage(
        settings.s3_report_bucket,
        store_json=settings.store_blueprint_json,
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
    )


def _safe_consultation_id(consultation_id: SessionId) -> str:
    value = str(consultation_id)
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("consultation_id is not safe for report storage.")
    return value
