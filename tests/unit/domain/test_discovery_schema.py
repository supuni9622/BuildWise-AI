from __future__ import annotations

import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from buildwise.domain.discovery import (
    CapabilityClassification,
    DiscoveryRefinement,
    DiscoveryResult,
)
from buildwise.domain.enums import CapabilityType, ConfidenceLevel
from buildwise.domain.intake import ProductIdeaContext


def test_discovery_schema_avoids_unsupported_property_names() -> None:
    schema = to_strict_json_schema(DiscoveryResult)

    assert "propertyNames" not in str(schema)
    assert not _contains_format(schema, "uri")
    assert not _contains_typed_additional_properties(schema)
    assert _strict_objects_are_complete(schema)


def test_discovery_schema_explains_unknown_cross_field_rules() -> None:
    schema = to_strict_json_schema(DiscoveryResult)
    known_fact_schema = schema["$defs"]["KnownFact"]["properties"]
    unknown_schema = schema["$defs"]["Unknown"]["properties"]
    completeness_schema = schema["$defs"]["CompletenessResult"]["properties"]
    question_schema = schema["$defs"]["ClarificationQuestion"]["properties"]

    assert (
        "must be non-empty"
        in known_fact_schema["source_reference_ids"]["description"].lower()
    )
    assert "must be null" in unknown_schema["recommended_assumption"]["description"]
    assert "can_continue=false" in completeness_schema["blocking_unknown_keys"]["description"]
    assert "empty list" in question_schema["options"]["description"]


def test_unknown_specialist_signals_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        CapabilityClassification(
            capabilities=[CapabilityType.STANDARD_SOFTWARE],
            primary_capability=CapabilityType.STANDARD_SOFTWARE,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.9,
            rationale="The request describes a conventional software product.",
            specialist_signals={"invalid_signal": True},
        )


def test_capability_signals_are_normalized_before_cross_field_validation() -> None:
    classification = CapabilityClassification.model_validate(
        {
            "capabilities": [CapabilityType.AI_CORE],
            "primary_capability": CapabilityType.AI_CORE,
            "confidence": ConfidenceLevel.HIGH,
            "confidence_score": 0.9,
            "rationale": "The product uses AI with retrieval and workflow agents.",
            "rag_required": True,
            "agents_required": True,
        }
    )

    assert classification.capabilities == [
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    ]
    assert classification.ai_required is True


def test_primary_capability_is_added_when_provider_omits_it_from_capabilities() -> None:
    classification = CapabilityClassification.model_validate(
        {
            "capabilities": [CapabilityType.STANDARD_SOFTWARE],
            "primary_capability": CapabilityType.ANALYTICS,
            "confidence": ConfidenceLevel.MEDIUM,
            "confidence_score": 0.7,
            "rationale": "Analytics is the primary capability.",
        }
    )

    assert classification.capabilities == [
        CapabilityType.STANDARD_SOFTWARE,
        CapabilityType.ANALYTICS,
    ]


def test_resolved_context_keys_remain_slug_validated() -> None:
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        ProductIdeaContext.model_validate(
            {
                "session_id": "cf4fca52-e008-4bd5-aa8e-563e9f2f0a83",
                "validated_idea": {},
                "resolved_context": [
                    {"key": "Invalid Context", "value": "A resolved value."}
                ],
            }
        )


def test_refinement_derives_non_blocking_route_before_validation() -> None:
    refinement = DiscoveryRefinement.model_validate(
        {
            "unknowns": [],
            "completeness": {
                "score": 0.6,
                "blocking_unknown_keys": [],
                "non_blocking_unknown_keys": ["deployment_region"],
                "missing_categories": ["technical_constraints"],
                "satisfied_categories": ["problem"],
                "rationale": "The remaining uncertainty is non-blocking.",
            },
            "clarification_questions": {
                "session_id": "cf4fca52-e008-4bd5-aa8e-563e9f2f0a83",
                "round_number": 2,
                "questions": [],
                "summary": "No blocking questions remain.",
                "blocking": False,
            },
            "recommended_next_step": "request_clarification",
            "limitations": ["Deployment region remains an assumption."],
            "confidence": "medium",
            "confidence_score": 0.6,
        }
    )

    assert refinement.clarification_questions is None
    assert refinement.recommended_next_step == "continue_with_limitations"


def test_refinement_without_blockers_or_limitations_continues() -> None:
    refinement = DiscoveryRefinement.model_validate(
        {
            "unknowns": [],
            "completeness": {
                "score": 0.9,
                "blocking_unknown_keys": [],
                "non_blocking_unknown_keys": [],
                "missing_categories": [],
                "satisfied_categories": ["problem"],
                "rationale": "The clarification resolved the blocker.",
            },
            "clarification_questions": None,
            "recommended_next_step": "request_clarification",
            "limitations": [],
            "confidence": "high",
            "confidence_score": 0.9,
        }
    )

    assert refinement.recommended_next_step == "continue_to_product_definition"


def _contains_typed_additional_properties(value: object) -> bool:
    if isinstance(value, dict):
        if isinstance(value.get("additionalProperties"), dict):
            return True
        return any(_contains_typed_additional_properties(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_typed_additional_properties(item) for item in value)
    return False


def _contains_format(value: object, expected: str) -> bool:
    if isinstance(value, dict):
        if value.get("format") == expected:
            return True
        return any(_contains_format(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_format(item, expected) for item in value)
    return False


def _strict_objects_are_complete(value: object) -> bool:
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            if set(value.get("required", [])) != set(properties):
                return False
            if value.get("additionalProperties") is not False:
                return False
        return all(_strict_objects_are_complete(item) for item in value.values())
    if isinstance(value, list):
        return all(_strict_objects_are_complete(item) for item in value)
    return True
