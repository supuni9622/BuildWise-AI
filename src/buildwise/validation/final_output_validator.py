"""Validation of the actual assembled blueprint and rendered Markdown."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from buildwise.domain.blueprint import BlueprintSection, ProductBlueprint
from buildwise.domain.enums import BlueprintSectionType
from buildwise.reporting.markdown_renderer import render_blueprint_markdown

_PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|LOREM\s+IPSUM)\b|"
    r"<\s*insert\b[^>]*>|\[\s*placeholder\s*\]",
    re.IGNORECASE,
)


def validate_final_output(blueprint: ProductBlueprint) -> None:
    """Reject an incomplete or internally inconsistent final deliverable."""

    _require_text(blueprint.title, "title")
    _require_text(blueprint.executive_summary, "executive_summary")
    _validate_sections(blueprint)
    _validate_disclosures(blueprint)
    _validate_usage(blueprint)

    expected_markdown = render_blueprint_markdown(
        blueprint.model_copy(update={"generated_markdown": ""})
    )
    if blueprint.generated_markdown != expected_markdown:
        raise ValueError(
            "generated_markdown is stale or does not match the assembled blueprint."
        )
    _reject_placeholders(blueprint.generated_markdown, "generated_markdown")


def _validate_sections(blueprint: ProductBlueprint) -> None:
    expected = list(BlueprintSectionType)
    actual = [section.section for section in blueprint.sections]
    if actual != expected:
        raise ValueError(
            "Blueprint sections must be complete, unique, and in canonical order."
        )

    for section in blueprint.sections:
        _require_text(section.title, f"{section.section}.title")
        _require_text(section.summary, f"{section.section}.summary")
        _require_text(section.markdown, f"{section.section}.markdown")
        if not section.markdown.startswith(f"## {section.title}\n"):
            raise ValueError(
                f"{section.section}.markdown must start with its rendered section title."
            )
        _reject_placeholders(section.summary, f"{section.section}.summary")
        _reject_placeholders(section.markdown, f"{section.section}.markdown")
        _validate_references(section)

    costs = _section(blueprint, BlueprintSectionType.COSTS)
    if "estimate" not in costs.summary.casefold():
        raise ValueError("The Costs section must disclose that project costs are estimates.")


def _validate_disclosures(blueprint: ProductBlueprint) -> None:
    mappings = (
        (
            blueprint.risks,
            _section(blueprint, BlueprintSectionType.RISKS_AND_ASSUMPTIONS),
            "risk",
        ),
        (
            blueprint.assumptions,
            _section(blueprint, BlueprintSectionType.RISKS_AND_ASSUMPTIONS),
            "assumption",
        ),
        (
            blueprint.open_questions,
            _section(blueprint, BlueprintSectionType.OPEN_QUESTIONS),
            "open question",
        ),
        (
            blueprint.limitations,
            _section(blueprint, BlueprintSectionType.LIMITATIONS),
            "limitation",
        ),
        (
            blueprint.implementation_phases,
            _section(blueprint, BlueprintSectionType.IMPLEMENTATION_GUIDANCE),
            "implementation phase",
        ),
    )
    for values, section, label in mappings:
        for value in values:
            if value not in section.markdown:
                raise ValueError(
                    f"Final Markdown omits the declared {label}: {value!r}."
                )


def _validate_usage(blueprint: ProductBlueprint) -> None:
    usage = blueprint.usage_summary
    if usage.prompt_tokens + usage.completion_tokens > usage.total_tokens:
        raise ValueError(
            "usage_summary.total_tokens cannot be lower than prompt plus completion tokens."
        )


def _validate_references(section: BlueprintSection) -> None:
    for reference in section.references:
        _require_text(reference.source, f"{section.section}.reference.source")
        _require_text(reference.description, f"{section.section}.reference.description")
        if reference.url is not None:
            parsed = urlparse(reference.url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(
                    f"{section.section} contains an invalid final reference URL."
                )


def _section(
    blueprint: ProductBlueprint,
    section_type: BlueprintSectionType,
) -> BlueprintSection:
    return next(section for section in blueprint.sections if section.section is section_type)


def _require_text(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be blank.")


def _reject_placeholders(value: str, name: str) -> None:
    if _PLACEHOLDER_PATTERN.search(value):
        raise ValueError(f"{name} contains an unresolved placeholder.")
