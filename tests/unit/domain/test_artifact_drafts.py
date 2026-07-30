import json

from openai.lib._pydantic import to_strict_json_schema

from buildwise.domain.artifact_drafts import (
    ProductDefinitionDraft,
    RequirementsSpecificationDraft,
    assemble_product_definition,
    assemble_requirements_specification,
)
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from fixtures.planning import build_product_planning_inputs


def test_product_and_requirements_drafts_assemble_authoritative_ownership() -> None:
    discovery, planning = build_product_planning_inputs()
    product_payload = planning.product_definition.model_dump(
        exclude={
            "id",
            "session_id",
            "discovery_result_id",
            "source_metadata",
            "generated_at",
        }
    )
    product = assemble_product_definition(
        ProductDefinitionDraft.model_validate(product_payload),
        discovery=discovery,
    )
    requirements_payload = planning.requirements.model_dump(
        exclude={
            "id",
            "session_id",
            "product_definition_id",
            "source_metadata",
            "generated_at",
            "updated_at",
        }
    )
    # Preserve the canonical nested references while rebinding their owner.
    requirements_payload = _replace_uuid(
        requirements_payload,
        old=str(planning.product_definition.id),
        new=str(product.id),
    )
    requirements = assemble_requirements_specification(
        RequirementsSpecificationDraft.model_validate(requirements_payload),
        product_definition=product,
    )

    assert product.session_id == discovery.session_id
    assert product.discovery_result_id == discovery.id
    assert requirements.session_id == product.session_id
    assert requirements.product_definition_id == product.id


def test_operational_metadata_is_absent_and_schemas_are_smaller() -> None:
    product_properties = to_strict_json_schema(ProductDefinitionDraft)["properties"]
    requirements_properties = to_strict_json_schema(RequirementsSpecificationDraft)[
        "properties"
    ]

    assert "session_id" not in product_properties
    assert "discovery_result_id" not in product_properties
    assert "generated_at" not in product_properties
    assert "product_definition_id" not in requirements_properties
    assert len(json.dumps(to_strict_json_schema(ProductDefinitionDraft))) < len(
        json.dumps(to_strict_json_schema(ProductDefinition))
    )
    assert len(
        json.dumps(to_strict_json_schema(RequirementsSpecificationDraft))
    ) < len(json.dumps(to_strict_json_schema(RequirementsSpecification)))


def _replace_uuid(value: object, *, old: str, new: str) -> object:
    if isinstance(value, dict):
        return {
            key: _replace_uuid(item, old=old, new=new)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_uuid(item, old=old, new=new) for item in value]
    return new if str(value) == old else value
