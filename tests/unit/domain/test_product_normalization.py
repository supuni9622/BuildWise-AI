from uuid import uuid4

import pytest
from pydantic import ValidationError

from buildwise.domain.enums import RiskLikelihood, RiskSeverity
from buildwise.domain.product import ProductDefinition, ProductRisk
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
