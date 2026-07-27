from __future__ import annotations

import pytest

from buildwise.domain.enums import DependencyType, ExecutionMode, SpecialistType
from buildwise.domain.specialist_planning import SpecialistDependency, SpecialistExecutionGroup
from buildwise.planning import execution_graph

_SOLUTION = SpecialistType.SOLUTION_ARCHITECTURE
_AI = SpecialistType.AI_ARCHITECTURE
_SECURITY = SpecialistType.SECURITY_ARCHITECTURE
_QA = SpecialistType.QA_AND_EVALUATION


class TestBuildDependencies:
    def test_solution_only_has_no_dependencies(self) -> None:
        dependencies = execution_graph.build_dependencies(selected_specialists={_SOLUTION})

        assert dependencies == []

    def test_solution_and_ai(self) -> None:
        dependencies = execution_graph.build_dependencies(
            selected_specialists={_SOLUTION, _AI},
        )

        assert len(dependencies) == 1
        assert dependencies[0].source is _SOLUTION
        assert dependencies[0].target is _AI
        assert dependencies[0].dependency is DependencyType.REQUIRES_OUTPUT

    def test_solution_and_security(self) -> None:
        dependencies = execution_graph.build_dependencies(
            selected_specialists={_SOLUTION, _SECURITY},
        )

        pairs = {(dependency.source, dependency.target) for dependency in dependencies}

        assert pairs == {(_SOLUTION, _SECURITY)}

    def test_solution_ai_security_qa(self) -> None:
        dependencies = execution_graph.build_dependencies(
            selected_specialists={_SOLUTION, _AI, _SECURITY, _QA},
        )

        pairs = {(dependency.source, dependency.target) for dependency in dependencies}

        assert pairs == {
            (_SOLUTION, _AI),
            (_SOLUTION, _SECURITY),
            (_AI, _SECURITY),
            (_SOLUTION, _QA),
            (_AI, _QA),
            (_SECURITY, _QA),
        }

    def test_no_self_dependencies(self) -> None:
        dependencies = execution_graph.build_dependencies(
            selected_specialists={_SOLUTION, _AI, _SECURITY, _QA},
        )

        assert all(dependency.source != dependency.target for dependency in dependencies)

    def test_dependent_without_solution_raises(self) -> None:
        with pytest.raises(ValueError, match="Solution Architecture"):
            execution_graph.build_dependencies(selected_specialists={_AI})


class TestBuildExecutionGroups:
    def test_every_selected_specialist_appears_once(self) -> None:
        selected = {_SOLUTION, _AI, _SECURITY, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)

        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )

        grouped = [specialist for group in groups for specialist in group.specialists]

        assert set(grouped) == selected
        assert len(grouped) == len(set(grouped))

    def test_excluded_specialists_never_appear(self) -> None:
        selected = {_SOLUTION, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)

        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )

        grouped = {specialist for group in groups for specialist in group.specialists}

        assert _AI not in grouped
        assert _SECURITY not in grouped

    def test_solution_precedes_dependents(self) -> None:
        selected = {_SOLUTION, _AI, _SECURITY, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)

        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )

        order = [group.specialists[0] for group in groups]

        assert order.index(_SOLUTION) < order.index(_AI)
        assert order.index(_SOLUTION) < order.index(_SECURITY)
        assert order.index(_SOLUTION) < order.index(_QA)
        assert order.index(_AI) < order.index(_SECURITY)
        assert order.index(_AI) < order.index(_QA)
        assert order.index(_SECURITY) < order.index(_QA)

    def test_all_groups_are_sequential(self) -> None:
        selected = {_SOLUTION, _SECURITY, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)

        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )

        assert all(group.execution_mode is ExecutionMode.SEQUENTIAL for group in groups)


class TestValidateExecutionGraph:
    def test_valid_graph_passes(self) -> None:
        selected = {_SOLUTION, _AI, _SECURITY, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)
        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )

        execution_graph.validate_execution_graph(
            selected_specialists=selected,
            dependencies=dependencies,
            execution_groups=groups,
        )

    def test_self_dependency_is_rejected(self) -> None:
        selected = {_SOLUTION}
        dependencies = [
            SpecialistDependency(
                source=_SOLUTION,
                target=_SOLUTION,
                dependency=DependencyType.REQUIRES_OUTPUT,
                description="Invalid self dependency.",
            )
        ]
        groups = [
            SpecialistExecutionGroup(
                name=_SOLUTION.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION],
                rationale="Runs first.",
            )
        ]

        with pytest.raises(ValueError, match="cannot depend on itself"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )

    def test_missing_specialist_from_groups_is_rejected(self) -> None:
        selected = {_SOLUTION, _QA}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)
        groups = [
            SpecialistExecutionGroup(
                name=_SOLUTION.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION],
                rationale="Runs first.",
            )
        ]

        with pytest.raises(ValueError, match="missing from execution groups"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )

    def test_excluded_specialist_in_groups_is_rejected(self) -> None:
        selected = {_SOLUTION}
        dependencies: list[SpecialistDependency] = []
        groups = [
            SpecialistExecutionGroup(
                name=_SOLUTION.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION, _QA],
                rationale="Runs first.",
            )
        ]

        with pytest.raises(ValueError, match="was not selected"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )

    def test_out_of_order_groups_are_rejected(self) -> None:
        selected = {_SOLUTION, _AI}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)
        groups = [
            SpecialistExecutionGroup(
                name=_AI.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_AI],
                rationale="Runs first (invalid).",
            ),
            SpecialistExecutionGroup(
                name=_SOLUTION.value,
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION],
                rationale="Runs second (invalid).",
            ),
        ]

        with pytest.raises(ValueError, match="do not order"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )

    def test_parallel_group_with_internal_dependency_is_rejected(self) -> None:
        selected = {_SOLUTION, _AI}
        dependencies = execution_graph.build_dependencies(selected_specialists=selected)
        groups = [
            SpecialistExecutionGroup(
                name="invalid_parallel_group",
                execution_mode=ExecutionMode.PARALLEL,
                specialists=[_SOLUTION, _AI],
                rationale="Invalid: AI depends on Solution.",
            )
        ]

        with pytest.raises(ValueError, match="direct dependency"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )

    def test_duplicate_specialist_across_groups_is_rejected(self) -> None:
        selected = {_SOLUTION}
        dependencies: list[SpecialistDependency] = []
        groups = [
            SpecialistExecutionGroup(
                name="group_one",
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION],
                rationale="Runs first.",
            ),
            SpecialistExecutionGroup(
                name="group_two",
                execution_mode=ExecutionMode.SEQUENTIAL,
                specialists=[_SOLUTION],
                rationale="Runs again (invalid).",
            ),
        ]

        with pytest.raises(ValueError, match="exactly one execution group"):
            execution_graph.validate_execution_graph(
                selected_specialists=selected,
                dependencies=dependencies,
                execution_groups=groups,
            )
