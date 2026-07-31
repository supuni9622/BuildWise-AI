"""Small fixed specialist dependency graph — not a general DAG engine.

The technical specialist graph has exactly four possible nodes and a fixed
set of edges (see ``05_specialist_planner.md`` section 17), so this module
builds and validates that fixed graph rather than implementing generic
graph machinery.
"""

from __future__ import annotations

from buildwisev2.domain.common import SpecialistType
from buildwisev2.domain.specialist_planning import (
    DependencyType,
    ExecutionMode,
    SpecialistDependency,
    SpecialistExecutionGroup,
)

# Fixed topological order for the technical specialist graph.
_CANONICAL_ORDER = (
    SpecialistType.SOLUTION_ARCHITECTURE,
    SpecialistType.AI_ARCHITECTURE,
    SpecialistType.SECURITY_ARCHITECTURE,
    SpecialistType.QA_AND_EVALUATION,
)


def build_dependencies(*, selected_specialists: set[SpecialistType]) -> list[SpecialistDependency]:
    dependencies: list[SpecialistDependency] = []

    def add(source: SpecialistType, target: SpecialistType, description: str) -> None:
        if source in selected_specialists and target in selected_specialists:
            dependencies.append(
                SpecialistDependency(
                    source=source,
                    target=target,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description=description,
                )
            )

    add(
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
        "AI Architecture must fit inside the approved general solution architecture.",
    )
    add(
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        "Security Architecture requires system components, boundaries, and integrations.",
    )
    add(
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        "Security review must account for AI-specific tool use and attack surfaces.",
    )
    add(
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
        "QA planning requires the architecture it must validate.",
    )
    add(
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
        "QA must include AI evaluation coverage when AI Architecture exists.",
    )
    add(
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
        "QA must validate the selected security controls.",
    )

    return dependencies


def build_execution_groups(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
) -> list[SpecialistExecutionGroup]:
    """Return one sequential group per selected specialist, in canonical order.

    The Technical Planning Crew currently uses ``Process.sequential``, so
    the planner favors valid sequential groups over theoretical
    parallelism — see the planner PRD section 18.4.
    """

    groups: list[SpecialistExecutionGroup] = []
    for specialist in _CANONICAL_ORDER:
        if specialist not in selected_specialists:
            continue
        groups.append(
            SpecialistExecutionGroup(
                name=specialist.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[specialist],
                rationale=f"{specialist.value} runs after its upstream dependencies complete.",
            )
        )
    return groups


def validate_execution_graph(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
    execution_groups: list[SpecialistExecutionGroup],
) -> None:
    group_order: dict[SpecialistType, int] = {}
    seen: set[SpecialistType] = set()
    for index, group in enumerate(execution_groups):
        for specialist in group.specialists:
            if specialist in seen:
                raise ValueError(f"{specialist} appears in more than one execution group")
            if specialist not in selected_specialists:
                raise ValueError(f"{specialist} appears in an execution group but was not selected")
            seen.add(specialist)
            group_order[specialist] = index

    missing = selected_specialists - seen
    if missing:
        raise ValueError(f"Selected specialists missing from execution groups: {sorted(missing)}")

    for dependency in dependencies:
        if dependency.source == dependency.target:
            raise ValueError(f"{dependency.source} cannot depend on itself")
        if (
            dependency.source not in selected_specialists
            or dependency.target not in selected_specialists
        ):
            raise ValueError(
                f"Dependency {dependency.source} -> {dependency.target} "
                "references an unselected specialist"
            )
        if group_order[dependency.source] >= group_order[dependency.target]:
            raise ValueError(
                f"Dependency {dependency.source} -> {dependency.target} "
                "is not respected by execution group order"
            )

    for group in execution_groups:
        if group.execution_mode == ExecutionMode.PARALLEL and len(group.specialists) > 1:
            in_group = set(group.specialists)
            for dependency in dependencies:
                if dependency.source in in_group and dependency.target in in_group:
                    raise ValueError(
                        f"Parallel group {group.name!r} contains a dependency between its own "
                        "members"
                    )
