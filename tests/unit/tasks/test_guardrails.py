"""Tests for require_self_consistent_draft.

These cover the failure mode that originally crashed a live consultation:
a schema-valid ``ProductDefinitionDraft`` whose nested ``ProductFeature``
violated a business rule (``ProductFeature.validate_feature_scope``) that
``_draft_model`` intentionally no longer enforces at generation time. The
guardrail is the mechanism that is supposed to catch this before it can
reach unguarded deterministic assembly.
"""

from __future__ import annotations

import uuid

import pytest
from crewai.tasks.task_output import TaskOutput

from buildwise.domain.artifact_drafts import (
    ProductDefinitionDraft,
    RequirementsSpecificationDraft,
    reconcile_product_definition_scope,
    reconcile_requirements_specification_narratives,
)
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.tasks.guardrails import require_self_consistent_draft
from fixtures.planning import build_product_planning_inputs


def _product_definition_guardrail():
    return require_self_consistent_draft(
        ProductDefinitionDraft,
        ProductDefinition,
        reconcile=reconcile_product_definition_scope,
    )


def _product_definition_draft() -> ProductDefinitionDraft:
    _discovery, planning = build_product_planning_inputs()
    payload = planning.product_definition.model_dump(
        exclude={
            "id",
            "session_id",
            "discovery_result_id",
            "source_metadata",
            "generated_at",
            "mvp_feature_ids",
            "out_of_scope_feature_ids",
        }
    )
    return ProductDefinitionDraft.model_validate(payload)


def _as_task_output(pydantic_output: object) -> TaskOutput:
    return TaskOutput(description="d", raw="{}", agent="a", pydantic=pydantic_output)


def test_valid_draft_passes() -> None:
    guardrail = _product_definition_guardrail()

    ok, result = guardrail(_as_task_output(_product_definition_draft()))

    assert ok is True
    assert isinstance(result, TaskOutput)


def test_feature_missing_supporting_goal_is_rejected_with_actionable_feedback() -> None:
    """Reproduces the crash: a non-excluded feature with no supporting goal."""

    draft = _product_definition_draft()
    guardrail = _product_definition_guardrail()

    broken_feature = draft.features[0].model_copy(
        update={"status": "proposed", "supporting_goal_ids": []}
    )
    broken_draft = draft.model_copy(
        update={"features": [broken_feature, *draft.features[1:]]}
    )

    ok, message = guardrail(_as_task_output(broken_draft))

    assert ok is False
    assert "supporting goal" in message


def test_feature_referencing_unknown_persona_is_rejected() -> None:
    """A cross-item reference error the nested model alone cannot see."""

    draft = _product_definition_draft()
    guardrail = _product_definition_guardrail()

    broken_feature = draft.features[0].model_copy(
        update={"target_persona_ids": [uuid.uuid4()]}
    )
    broken_draft = draft.model_copy(
        update={"features": [broken_feature, *draft.features[1:]]}
    )

    ok, message = guardrail(_as_task_output(broken_draft))

    assert ok is False
    assert "unknown personas" in message


def test_excluded_feature_scope_is_derived_not_required_from_the_llm() -> None:
    """Reproduces a live-run failure: an excluded feature that the LLM never
    listed in the (now-removed) mvp_feature_ids/out_of_scope_feature_ids
    top-level lists used to fail guardrail retries twice in a row and crash
    the whole consultation. Those lists no longer exist on the draft at
    all — reconcile_product_definition_scope must derive them from each
    feature's own included_in_mvp/status, so this now passes on the first
    attempt regardless of what the LLM would have put in them."""

    draft = _product_definition_draft()
    guardrail = _product_definition_guardrail()

    # The fixture's only feature is the sole MVP feature; excluding it
    # outright would trip the (unrelated) "at least one MVP feature"
    # constraint, so add a second feature to remain the MVP anchor and
    # flip the original one to excluded — the exact shape of the failure
    # observed in production.
    mvp_feature = draft.features[0].model_copy(
        update={"id": uuid.uuid4(), "name": "Other MVP feature"}
    )
    excluded_feature = draft.features[0].model_copy(
        update={"status": "excluded", "included_in_mvp": False}
    )
    updated_draft = draft.model_copy(
        update={"features": [excluded_feature, mvp_feature]}
    )

    assert not hasattr(updated_draft, "mvp_feature_ids")
    assert not hasattr(updated_draft, "out_of_scope_feature_ids")

    ok, result = guardrail(_as_task_output(updated_draft))

    assert ok is True
    assert isinstance(result, TaskOutput)


def test_non_draft_output_is_left_to_require_pydantic_output() -> None:
    guardrail = _product_definition_guardrail()

    ok, result = guardrail(_as_task_output(None))

    assert ok is True
    assert isinstance(result, TaskOutput)


def test_unmapped_required_placeholder_field_fails_fast() -> None:
    """A future Draft/canonical pair with a non-UUID required omitted field
    must fail loudly at guardrail construction, not silently misbehave."""

    from pydantic import BaseModel

    class _Canonical(BaseModel):
        id: uuid.UUID
        title: str

    class _Draft(BaseModel):
        pass

    with pytest.raises(TypeError):
        require_self_consistent_draft(_Draft, _Canonical)


def _requirements_draft():
    _discovery, planning = build_product_planning_inputs()
    payload = planning.requirements.model_dump(
        exclude={
            "id",
            "session_id",
            "product_definition_id",
            "source_metadata",
            "generated_at",
            "updated_at",
        }
    )
    return RequirementsSpecificationDraft.model_validate(payload)


def _requirements_guardrail():
    return require_self_consistent_draft(
        RequirementsSpecificationDraft,
        RequirementsSpecification,
        reconcile=reconcile_requirements_specification_narratives,
    )


def test_requirements_draft_self_consistency() -> None:
    ok, result = _requirements_guardrail()(_as_task_output(_requirements_draft()))

    assert ok is True
    assert isinstance(result, TaskOutput)


def test_paraphrased_user_story_narrative_is_derived_not_required_from_the_llm() -> None:
    """Reproduces a live-run failure: UserStory.validate_user_story requires
    ``narrative`` to literally contain the casefolded actor/capability/
    benefit text. An LLM naturally paraphrases when composing readable
    prose, so this failed on every retry attempt in production —
    reconcile_requirements_specification_narratives must derive the
    narrative instead of trusting the LLM to match it verbatim."""

    draft = _requirements_draft()
    guardrail = _requirements_guardrail()

    paraphrased_story = draft.user_stories[0].model_copy(
        update={
            "narrative": (
                "Team leads need a fast way to see when everyone is free "
                "so scheduling meetings doesn't turn into a back-and-forth."
            )
        }
    )
    updated_draft = draft.model_copy(
        update={"user_stories": [paraphrased_story, *draft.user_stories[1:]]}
    )

    ok, result = guardrail(_as_task_output(updated_draft))

    assert ok is True
    assert isinstance(result, TaskOutput)
