"""Wires compact context projections into same-Crew chained tasks.

CrewAI's native ``Task.context = [other_task]`` mechanism injects the full
raw output of ``other_task`` into the downstream prompt once it completes
(``Crew._get_context`` -> ``aggregate_raw_outputs_from_tasks``). For
downstream specialists whose upstream artifacts carry hundreds of fields
(``AIArchitecture`` alone has 428), that defeats the compact, field-projected
context objects already built in ``planning/specialist_context.py`` — they
were only reachable when specialists ran in separate Crews, because the real
completed artifact doesn't exist yet when tasks in the *same* Crew are
constructed, before ``Crew.kickoff()`` runs.

This module closes that gap using CrewAI's task ``callback`` hook, which
fires synchronously right after a task completes and before
``Process.sequential`` advances to the next task. ``wire_compact_context``
attaches a callback to the upstream task that replaces a placeholder token
in the downstream task's already-built ``description`` with the compact
projection, computed from the upstream task's real structured output.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from crewai import Task
from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel

SOLUTION_CONTEXT_PLACEHOLDER = "<<SOLUTION_ARCHITECTURE_COMPACT_CONTEXT>>"
AI_CONTEXT_PLACEHOLDER = "<<AI_ARCHITECTURE_COMPACT_CONTEXT>>"
SECURITY_CONTEXT_PLACEHOLDER = "<<SECURITY_ARCHITECTURE_COMPACT_CONTEXT>>"
PRODUCT_DEFINITION_CONTEXT_PLACEHOLDER = "<<PRODUCT_DEFINITION_COMPACT_CONTEXT>>"
REQUIREMENTS_CONTEXT_PLACEHOLDER = "<<REQUIREMENTS_SPECIFICATION_COMPACT_CONTEXT>>"
"""Unique markers embedded in a downstream task's description at
construction time, each replaced by exactly one ``wire_compact_context``
call once its corresponding upstream task completes in the same Crew."""


def wire_compact_context(
    *,
    source_task: Task,
    target_task: Task,
    placeholder: str,
    project: Callable[[Any], BaseModel],
) -> None:
    """Replace ``placeholder`` in ``target_task.description`` once ``source_task`` finishes.

    Args:
        source_task: The upstream task whose completion supplies the context.
        target_task: The downstream task whose description already contains
            exactly one occurrence of ``placeholder``.
        placeholder: A unique marker string embedded in ``target_task``'s
            description at construction time.
        project: Builds the compact context object from
            ``source_task.output.pydantic`` once it is available.

    Raises:
        ValueError: If ``target_task.description`` does not contain
            ``placeholder``, since that means the wiring would silently do
            nothing.

    Note:
        Callers must build ``target_task`` with ``context=[]`` (an explicit
        empty list), never ``context=[source_task]`` and never left unset.
        CrewAI injects ``context`` into the prompt independently of
        ``description`` (``Crew._get_context`` -> aggregated raw task
        outputs, passed to ``Agent.execute_task`` alongside the prompt built
        from ``description``). Setting ``context=[source_task]`` re-adds the
        full raw output this function exists to avoid, on top of the
        compact projection. Leaving ``context`` unset is worse, not neutral:
        CrewAI's sentinel default (``NOT_SPECIFIED``) makes ``_get_context``
        aggregate the raw output of *every* task the Crew has run so far,
        not just the immediate upstream one. Only an explicit ``[]`` makes
        ``_get_context`` return "" and rely solely on ``description``.
    """

    if placeholder not in target_task.description:
        raise ValueError(
            f"Target task '{target_task.name}' description does not contain "
            f"the placeholder '{placeholder}'. Nothing would be wired."
        )

    previous_callback = source_task.callback

    def _callback(output: TaskOutput) -> None:
        if previous_callback is not None:
            previous_callback(output)

        projection = project(output.pydantic)
        target_task.description = target_task.description.replace(
            placeholder,
            projection.model_dump_json(),
            1,
        )

    source_task.callback = _callback
