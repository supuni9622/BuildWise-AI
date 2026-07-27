from uuid import uuid4

from buildwise.crews.discovery import (
    bind_discovery_session,
    merge_discovery_refinement,
)
from buildwise.domain.discovery import (
    DiscoveryCompletenessRefinement,
    DiscoveryRefinement,
)
from fixtures.planning import build_discovery_result


def test_bind_discovery_session_replaces_all_owned_session_ids() -> None:
    result = build_discovery_result()
    session_id = uuid4()

    bound = bind_discovery_session(result, session_id=session_id)

    assert bound.session_id == session_id
    assert bound.idea_context.session_id == session_id
    assert bound.idea_context.validated_idea.session_id == session_id
    if bound.clarification_questions is not None:
        assert bound.clarification_questions.session_id == session_id


def test_merge_discovery_refinement_preserves_accepted_sections() -> None:
    previous = build_discovery_result()
    refinement = DiscoveryRefinement(
        unknowns=previous.unknowns,
        completeness=DiscoveryCompletenessRefinement.from_result(
            previous.completeness
        ),
        clarification_questions=previous.clarification_questions,
        recommended_next_step=previous.recommended_next_step,
        limitations=previous.limitations,
        confidence=previous.confidence,
        confidence_score=previous.confidence_score,
    )

    merged = merge_discovery_refinement(
        previous,
        previous.idea_context,
        refinement,
        session_id=previous.session_id,
    )

    assert merged.known_facts == previous.known_facts
    assert merged.risks == previous.risks
    assert merged.capability_classification == previous.capability_classification
