"""Tests for wire_compact_context.

CrewAI's native ``Task.context = [other_task]`` mechanism injects the full
raw output of the upstream task once it completes. ``wire_compact_context``
is the mechanism that replaces that with a compact, field-projected context
object instead, for tasks chained inside a single Crew (where the real
upstream artifact does not exist yet at Task-construction time).
"""

from __future__ import annotations

import pytest
from crewai import Task
from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel

from buildwise.tasks.context_wiring import wire_compact_context


class _Source(BaseModel):
    value: str


class _Projection(BaseModel):
    projected_value: str


def _task(description: str) -> Task:
    return Task(description=description, expected_output="anything")


def test_placeholder_is_replaced_once_source_completes() -> None:
    source = _task("produce a value")
    target = _task("Context: <<PLACEHOLDER>>\n\nDo the thing.")

    wire_compact_context(
        source_task=source,
        target_task=target,
        placeholder="<<PLACEHOLDER>>",
        project=lambda raw: _Projection(projected_value=raw.value.upper()),
    )

    assert "<<PLACEHOLDER>>" in target.description  # not yet replaced

    source.callback(TaskOutput(description="d", raw="{}", agent="a", pydantic=_Source(value="hi")))

    assert "<<PLACEHOLDER>>" not in target.description
    assert '"projected_value":"HI"' in target.description


def test_missing_placeholder_raises_immediately() -> None:
    source = _task("produce a value")
    target = _task("no marker here")

    with pytest.raises(ValueError, match="does not contain"):
        wire_compact_context(
            source_task=source,
            target_task=target,
            placeholder="<<PLACEHOLDER>>",
            project=lambda raw: _Projection(projected_value="x"),
        )


def test_multiple_targets_from_the_same_source_both_resolve() -> None:
    """Solution Architecture feeds AI, Security, and QA in the real Crew —
    one source task's callback must fan out to every downstream target."""

    source = _task("produce a value")
    target_a = _task("A context: <<PLACEHOLDER>>")
    target_b = _task("B context: <<PLACEHOLDER>>")

    for target in (target_a, target_b):
        wire_compact_context(
            source_task=source,
            target_task=target,
            placeholder="<<PLACEHOLDER>>",
            project=lambda raw: _Projection(projected_value=raw.value),
        )

    source.callback(
        TaskOutput(description="d", raw="{}", agent="a", pydantic=_Source(value="shared"))
    )

    assert "<<PLACEHOLDER>>" not in target_a.description
    assert "<<PLACEHOLDER>>" not in target_b.description
    assert "shared" in target_a.description
    assert "shared" in target_b.description


def test_chained_wiring_preserves_earlier_callbacks() -> None:
    """Security Architecture receives context from both Solution and AI —
    two separate wire_compact_context calls on two different sources must
    not clobber each other, and each must fire independently."""

    solution = _task("produce solution")
    ai = _task("produce ai")
    security = _task("Solution: <<SOLUTION>>\nAI: <<AI>>")

    wire_compact_context(
        source_task=solution,
        target_task=security,
        placeholder="<<SOLUTION>>",
        project=lambda raw: _Projection(projected_value=f"solution:{raw.value}"),
    )
    wire_compact_context(
        source_task=ai,
        target_task=security,
        placeholder="<<AI>>",
        project=lambda raw: _Projection(projected_value=f"ai:{raw.value}"),
    )

    solution.callback(TaskOutput(description="d", raw="{}", agent="a", pydantic=_Source(value="S")))
    assert "<<SOLUTION>>" not in security.description
    assert "<<AI>>" in security.description  # not yet, ai hasn't run

    ai.callback(TaskOutput(description="d", raw="{}", agent="a", pydantic=_Source(value="A")))
    assert "<<AI>>" not in security.description
