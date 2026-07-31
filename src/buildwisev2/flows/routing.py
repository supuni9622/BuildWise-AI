"""Pure routing decision helpers for the Consulting Flow.

No CrewAI imports here on purpose: these are ordinary functions of
structured domain state, testable without constructing a Flow.
"""

from __future__ import annotations

from enum import StrEnum

from buildwisev2.domain.common import FlowRuntimeLimits
from buildwisev2.domain.discovery import DiscoveryDecision, DiscoveryResult
from buildwisev2.domain.review import LeadReview, ReviewDecision, RevisionRequest, RevisionTarget

_PRODUCT_PLANNING_TARGETS = {
    RevisionTarget.PRODUCT_DEFINITION,
    RevisionTarget.REQUIREMENTS,
    RevisionTarget.MARKET_AND_GTM,
}
_TECHNICAL_PLANNING_TARGETS = {
    RevisionTarget.SOLUTION_ARCHITECTURE,
    RevisionTarget.AI_ARCHITECTURE,
    RevisionTarget.SECURITY_ARCHITECTURE,
    RevisionTarget.QA_EVALUATION,
}


class DiscoveryRoute(StrEnum):
    CONTINUE = "continue"
    CLARIFY = "clarify"
    FAIL = "fail"


def route_discovery(
    discovery: DiscoveryResult,
    *,
    clarification_round: int,
    limits: FlowRuntimeLimits,
) -> DiscoveryRoute:
    """Decide what the Flow does after Discovery completes.

    A clarification-required decision only pauses the Flow while rounds
    remain; once the round budget is exhausted the Flow proceeds with
    whatever limitations Discovery has already recorded rather than
    looping forever. Callers that get ``CONTINUE`` back while
    ``discovery.completeness.can_continue`` is still ``False`` must call
    ``force_continue_discovery`` before handing the artifact downstream —
    see that function's docstring for why.
    """

    if discovery.decision == DiscoveryDecision.FAILED:
        return DiscoveryRoute.FAIL
    if discovery.decision == DiscoveryDecision.CLARIFICATION_REQUIRED:
        if clarification_round >= limits.maximum_clarification_rounds:
            return DiscoveryRoute.CONTINUE
        return DiscoveryRoute.CLARIFY
    return DiscoveryRoute.CONTINUE


def force_continue_discovery(discovery: DiscoveryResult) -> DiscoveryResult:
    """Reconcile a ``DiscoveryResult`` with the Flow's decision to proceed
    anyway after exhausting the clarification-round budget.

    ``route_discovery`` can return ``CONTINUE`` even when Discovery itself
    still reports ``completeness.can_continue=False`` (round budget
    exhausted while still asking for clarification). Downstream components
    — the deterministic planner in particular — treat
    ``completeness.can_continue=False`` as a hard precondition failure and
    will raise rather than silently proceeding on an artifact that still
    claims to be incomplete. This function makes the artifact honestly
    reflect the Flow's decision instead of leaving that contradiction in
    place: it flips ``completeness.can_continue`` to ``True``, records why
    under a ``CONTINUE_WITH_LIMITATIONS`` decision, and appends a
    limitation noting the unresolved unknowns were not actually resolved.

    Returns ``discovery`` unchanged when it already reports
    ``can_continue=True`` (the common case).
    """

    if discovery.completeness.can_continue:
        return discovery
    return discovery.model_copy(
        update={
            "completeness": discovery.completeness.model_copy(update={"can_continue": True}),
            "decision": DiscoveryDecision.CONTINUE_WITH_LIMITATIONS,
            "limitations": [
                *discovery.limitations,
                "The maximum number of clarification rounds was reached before Discovery "
                "reported full completeness. The consultation proceeded with the "
                "outstanding unknowns recorded above rather than pausing indefinitely.",
            ],
        }
    )


class ReviewRoute(StrEnum):
    ASSEMBLE_BLUEPRINT = "assemble_blueprint"
    REVISE = "revise"
    REJECT = "reject"
    """Distinct from ``DiscoveryRoute.FAIL`` ("fail") so a single Flow can
    ``@listen`` to each independently without one handler firing for both."""


def route_lead_review(
    review: LeadReview,
    *,
    revision_count: int,
    limits: FlowRuntimeLimits,
) -> ReviewRoute:
    """Decide what the Flow does after Lead Review completes.

    Once the revision budget is exhausted, a REVISION_REQUIRED decision is
    treated as "complete with limitations" rather than looping forever —
    the Flow still assembles the blueprint but the caller should record
    the outstanding revision requests as limitations.
    """

    if review.decision in (ReviewDecision.APPROVED, ReviewDecision.APPROVED_WITH_LIMITATIONS):
        return ReviewRoute.ASSEMBLE_BLUEPRINT
    if review.decision == ReviewDecision.REJECTED:
        return ReviewRoute.REJECT
    if revision_count >= limits.maximum_specialist_revisions:
        return ReviewRoute.ASSEMBLE_BLUEPRINT
    return ReviewRoute.REVISE


def group_revisions_by_crew(
    requests: list[RevisionRequest],
) -> tuple[list[RevisionRequest], list[RevisionRequest]]:
    """Split bounded revision requests by which Crew owns each target.

    Returns ``(product_planning_requests, technical_planning_requests)``.
    A request whose target belongs to neither group is impossible given
    the closed ``RevisionTarget`` enum, aside from ``DISCOVERY`` — Discovery
    revisions are not supported by targeted re-runs and are surfaced as a
    warning by the caller instead of silently dropped.
    """

    product_requests = [r for r in requests if r.target in _PRODUCT_PLANNING_TARGETS]
    technical_requests = [r for r in requests if r.target in _TECHNICAL_PLANNING_TARGETS]
    return product_requests, technical_requests
