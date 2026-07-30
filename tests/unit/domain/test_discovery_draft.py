from __future__ import annotations

import json

from openai.lib._pydantic import to_strict_json_schema

from buildwise.domain.common import generate_uuid
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.discovery_draft import (
    CapabilitySignalsDraft,
    ClarificationQuestionDraft,
    ClarificationQuestionSetDraft,
    DiscoveryCompletenessDraft,
    DiscoveryDraft,
    KnownFactDraft,
    UnknownDraft,
    assemble_discovery_result,
)
from buildwise.domain.enums import (
    CapabilityType,
    ConfidenceLevel,
    FactSourceType,
)
from buildwise.domain.intake import ProductIdeaRequest


def _draft(*, blocking: bool = False) -> DiscoveryDraft:
    unknowns = (
        [
            UnknownDraft(
                key="target_market",
                description="The initial target market is not established.",
                reason_missing="The intake does not identify a market.",
                impact_areas=["market"],
                blocking=True,
                can_proceed_with_assumption=False,
                recommended_assumption=None,
            )
        ]
        if blocking
        else []
    )
    questions = (
        ClarificationQuestionSetDraft(
            round_number=1,
            questions=[
                ClarificationQuestionDraft(
                    key="target_market",
                    category="market",
                    question="Which market should the initial product target?",
                    rationale="The market determines the initial product scope.",
                    related_unknown_keys=["target_market"],
                    affected_areas=["market"],
                )
            ],
            summary="The target market must be clarified.",
            blocking=True,
        )
        if blocking
        else None
    )
    return DiscoveryDraft(
        title="Team scheduling assistant",
        summary="A tool that coordinates schedules for distributed teams.",
        problem_interpretation="Distributed teams struggle to coordinate schedules.",
        target_user_interpretation="Team leads and distributed contributors.",
        desired_outcome_interpretation="Reduce scheduling delays and manual coordination.",
        target_users=["team leads", "distributed contributors"],
        desired_outcomes=["Reduce scheduling delays."],
        known_facts=[
            KnownFactDraft(
                key="distributed_teams",
                statement="The product is intended for distributed teams.",
                source_type=FactSourceType.USER_PROVIDED,
                confirmed_by_user=True,
            )
        ],
        unknowns=unknowns,
        completeness=DiscoveryCompletenessDraft(
            score=0.4 if blocking else 0.9,
            missing_categories=["market"] if blocking else [],
            satisfied_categories=["problem", "target_users"],
            rationale="Core intake evidence was assessed.",
        ),
        clarification_questions=questions,
        capability_signals=CapabilitySignalsDraft(
            capabilities=[CapabilityType.STANDARD_SOFTWARE],
            primary_capability=CapabilityType.STANDARD_SOFTWARE,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.9,
            rationale="The request describes conventional application behavior.",
        ),
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.9,
    )


def _idea() -> ProductIdeaRequest:
    return ProductIdeaRequest(
        idea=(
            "Build a scheduling assistant for distributed teams that reduces "
            "manual coordination across time zones."
        )
    )


def test_deterministic_assembly_adds_ownership_provenance_and_derived_fields() -> None:
    session_id = generate_uuid()

    result = assemble_discovery_result(
        _draft(),
        session_id=session_id,
        product_idea=_idea(),
    )

    assert result.session_id == session_id
    assert result.idea_context.validated_idea.session_id == session_id
    assert result.completeness.percentage == 90
    assert result.completeness.is_complete is True
    assert result.completeness.can_continue is True
    assert result.recommended_next_step == "continue_to_product_definition"
    assert result.known_facts[0].source_reference_ids == [result.source_metadata[0].id]
    assert result.capability_classification.classification_source == "hybrid"


def test_deterministic_assembly_links_questions_to_generated_unknown_ids() -> None:
    result = assemble_discovery_result(
        _draft(blocking=True),
        session_id=generate_uuid(),
        product_idea=_idea(),
    )

    assert result.completeness.blocking_unknown_keys == ["target_market"]
    assert result.completeness.clarification_required is True
    assert result.recommended_next_step == "request_clarification"
    assert result.clarification_questions is not None
    assert result.clarification_questions.questions[0].related_unknown_ids == [
        result.unknowns[0].id
    ]


def test_discovery_draft_strict_schema_is_materially_smaller() -> None:
    draft_schema = json.dumps(to_strict_json_schema(DiscoveryDraft))
    result_schema = json.dumps(to_strict_json_schema(DiscoveryResult))

    assert len(draft_schema) < len(result_schema) * 0.7
