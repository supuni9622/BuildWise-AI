import json

import pytest
from openai.lib._pydantic import to_strict_json_schema

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.artifact_drafts import (
    AIArchitectureDraft,
    MarketAndGTMStrategyDraft,
    ProductDefinitionDraft,
    RequirementsSpecificationDraft,
    SolutionArchitectureDraft,
    assemble_product_definition,
    assemble_requirements_specification,
)
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from fixtures.planning import build_product_planning_inputs

_DRAFT_CANONICAL_PAIRS = [
    (ProductDefinitionDraft, ProductDefinition),
    (RequirementsSpecificationDraft, RequirementsSpecification),
    (MarketAndGTMStrategyDraft, MarketAndGTMStrategy),
    (SolutionArchitectureDraft, SolutionArchitecture),
    (AIArchitectureDraft, AIArchitecture),
]


def test_product_and_requirements_drafts_assemble_authoritative_ownership() -> None:
    discovery, planning = build_product_planning_inputs()
    product_payload = planning.product_definition.model_dump(
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


@pytest.mark.parametrize("draft_model, canonical_model", _DRAFT_CANONICAL_PAIRS)
def test_every_draft_model_produces_a_valid_strict_schema_smaller_than_canonical(
    draft_model: type,
    canonical_model: type,
) -> None:
    """Regression guard for every ``*Draft`` model, not just Product Definition.

    Confirms the recursive loosening in ``_draft_model`` still produces an
    OpenAI-strict-schema-compatible model (this is exactly the code path
    CrewAI's structured-output call exercises) for every draft, and that it
    stays smaller than its canonical counterpart since operational fields are
    always omitted.
    """

    draft_schema = to_strict_json_schema(draft_model)
    canonical_schema = to_strict_json_schema(canonical_model)

    assert len(json.dumps(draft_schema)) < len(json.dumps(canonical_schema))


def test_nested_business_rule_validator_is_stripped_from_ai_architecture_draft() -> None:
    """AIArchitecture carries 17 model_validators, the highest of any artifact.

    A nested AIGuardrail with an internally-inconsistent retry configuration
    would previously make ``AIArchitectureDraft`` itself unconstructable
    (the exact class of failure that crashed the observed consultation, one
    level deeper). It must now build successfully at the draft level, while
    the canonical ``AIGuardrail`` still rejects the same shape.
    """

    from buildwise.domain.ai_architecture import AIGuardrail

    guardrail_draft_type = AIArchitectureDraft.model_fields["guardrails"].annotation.__args__[0]
    assert guardrail_draft_type is not AIGuardrail

    inconsistent_payload = {
        "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "key": "test-guardrail",
        "name": "Test guardrail",
        "description": "desc",
        "stage": "output",
        "guardrail_type": "schema_validation",
        "trigger_condition": "trigger",
        "validation_method": "deterministic schema check",
        "action": "reject",
        "blocking": True,
        "retry_allowed": True,
        "maximum_retry_attempts": None,  # invalid when retry_allowed=True
        "human_review_required": False,
        "audit_required": True,
    }

    draft_guardrail = guardrail_draft_type.model_validate(inconsistent_payload)
    assert draft_guardrail.maximum_retry_attempts is None

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AIGuardrail.model_validate(inconsistent_payload)


def test_enum_and_literal_fields_are_loosened_to_str_on_the_draft() -> None:
    """Reproduces a live-run failure: the LLM emitted an invalid enum value
    ('business') for ProductFeature.category. OpenAI structured output does
    not reliably enforce enum/Literal membership server-side even though
    it's JSON-Schema-expressible, so an invalid value previously raised a
    raw parse-time ValidationError with zero retries — the same failure
    shape F1 already fixed for business-rule validators. The draft must
    accept any string there now, while the canonical model still enforces
    the real enum.
    """

    from buildwise.domain.product import ProductFeature

    feature_draft_type = ProductDefinitionDraft.model_fields["features"].annotation.__args__[0]
    assert feature_draft_type.model_fields["category"].annotation is str
    assert feature_draft_type.model_fields["status"].annotation is str

    payload = {
        "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "name": "Test",
        "description": "desc",
        "category": "business",  # not a real FeatureCategory value
        "priority": "must_have",
        "status": "proposed",
        "user_value": "value",
        "rationale": "why",
        "included_in_mvp": False,
        "ai_enabled": False,
        "target_persona_ids": [],
        "supporting_goal_ids": [],
    }

    draft_feature = feature_draft_type.model_validate(payload)
    assert draft_feature.category == "business"

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ProductFeature.model_validate(payload)


def _replace_uuid(value: object, *, old: str, new: str) -> object:
    if isinstance(value, dict):
        return {
            key: _replace_uuid(item, old=old, new=new)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_uuid(item, old=old, new=new) for item in value]
    return new if str(value) == old else value
