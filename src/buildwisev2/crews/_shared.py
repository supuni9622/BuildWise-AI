"""Tiny shared helper reused by every Crew that supports targeted revisions."""

from __future__ import annotations

from buildwisev2.domain.review import RevisionRequest, RevisionTarget


def find_revision(
    requests: list[RevisionRequest] | None,
    target: RevisionTarget,
) -> RevisionRequest | None:
    """Return the revision request owned by ``target``, if any.

    Each Crew must route a revision request only to the Task that owns it —
    never broadcast it to every Task in the Crew.
    """

    if not requests:
        return None
    for request in requests:
        if request.target == target:
            return request
    return None
