"""Deterministic construction and validation of the specialist execution graph.

This module owns the small, fixed dependency graph between the four
technical specialists (Solution, AI, Security, QA). It is intentionally not
a general DAG engine: the set of possible edges is fixed and enumerated
directly from ``buildwise/prds/05_specialist_planner.md`` section 17.

Market & GTM is never part of this graph: it belongs to the Product Planning
Crew and is decided by the early-market policy, not by technical planning.
"""

from __future__ import annotations

from buildwise.domain.enums import DependencyType, ExecutionMode, SpecialistType
from buildwise.domain.specialist_planning import (
    SpecialistDependency,
    SpecialistExecutionGroup,
)

_TECHNICAL_SPECIALIST_NAMES: dict[SpecialistType, str] = {
    SpecialistType.SOLUTION_ARCHITECTURE: "Solution Architecture",
    SpecialistType.AI_ARCHITECTURE: "AI Architecture",
    SpecialistType.SECURITY_ARCHITECTURE: "Security Architecture",
    SpecialistType.QA_AND_EVALUATION: "QA & Evaluation",
}


def build_dependencies(
    *,
    selected_specialists: set[SpecialistType],
) -> list[SpecialistDependency]:
    """Build the fixed technical-specialist dependency graph.

    Raises:
        ValueError: If AI Architecture, Security Architecture, or QA &
            Evaluation is selected without Solution Architecture, since each
            of those specialists depends on the Solution Architecture output
            inside the Technical Planning Crew.
    """

    solution_selected = SpecialistType.SOLUTION_ARCHITECTURE in selected_specialists
    ai_selected = SpecialistType.AI_ARCHITECTURE in selected_specialists
    security_selected = SpecialistType.SECURITY_ARCHITECTURE in selected_specialists
    qa_selected = SpecialistType.QA_AND_EVALUATION in selected_specialists

    dependents = [
        specialist
        for specialist, is_selected in (
            (SpecialistType.AI_ARCHITECTURE, ai_selected),
            (SpecialistType.SECURITY_ARCHITECTURE, security_selected),
            (SpecialistType.QA_AND_EVALUATION, qa_selected),
        )
        if is_selected
    ]

    if dependents and not solution_selected:
        formatted = ", ".join(sorted(specialist.value for specialist in dependents))
        raise ValueError(
            "Solution Architecture must be selected whenever a dependent "
            f"technical specialist is selected: {formatted}."
        )

    dependencies: list[SpecialistDependency] = []

    if ai_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.AI_ARCHITECTURE,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description=(
                    "AI Architecture designs against the approved Solution "
                    "Architecture and cannot start before it completes."
                ),
            )
        )

    if security_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.SECURITY_ARCHITECTURE,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description=(
                    "Security Architecture reviews the approved Solution "
                    "Architecture's components, boundaries, and integrations."
                ),
            )
        )

        if ai_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.AI_ARCHITECTURE,
                    target=SpecialistType.SECURITY_ARCHITECTURE,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description=(
                        "Security Architecture must also review the AI "
                        "Architecture's model, tool, and agent boundaries."
                    ),
                )
            )

    if qa_selected:
        dependencies.append(
            SpecialistDependency(
                source=SpecialistType.SOLUTION_ARCHITECTURE,
                target=SpecialistType.QA_AND_EVALUATION,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description="QA and Evaluation validates the approved Solution Architecture.",
            )
        )

        if ai_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.AI_ARCHITECTURE,
                    target=SpecialistType.QA_AND_EVALUATION,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description="QA and Evaluation includes AI evaluation coverage.",
                )
            )

        if security_selected:
            dependencies.append(
                SpecialistDependency(
                    source=SpecialistType.SECURITY_ARCHITECTURE,
                    target=SpecialistType.QA_AND_EVALUATION,
                    dependency=DependencyType.REQUIRES_OUTPUT,
                    description="QA and Evaluation validates the security controls.",
                )
            )

    return dependencies


