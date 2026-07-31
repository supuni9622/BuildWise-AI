"""Product Blueprint domain models — the final deterministic assembly output."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class BlueprintSection(BuildWiseModel):
    """One rendered section of the final blueprint document."""

    section: str
    """Stable slug, e.g. "discovery", "product_definition", "solution_architecture"."""
    title: str
    summary: str
    markdown: str


class ProductBlueprint(BuildWiseModel):
    """The deterministic, final assembled artifact of a consultation.

    Assembled by ``buildwisev2.reporting.blueprint_builder`` from already
    approved structured artifacts. No LLM call produces this model —
    assembly is a rendering step, not a reasoning step.
    """

    session_id: UUID
    title: str
    executive_summary: str
    sections: list[BlueprintSection]
    open_questions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_markdown: str
    version: str = "1.0"
