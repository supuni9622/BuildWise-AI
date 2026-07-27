from __future__ import annotations

import pytest

from buildwise.domain.enums import RevisionTarget, SpecialistType
from buildwise.domain.review import RevisionRequest
from buildwise.flows.revisions import RevisionCrew, route_targeted_revision
from buildwise.flows.state import BuildWiseFlowState


def _request(target: RevisionTarget) -> RevisionRequest:
    return RevisionRequest(target=target, reason="A material correction is required.")


def _state(*specialists: SpecialistType, revision_count: int = 0) -> BuildWiseFlowState:
    state = BuildWiseFlowState(revision_count=revision_count)
    for specialist in specialists:
        state.register_specialist(
            specialist=specialist,
            selected=True,
            reason="required",
            rationale="Selected for deterministic revision routing.",
        )
    return state


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (
            RevisionTarget.SOLUTION_ARCHITECTURE,
            (
                SpecialistType.SOLUTION_ARCHITECTURE,
                SpecialistType.AI_ARCHITECTURE,
                SpecialistType.SECURITY_ARCHITECTURE,
                SpecialistType.QA_AND_EVALUATION,
            ),
        ),
        (
            RevisionTarget.AI_ARCHITECTURE,
            (
                SpecialistType.AI_ARCHITECTURE,
                SpecialistType.SECURITY_ARCHITECTURE,
                SpecialistType.QA_AND_EVALUATION,
            ),
        ),
        (
            RevisionTarget.SECURITY_ARCHITECTURE,
            (SpecialistType.SECURITY_ARCHITECTURE, SpecialistType.QA_AND_EVALUATION),
        ),
        (
            RevisionTarget.QA_AND_EVALUATION,
            (SpecialistType.QA_AND_EVALUATION,),
        ),
    ],
)
def test_technical_revision_cascades_to_selected_dependants(
    target: RevisionTarget,
    expected: tuple[SpecialistType, ...],
) -> None:
    state = _state(*tuple(SpecialistType))

    route = route_targeted_revision(state=state, requests=[_request(target)])

    assert route.crews == {RevisionCrew.TECHNICAL_PLANNING}
    assert route.technical_specialists == expected


def test_product_target_routes_to_product_planning() -> None:
    route = route_targeted_revision(
        state=_state(SpecialistType.SOLUTION_ARCHITECTURE),
        requests=[_request(RevisionTarget.REQUIREMENTS)],
    )

    assert route.crews == {RevisionCrew.PRODUCT_PLANNING}
    assert route.technical_specialists == ()


def test_cost_summary_revision_rebuilds_without_another_crew() -> None:
    route = route_targeted_revision(
        state=_state(SpecialistType.SOLUTION_ARCHITECTURE),
        requests=[_request(RevisionTarget.COST_SUMMARY)],
    )

    assert route.crews == set()
    assert route.rebuild_cost_summary is True
    assert route.technical_specialists == ()


def test_revision_limit_is_enforced() -> None:
    with pytest.raises(ValueError, match="maximum number"):
        route_targeted_revision(
            state=_state(SpecialistType.SOLUTION_ARCHITECTURE, revision_count=2),
            requests=[_request(RevisionTarget.SOLUTION_ARCHITECTURE)],
        )
