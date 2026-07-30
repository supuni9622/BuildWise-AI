"""Tests for the compact context projections used to keep specialist prompts small."""

from __future__ import annotations

from buildwise.planning.specialist_context import DiscoveryProjection, context_size_reduction
from fixtures.planning import build_discovery_result


def test_discovery_projection_drops_routing_metadata_kept_by_the_full_artifact() -> None:
    discovery = build_discovery_result()

    projection = DiscoveryProjection.from_artifact(discovery)

    assert "id" not in DiscoveryProjection.model_fields
    assert "session_id" not in DiscoveryProjection.model_fields
    assert "source_metadata" not in DiscoveryProjection.model_fields
    assert "discovered_at" not in DiscoveryProjection.model_fields
    assert "completeness" not in DiscoveryProjection.model_fields
    assert "recommended_next_step" not in DiscoveryProjection.model_fields

    assert projection.summary == discovery.summary
    assert projection.capability_classification == discovery.capability_classification
    assert [fact.id for fact in projection.known_facts] == [
        fact.id for fact in discovery.known_facts
    ]


def test_discovery_projection_is_not_larger_than_the_full_artifact() -> None:
    discovery = build_discovery_result()

    full_chars, projected_chars = context_size_reduction(
        [discovery], DiscoveryProjection.from_artifact(discovery)
    )

    assert projected_chars <= full_chars
