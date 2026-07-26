"""Shared revision-instruction formatting for BuildWise CrewAI tasks.

Specialist task factories accept an optional ``RevisionRequest`` so the same
Crew can be reused for both initial generation and a Lead-Review-triggered
targeted revision. Formatting the bounded instruction text is identical
across every specialist task factory, so it lives here instead of being
duplicated in each module.
"""

from __future__ import annotations

from buildwise.domain.review import RevisionRequest


def format_revision_instructions(revision_request: RevisionRequest) -> str:
    """Format a bounded revision-instruction block for a task description."""

    if revision_request.requested_changes:
        requested_changes = "\n".join(
            f"  - {change}" for change in revision_request.requested_changes
        )
    else:
        requested_changes = "  - (no specific changes listed; use the reason below)"

    return (
        "Revision instructions:\n"
        f"Reason: {revision_request.reason}\n"
        "Requested changes:\n"
        f"{requested_changes}\n\n"
        "Preserve every unaffected section and every previously valid "
        "decision from the prior output. Address only the issue described "
        "above, stay within your specialist ownership, and still return "
        "the complete, schema-valid root output model rather than a partial "
        "patch."
    )
