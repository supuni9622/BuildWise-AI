"""Deterministic routing for bounded, targeted planning revisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from buildwise.domain.enums import RevisionTarget, SpecialistType
from buildwise.domain.review import RevisionRequest
from buildwise.flows.state import BuildWiseFlowState


class RevisionCrew(StrEnum):
    """The existing crew responsible for a revision target."""

    PRODUCT_PLANNING = "product_planning"
    TECHNICAL_PLANNING = "technical_planning"


PRODUCT_REVISION_TARGETS = frozenset(
    {
        RevisionTarget.PRODUCT_DEFINITION,
        RevisionTarget.REQUIREMENTS,
        RevisionTarget.MARKET_AND_GTM,
    }
)
TECHNICAL_REVISION_TARGETS = frozenset(
    {
        RevisionTarget.SOLUTION_ARCHITECTURE,
        RevisionTarget.AI_ARCHITECTURE,
        RevisionTarget.SECURITY_ARCHITECTURE,
        RevisionTarget.QA_AND_EVALUATION,
    }
)
COST_REVISION_TARGETS = frozenset({RevisionTarget.COST_SUMMARY})

_TARGET_SPECIALIST = {
    RevisionTarget.SOLUTION_ARCHITECTURE: SpecialistType.SOLUTION_ARCHITECTURE,
    RevisionTarget.AI_ARCHITECTURE: SpecialistType.AI_ARCHITECTURE,
    RevisionTarget.SECURITY_ARCHITECTURE: SpecialistType.SECURITY_ARCHITECTURE,
    RevisionTarget.QA_AND_EVALUATION: SpecialistType.QA_AND_EVALUATION,
}
_TECHNICAL_ORDER = (
    SpecialistType.SOLUTION_ARCHITECTURE,
    SpecialistType.AI_ARCHITECTURE,
    SpecialistType.SECURITY_ARCHITECTURE,
    SpecialistType.QA_AND_EVALUATION,
)


@dataclass(frozen=True)
class RevisionRoute:
    """Crews and selected technical specialists affected by one review round."""

    product_targets: frozenset[RevisionTarget]
    technical_targets: frozenset[RevisionTarget]
    technical_specialists: tuple[SpecialistType, ...]
    rebuild_cost_summary: bool

    @property
    def crews(self) -> frozenset[RevisionCrew]:
        crews: set[RevisionCrew] = set()
        if self.product_targets:
            crews.add(RevisionCrew.PRODUCT_PLANNING)
        if self.technical_targets:
            crews.add(RevisionCrew.TECHNICAL_PLANNING)
        return frozenset(crews)


def route_targeted_revision(
    *,
    state: BuildWiseFlowState,
    requests: list[RevisionRequest],
) -> RevisionRoute:
    """Build a revision route and enforce the Flow's revision-round limit."""

    if not requests:
        raise ValueError("A targeted revision requires at least one revision request.")
    if state.revision_count >= state.limits.maximum_specialist_revisions:
        raise ValueError("The maximum number of specialist revisions was exceeded.")

    targets = {request.target for request in requests}
    supported = PRODUCT_REVISION_TARGETS | TECHNICAL_REVISION_TARGETS | COST_REVISION_TARGETS
    unsupported = targets.difference(supported)
    if unsupported:
        formatted = ", ".join(sorted(target.value for target in unsupported))
        raise ValueError(f"Unsupported revision targets: {formatted}.")

    technical_targets = targets.intersection(TECHNICAL_REVISION_TARGETS)
    selected = set(state.selected_specialists)
    unselected_targets = {
        target for target in technical_targets if _TARGET_SPECIALIST[target] not in selected
    }
    if unselected_targets:
        formatted = ", ".join(sorted(target.value for target in unselected_targets))
        raise ValueError(f"Revision targets were not selected for this Flow: {formatted}.")

    affected: set[SpecialistType] = set()
    for target in technical_targets:
        first = _TECHNICAL_ORDER.index(_TARGET_SPECIALIST[target])
        affected.update(
            specialist for specialist in _TECHNICAL_ORDER[first:] if specialist in selected
        )

    return RevisionRoute(
        product_targets=frozenset(targets.intersection(PRODUCT_REVISION_TARGETS)),
        technical_targets=frozenset(technical_targets),
        technical_specialists=tuple(
            specialist for specialist in _TECHNICAL_ORDER if specialist in affected
        ),
        rebuild_cost_summary=RevisionTarget.COST_SUMMARY in targets,
    )
