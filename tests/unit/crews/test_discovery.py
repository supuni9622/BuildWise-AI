from uuid import uuid4

from buildwise.crews.discovery import bind_discovery_session
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
