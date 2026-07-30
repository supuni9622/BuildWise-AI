"""Tests for _validate_discovery_semantic_consistency.

Reproduces a live-run failure: ``discovery_draft.py``'s cross-field
validators were removed from the draft models (they're already re-enforced
on the canonical models at assembly time — see F12 in
docs/reliability_and_latency_remediation.md), but Discovery never got the
guardrail equivalent of F2 to catch a violation with retry feedback before
it reaches unguarded assembly. This guardrail closes that gap.
"""

from __future__ import annotations

from crewai.tasks.task_output import TaskOutput

from buildwise.domain.discovery_draft import (
    AssumptionDraft,
    CapabilitySignalsDraft,
    ClarificationQuestionDraft,
    ClarificationQuestionSetDraft,
    DiscoveryCompletenessDraft,
    DiscoveryDraft,
    KnownFactDraft,
    UnknownDraft,
)
from buildwise.domain.enums import CapabilityType, ConfidenceLevel, FactSourceType
from buildwise.tasks.discovery import _validate_discovery_semantic_consistency


def _base_draft(**overrides: object) -> DiscoveryDraft:
    defaults: dict[str, object] = dict(
        title="Team scheduling assistant",
        summary="A tool that coordinates schedules for distributed teams.",
        problem_interpretation="Distributed teams struggle to coordinate schedules.",
        target_user_interpretation="Team leads and distributed contributors.",
        desired_outcome_interpretation="Reduce scheduling delays and manual coordination.",
        target_users=["team leads"],
        desired_outcomes=["Reduce scheduling delays."],
        known_facts=[
            KnownFactDraft(
                key="distributed_teams",
                statement="The product is intended for distributed teams.",
                source_type=FactSourceType.USER_PROVIDED,
                confirmed_by_user=True,
            )
        ],
        assumptions=[],
        unknowns=[],
        completeness=DiscoveryCompletenessDraft(
            score=0.9,
            satisfied_categories=["problem", "target_users"],
            rationale="Core intake evidence was assessed.",
        ),
        clarification_questions=None,
        capability_signals=CapabilitySignalsDraft(
            capabilities=[CapabilityType.STANDARD_SOFTWARE],
            primary_capability=CapabilityType.STANDARD_SOFTWARE,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.9,
            rationale="Conventional application behavior.",
        ),
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.9,
    )
    defaults.update(overrides)
    return DiscoveryDraft(**defaults)


def _as_task_output(pydantic_output: object) -> TaskOutput:
    return TaskOutput(description="d", raw="{}", agent="a", pydantic=pydantic_output)


def test_valid_draft_passes() -> None:
    ok, result = _validate_discovery_semantic_consistency(_as_task_output(_base_draft()))

    assert ok is True
    assert isinstance(result, TaskOutput)


def test_assumption_missing_validation_question_is_rejected() -> None:
    """Reproduces the live crash: requires_validation=True with no question."""

    draft = _base_draft(
        assumptions=[
            AssumptionDraft(
                key="pricing",
                statement="Pricing model is not yet decided.",
                rationale="No pricing signal in the intake.",
                requires_validation=True,
                validation_question=None,
            )
        ]
    )

    ok, message = _validate_discovery_semantic_consistency(_as_task_output(draft))

    assert ok is False
    assert "validation_question" in message


def test_unknown_missing_recommended_assumption_is_rejected() -> None:
    draft = _base_draft(
        unknowns=[
            UnknownDraft(
                key="target_market",
                description="Target market is not established.",
                reason_missing="Not stated in the intake.",
                impact_areas=["market"],
                can_proceed_with_assumption=True,
                recommended_assumption=None,
            )
        ]
    )

    ok, message = _validate_discovery_semantic_consistency(_as_task_output(draft))

    assert ok is False
    assert "recommended_assumption" in message


def test_clarification_question_referencing_missing_unknown_key_is_rejected() -> None:
    draft = _base_draft(
        unknowns=[
            UnknownDraft(
                key="target_market",
                description="Target market is not established.",
                reason_missing="Not stated in the intake.",
                impact_areas=["market"],
                blocking=True,
                can_proceed_with_assumption=False,
                recommended_assumption=None,
            )
        ],
        clarification_questions=ClarificationQuestionSetDraft(
            round_number=1,
            questions=[
                ClarificationQuestionDraft(
                    key="q1",
                    category="market",
                    question="Which market?",
                    rationale="Needed for scope.",
                    related_unknown_keys=["nonexistent_key"],
                )
            ],
            summary="Market must be clarified.",
            blocking=True,
        ),
    )

    ok, message = _validate_discovery_semantic_consistency(_as_task_output(draft))

    assert ok is False
    assert "nonexistent_key" in message


def test_non_draft_output_is_left_to_require_pydantic_output() -> None:
    ok, result = _validate_discovery_semantic_consistency(_as_task_output(None))

    assert ok is True
    assert isinstance(result, TaskOutput)
