"""Deterministic Markdown rendering for product blueprints."""

from __future__ import annotations

from pathlib import Path

from buildwise.domain.blueprint import ProductBlueprint


def render_blueprint_markdown(blueprint: ProductBlueprint) -> str:
    """Render a blueprint without invoking an LLM."""

    parts = [f"# {blueprint.title}", ""]
    parts.extend(section.markdown.strip() for section in blueprint.sections)
    parts.extend(
        [
            "",
            "---",
            "",
            f"Blueprint version: {blueprint.version}",
            _usage_line(blueprint),
        ]
    )
    return "\n\n".join(part for part in parts if part != "").strip() + "\n"


def _usage_line(blueprint: ProductBlueprint) -> str:
    cost = blueprint.usage_summary.estimated_cost
    cost_text = "estimated cost unavailable" if cost is None else f"estimated cost ${cost:.2f}"
    return (
        f"Usage: {blueprint.usage_summary.total_tokens:,} tokens, "
        f"{blueprint.usage_summary.total_agents} agent executions, {cost_text}."
    )


def write_blueprint_markdown(
    blueprint: ProductBlueprint,
    output_path: str | Path = "blueprint.md",
) -> Path:
    """Write a rendered blueprint to ``blueprint.md`` or a supplied path."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_blueprint_markdown(blueprint), encoding="utf-8")
    return path


class MarkdownRenderer:
    """Object boundary for callers that prefer an injected renderer."""

    render = staticmethod(render_blueprint_markdown)
    write = staticmethod(write_blueprint_markdown)