def build_execution_groups(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
) -> list[SpecialistExecutionGroup]:
    """Build ordered execution groups from a topological sort.

    The current Technical Planning Crew runs ``Process.sequential``, so this
    builder produces one specialist per group in dependency order rather than
    theoretical parallel groups (see PRD section 18.4).
    """

    ordered = _topological_order(
        selected_specialists=selected_specialists,
        dependencies=dependencies,
    )

    groups: list[SpecialistExecutionGroup] = []

    for specialist in ordered:
        incoming = [dependency for dependency in dependencies if dependency.target is specialist]

        if incoming:
            sources = ", ".join(
                _TECHNICAL_SPECIALIST_NAMES[dependency.source] for dependency in incoming
            )
            rationale = f"Runs after {sources}, whose output this specialist requires."
        else:
            rationale = "Has no unmet dependency and can run first."

        groups.append(
            SpecialistExecutionGroup(
                name=specialist.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[specialist],
                rationale=rationale,
            )
        )

    return groups


def validate_execution_graph(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
    execution_groups: list[SpecialistExecutionGroup],
) -> None:
    """Validate dependency and execution-group invariants.

    Raises:
        ValueError: If any invariant from PRD section 23 is violated.
    """

    for dependency in dependencies:
        if dependency.source == dependency.target:
            raise ValueError(f"Specialist '{dependency.source.value}' cannot depend on itself.")

        if dependency.source not in selected_specialists:
            raise ValueError(
                f"Dependency source '{dependency.source.value}' is not a selected specialist."
            )

        if dependency.target not in selected_specialists:
            raise ValueError(
                f"Dependency target '{dependency.target.value}' is not a selected specialist."
            )

    # A successful topological sort proves there is no cycle and that every
    # selected specialist is reachable.
    _topological_order(
        selected_specialists=selected_specialists,
        dependencies=dependencies,
    )

    grouped_specialists: list[SpecialistType] = []

    for group in execution_groups:
        if group.execution_mode is ExecutionMode.PARALLEL:
            for specialist in group.specialists:
                for other in group.specialists:
                    if specialist is other:
                        continue

                    conflicting = any(
                        (dependency.source is specialist and dependency.target is other)
                        or (dependency.source is other and dependency.target is specialist)
                        for dependency in dependencies
                    )

                    if conflicting:
                        raise ValueError(
                            "Parallel execution group "
                            f"'{group.name}' contains specialists with a "
                            "direct dependency between them."
                        )

        for specialist in group.specialists:
            if specialist not in selected_specialists:
                raise ValueError(
                    f"Execution group '{group.name}' references specialist "
                    f"'{specialist.value}', which was not selected."
                )

            grouped_specialists.append(specialist)

    if len(grouped_specialists) != len(set(grouped_specialists)):
        raise ValueError("Each selected specialist must appear in exactly one execution group.")

    missing = selected_specialists.difference(grouped_specialists)

    if missing:
        formatted = ", ".join(sorted(specialist.value for specialist in missing))
        raise ValueError(f"Selected specialists are missing from execution groups: {formatted}.")

    order_index = {specialist: index for index, specialist in enumerate(grouped_specialists)}

    for dependency in dependencies:
        source_index = order_index[dependency.source]
        target_index = order_index[dependency.target]

        if source_index >= target_index:
            raise ValueError(
                f"Execution groups do not order '{dependency.source.value}' "
                f"before dependent '{dependency.target.value}'."
            )


def _topological_order(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
) -> list[SpecialistType]:
    """Return a stable topological order of the selected specialists.

    Raises:
        ValueError: If the dependency graph contains a cycle.
    """

    remaining = set(selected_specialists)
    incoming: dict[SpecialistType, set[SpecialistType]] = {
        specialist: set() for specialist in remaining
    }

    for dependency in dependencies:
        if dependency.target in incoming and dependency.source in remaining:
            incoming[dependency.target].add(dependency.source)

    ordered: list[SpecialistType] = []

    # Deterministic tie-break: iterate the canonical SpecialistType
    # declaration order rather than set iteration order.
    canonical_order = list(SpecialistType)

    while remaining:
        ready = [
            specialist
            for specialist in canonical_order
            if specialist in remaining and not incoming[specialist]
        ]

        if not ready:
            formatted = ", ".join(sorted(specialist.value for specialist in remaining))
            raise ValueError(
                f"Specialist dependency graph contains a cycle involving: {formatted}."
            )

        for specialist in ready:
            ordered.append(specialist)
            remaining.discard(specialist)

            for dependents in incoming.values():
                dependents.discard(specialist)

    return ordered
