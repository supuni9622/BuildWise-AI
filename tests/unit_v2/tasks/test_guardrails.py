"""Unit tests for deterministic task guardrails. No LLM calls."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from buildwisev2.domain.discovery import (
    CapabilityClassification,
    CompletenessAssessment,
    DiscoveryDecision,
    DiscoveryResult,
)
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.tasks.guardrails import (
    require_artifact_session,
    require_non_empty,
    require_pydantic_output,
)


def _fake_result(pydantic=None):
    return SimpleNamespace(pydantic=pydantic)


def _discovery(session_id) -> DiscoveryResult:
    return DiscoveryResult(
        session_id=session_id,
        interpreted_idea="idea",
        capability_classification=CapabilityClassification(),
        completeness=CompletenessAssessment(can_continue=True, completeness_score=0.9),
        decision=DiscoveryDecision.CONTINUE,
        confidence=0.7,
    )


def test_require_pydantic_output_accepts_matching_model() -> None:
    guardrail = require_pydantic_output(DiscoveryResult)
    discovery = _discovery(uuid4())

    ok, value = guardrail(_fake_result(discovery))

    assert ok is True
    assert value is discovery


def test_require_pydantic_output_rejects_missing_output() -> None:
    guardrail = require_pydantic_output(DiscoveryResult)

    ok, feedback = guardrail(_fake_result(None))

    assert ok is False
    assert "DiscoveryResult" in feedback


def test_require_pydantic_output_rejects_wrong_model() -> None:
    guardrail = require_pydantic_output(DiscoveryResult)
    wrong = ProductDefinition(
        session_id=uuid4(),
        vision="v",
        value_proposition="vp",
        goals=[],
        personas=[],
        features=[],
        mvp_feature_ids=[],
        decision="approved",
    )

    ok, feedback = guardrail(_fake_result(wrong))

    assert ok is False
    assert "ProductDefinition" in feedback


def test_require_artifact_session_matches() -> None:
    session_id = uuid4()
    guardrail = require_artifact_session(session_id)
    discovery = _discovery(session_id)

    ok, value = guardrail(_fake_result(discovery))

    assert ok is True
    assert value is discovery


def test_require_artifact_session_rejects_mismatch() -> None:
    guardrail = require_artifact_session(uuid4())
    discovery = _discovery(uuid4())

    ok, feedback = guardrail(_fake_result(discovery))

    assert ok is False
    assert "session_id" in feedback


def test_require_non_empty_rejects_empty_field() -> None:
    guardrail = require_non_empty("known_facts", DiscoveryResult)
    discovery = _discovery(uuid4())
    assert discovery.known_facts == []

    ok, feedback = guardrail(_fake_result(discovery))

    assert ok is False
    assert "known_facts" in feedback


def test_require_non_empty_accepts_populated_field() -> None:
    guardrail = require_non_empty("known_facts", DiscoveryResult)
    discovery = _discovery(uuid4())
    discovery.known_facts = ["fact one"]

    ok, value = guardrail(_fake_result(discovery))

    assert ok is True
    assert value is discovery
