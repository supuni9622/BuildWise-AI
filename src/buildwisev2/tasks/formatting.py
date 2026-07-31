"""Small shared formatting helpers used by multiple task factories.

Kept separate from ``guardrails.py`` because these construct prompt text,
not validation logic.
"""

from __future__ import annotations

from crewai import Task
from pydantic import BaseModel

from buildwisev2.domain.review import RevisionRequest


def revision_section(revision_request: RevisionRequest | None) -> str:
    """Render a bounded revision-instructions block, or a no-op notice."""

    if revision_request is None:
        return "No revision requested. Produce the artifact from scratch."
    return (
        "This is a targeted revision, not a full regeneration.\n"
        f"Issue: {revision_request.issue}\n"
        f"Instructions: {revision_request.instructions}\n"
        "Preserve every section and decision not affected by this issue. "
        "Stay within your own specialist ownership."
    )


def resolve_upstream_artifact(
    *,
    live_task: Task | None,
    prior_artifact: BaseModel | None,
    label: str,
    placeholder_key: str,
) -> tuple[str, Task | None]:
    """Describe one upstream dependency for a Task description.

    Exactly one of ``live_task`` (same-Crew, this run regenerates it) or
    ``prior_artifact`` (an earlier run's approved artifact, reused as-is
    because this targeted revision does not touch it) should be supplied
    by the caller — never both. Returns a ``(description_block,
    context_task_or_none)`` pair: the text to embed in the description, and
    the Task to add to native CrewAI ``context=`` (``None`` when reusing a
    prior artifact via a kickoff placeholder instead).
    """

    if live_task is not None:
        return (
            f"(the approved {label} is available above as prior Task context)",
            live_task,
        )
    if prior_artifact is not None:
        return (
            f"\nApproved {label} from an earlier run (not being revised now)\n"
            f"{{{placeholder_key}}}",
            None,
        )
    return f"(no {label} was selected for this consultation)", None
