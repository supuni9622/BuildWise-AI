from __future__ import annotations

import pytest
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from buildwise.domain.discovery import CapabilityClassification, DiscoveryResult
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
