from __future__ import annotations

from pathlib import Path
from typing import Any

from buildwise.domain.blueprint import ProductBlueprint, UsageSummary
from buildwise.domain.common import generate_uuid
from buildwise.reporting.storage import (
    FilesystemBlueprintReportStorage,
    S3BlueprintReportStorage,
)


def _blueprint() -> ProductBlueprint:
    return ProductBlueprint.model_construct(
        title="Stored blueprint",
        executive_summary="Ready to build.",
        sections=[],
        implementation_phases=[],
        assumptions=[],
        risks=[],
        recommendations=[],
        open_questions=[],
        limitations=[],
        usage_summary=UsageSummary(),
        generated_markdown="# Stored blueprint\n",
        version="1.0",
    )


class _S3Client:
    def __init__(self) -> None:
        self.objects: list[dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> None:
        self.objects.append(kwargs)


def test_filesystem_storage_writes_local_markdown_and_optional_json(tmp_path: Path) -> None:
    consultation_id = generate_uuid()
    review_id = generate_uuid()
    storage = FilesystemBlueprintReportStorage(tmp_path, store_json=True)

    record = storage.store(
        consultation_id=consultation_id,
        blueprint=_blueprint(),
        lead_review_id=review_id,
    )

    report_directory = tmp_path / str(consultation_id)
    assert (report_directory / "blueprint.md").read_text() == "# Stored blueprint\n"
    assert (report_directory / "blueprint.json").is_file()
    assert record.blueprint_version == 1
    assert record.lead_review_id == review_id
    assert record.storage_backend == "filesystem"


def test_s3_storage_uses_versioned_consultation_key() -> None:
    consultation_id = generate_uuid()
    client = _S3Client()
    storage = S3BlueprintReportStorage(
        "reports",
        client=client,
        store_json=True,
    )

    record = storage.store(
        consultation_id=consultation_id,
        blueprint=_blueprint(),
        lead_review_id=generate_uuid(),
    )

    prefix = f"consultations/{consultation_id}/blueprints/v1"
    assert [item["Key"] for item in client.objects] == [
        f"{prefix}/blueprint.md",
        f"{prefix}/blueprint.json",
    ]
    assert record.s3_key == f"{prefix}/blueprint.md"
    assert record.storage_backend == "s3"
