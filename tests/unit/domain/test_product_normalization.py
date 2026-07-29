from uuid import uuid4

import pytest
from pydantic import ValidationError

from buildwise.domain.enums import RiskLikelihood, RiskSeverity
from buildwise.domain.product import (
    ProductDefinition,
    ProductFeature,
    ProductRisk,
)
from fixtures.planning import build_product_planning_inputs


def test_product_definition_normalizes_generated_reference_shapes() -> None:
    _, planning = build_product_planning_inputs()
    payload = planning.product_definition.model_dump(mode="python")

    first_feature = payload["features"][0]
    dependent_feature = dict(first_feature)
    dependent_feature.update(
        {
            "id": uuid4(),
            "name": "Imported transaction review",
            "included_in_mvp": False,
            "dependencies": [],
        }
    )
    payload["features"].append(dependent_feature)
    first_feature["dependencies"] = [
        dependent_feature["name"],
        dependent_feature["name"],
    ]
    payload["mvp_feature_ids"].append(payload["mvp_feature_ids"][0])
    payload["roadmap"][0]["feature_ids"].append(
        payload["roadmap"][0]["feature_ids"][0]
    )

    risk = ProductRisk(
        title="Unconfirmed retention policy",
        description="Retention requirements are not confirmed.",
        category="compliance",
        severity=RiskSeverity.HIGH,
        likelihood=RiskLikelihood.POSSIBLE,
        potential_impact="Storage or compliance design may change.",
        mitigation="Confirm the retention policy before launch.",
    ).model_dump(mode="python")
    risk["acceptance_rationale"] = "The team will monitor this risk."
    payload["risks"] = [risk]

    normalized = ProductDefinition.model_validate(payload)

    assert normalized.features[0].dependencies == [
        normalized.features[1].id
    ]
    assert normalized.mvp_feature_ids == [
        normalized.features[0].id
    ]
    assert normalized.roadmap[0].feature_ids == [
        normalized.features[0].id
    ]
    assert normalized.risks[0].acceptance_rationale is None


def test_product_definition_keeps_unknown_dependency_invalid() -> None:
    _, planning = build_product_planning_inputs()
    payload = planning.product_definition.model_dump(mode="python")
    payload["features"][0]["dependencies"] = ["Unknown feature"]

    with pytest.raises(ValidationError, match="uuid_parsing"):
        ProductDefinition.model_validate(payload)


def test_product_definition_replaces_invalid_generated_ids_consistently() -> None:
    _, planning = build_product_planning_inputs()
    payload = planning.product_definition.model_dump(mode="python")
    invalid_feature_id = "d4e5f6a7-ffff-4cf0-9jg5-6a7b8c9d0e17"
    invalid_roadmap_id = "b8c9d0e1-3333-4a00-9nk9-0e1f2a3b4c21"
    invalid_cost_id = "c9d0e1f2-4444-4000-9ol0-1f2a3b4c5d22"

    payload["features"][0]["id"] = invalid_feature_id
    payload["mvp_feature_ids"] = [invalid_feature_id]
    payload["roadmap"][0]["id"] = invalid_roadmap_id
    payload["roadmap"][0]["feature_ids"] = [invalid_feature_id]

    cost = {
        "id": invalid_cost_id,
        "category": "product",
        "name": "MVP implementation",
        "description": "Directional implementation estimate.",
        "frequency": "one_time",
        "range": {
            "minimum": {"amount": "1000", "currency": "USD"},
            "expected": {"amount": "2000", "currency": "USD"},
            "maximum": {"amount": "3000", "currency": "USD"},
        },
        "assumptions": [],
        "exclusions": [],
        "source_reference_ids": [],
        "confidence": "medium",
    }
    payload["product_cost_estimates"] = [cost]

    normalized = ProductDefinition.model_validate(payload)

    assert normalized.features[0].id == normalized.mvp_feature_ids[0]
    assert normalized.features[0].id == normalized.roadmap[0].feature_ids[0]
    assert str(normalized.features[0].id) != invalid_feature_id
    assert str(normalized.roadmap[0].id) != invalid_roadmap_id
    assert str(normalized.product_cost_estimates[0].id) != invalid_cost_id


def test_excluded_feature_can_omit_persona_and_goal_references() -> None:
    _, planning = build_product_planning_inputs()
    feature = planning.product_definition.features[0].model_dump(mode="python")
    feature.update(
        {
            "status": "excluded",
            "included_in_mvp": False,
            "target_persona_ids": [],
            "supporting_goal_ids": [],
        }
    )

    normalized = ProductFeature.model_validate(feature)

    assert normalized.target_persona_ids == []
    assert normalized.supporting_goal_ids == []
