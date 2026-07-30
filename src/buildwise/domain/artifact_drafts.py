"""Compact top-level generation contracts for canonical planning artifacts.

Nested semantic structures are rebuilt into generation-safe twins that drop
every constraint an LLM cannot be reliably held to during generation:
custom Python-level ``model_validator``/cross-field ``field_validator``
business rules (for example "a non-excluded feature requires a supporting
goal", which cannot be enforced through OpenAI structured-output JSON
Schema at all), format constraints OpenAI's structured output does not
reliably enforce server-side even though they are technically
JSON-Schema-expressible (closed value sets — ``Enum``/``Literal`` fields —
and UUID format on ``ArtifactId`` fields), still reinforced via
task-description instructions (``IDENTIFIER_RULES``) since the type
constraint alone was also generation guidance the model could see.
Holding the LLM to either during generation only produces a
``ValidationError`` that CrewAI treats as a raw provider failure rather than
a correctable guardrail failure — string length/pattern constraints and
numeric bounds do not have this problem and are kept as-is. The full
business rules and closed-value-set/UUID-format checks still run once,
deterministically (and retryably, via `require_self_consistent_draft`),
when ``assemble_*`` builds the canonical model out of the draft. Ownership
identifiers, timestamps, and source metadata are injected at that same
point.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from functools import reduce
from operator import or_
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin
from uuid import UUID

from pydantic import BaseModel, create_model

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.common import BuildWiseModel, generate_uuid
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification

_COMMON_OPERATIONAL_FIELDS = {
    "id",
    "session_id",
    "source_metadata",
    "generated_at",
    "updated_at",
}

_CONTAINER_ORIGINS = (list, set, frozenset)


def _closed_value_hint(annotation: Any) -> str | None:
    """Describe an Enum/Literal's allowed values, for use once the field's
    own type constraint is loosened away.

    The JSON Schema `enum` keyword this constraint used to compile to was
    also visible to the model as generation guidance, not just a server-side
    constraint. Losing the type constraint (see `_loosen_type`) would
    silently lose that guidance too if it isn't preserved somewhere the
    model still sees — a plain `description` string.
    """

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        values = ", ".join(repr(member.value) for member in annotation)
        return f"Must be one of: {values}."

    if get_origin(annotation) is Literal:
        values = ", ".join(repr(value) for value in get_args(annotation))
        return f"Must be one of: {values}."

    return None


def _loosen_field(
    field: Any,
    cache: dict[type[BaseModel], type[BaseModel]],
) -> tuple[Any, Any]:
    """Loosen one field's type and return the ``(annotation, FieldInfo)`` pair.

    ``create_model`` reads the annotation from the first tuple element, not
    from ``FieldInfo.annotation`` — both are set here for consistency.
    """

    loosened_annotation = _loosen_type(field.annotation, cache)
    loosened_field = deepcopy(field)
    loosened_field.annotation = loosened_annotation

    hint = _closed_value_hint(field.annotation)
    if hint is not None:
        loosened_field.description = (
            f"{loosened_field.description} {hint}" if loosened_field.description else hint
        )

    return loosened_annotation, loosened_field


def _loosen_model(
    canonical: type[BaseModel],
    cache: dict[type[BaseModel], type[BaseModel]],
) -> type[BaseModel]:
    """Rebuild ``canonical`` (and everything it references) validator-free.

    ``create_model`` does not inherit from ``canonical``, so none of its
    ``@field_validator``/``@model_validator`` methods carry over. Every
    nested ``BaseModel`` field is recursively rebuilt the same way, so a
    business-rule validator buried several levels deep (for example on a
    ``ProductFeature`` nested inside ``ProductDefinition.features``) cannot
    reject a generation attempt either.
    """

    if canonical in cache:
        return cache[canonical]

    fields: dict[str, Any] = {}
    for field_name, field in canonical.model_fields.items():
        fields[field_name] = _loosen_field(field, cache)

    loosened_model = create_model(
        f"{canonical.__name__}Draft",
        __base__=BuildWiseModel,
        **fields,
    )
    cache[canonical] = loosened_model
    return loosened_model


def _loosen_type(
    annotation: Any,
    cache: dict[type[BaseModel], type[BaseModel]],
) -> Any:
    """Recursively rebuild any nested ``BaseModel``/``Enum``/``Literal``/``UUID`` type.

    ``Annotated`` constrained scalar types (``ShortText``, ``Slug``, and
    similar string length/pattern constraints) pass through unchanged —
    those are genuinely JSON-Schema-expressible and OpenAI's structured
    output honors them. ``Enum``, ``Literal``, and ``UUID`` (``ArtifactId``)
    fields are loosened to plain ``str`` instead, even though each is
    technically expressible in JSON Schema too: in practice OpenAI's
    structured output does not reliably enforce either server-side, so an
    invalid value still raises a raw parse-time ``ValidationError`` that
    bypasses the guardrail retry loop entirely — reproduced live with a
    `category` enum field (a wrong-but-plausible value) and, separately,
    with a malformed UUID one hex character short on a nested `risks.N.id`
    field (a typo, not a format the model was never told to use — unlike
    the slug-instead-of-UUID case ``IDENTIFIER_RULES`` already covers).
    Loosening either type here means the failure now surfaces through
    `require_self_consistent_draft` instead (F2's guardrail, which already
    re-validates every draft against the canonical model, where every
    ``ArtifactId`` field is still strictly ``UUID``-typed), giving the LLM a
    retry with feedback instead of a hard crash. Every ``ArtifactId``
    occurrence loosens the same way — including list-of-reference fields
    like ``mvp_feature_ids`` — so a cross-reference match is still a plain
    string comparison either way; nothing about matching references to each
    other depends on the Python-level type annotation.
    """

    if annotation is UUID:
        return str

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _loosen_model(annotation, cache)

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return str

    origin = get_origin(annotation)

    if origin is Literal:
        return str

    if origin in _CONTAINER_ORIGINS:
        (item_type,) = get_args(annotation)
        return origin[_loosen_type(item_type, cache)]

    if origin is tuple:
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple[_loosen_type(args[0], cache), ...]  # type: ignore[misc]
        return tuple[tuple(_loosen_type(arg, cache) for arg in args)]  # type: ignore[misc]

    if origin is dict:
        key_type, value_type = get_args(annotation)
        return dict[key_type, _loosen_type(value_type, cache)]  # type: ignore[misc,valid-type]

    if origin is Union or origin is UnionType:
        loosened_args = (_loosen_type(arg, cache) for arg in get_args(annotation))
        return reduce(or_, loosened_args)

    return annotation


def _draft_model(
    name: str,
    canonical: type[BaseModel],
    *,
    omit: set[str],
) -> type[BuildWiseModel]:
    cache: dict[type[BaseModel], type[BaseModel]] = {}
    fields: dict[str, Any] = {}
    for field_name, field in canonical.model_fields.items():
        if field_name in omit:
            continue
        fields[field_name] = _loosen_field(field, cache)
    return create_model(name, __base__=BuildWiseModel, **fields)


ProductDefinitionDraft = _draft_model(
    "ProductDefinitionDraft",
    ProductDefinition,
    # mvp_feature_ids/out_of_scope_feature_ids are omitted because they are
    # redundant with each feature's own included_in_mvp/status field.
    # reconcile_product_definition_scope() derives them deterministically,
    # so asking the LLM to also keep a top-level list in sync only adds a
    # cross-list bookkeeping task it reliably drops under load.
    omit=_COMMON_OPERATIONAL_FIELDS
    | {"discovery_result_id", "mvp_feature_ids", "out_of_scope_feature_ids"},
)
RequirementsSpecificationDraft = _draft_model(
    "RequirementsSpecificationDraft",
    RequirementsSpecification,
    omit=_COMMON_OPERATIONAL_FIELDS | {"product_definition_id"},
)
MarketAndGTMStrategyDraft = _draft_model(
    "MarketAndGTMStrategyDraft",
    MarketAndGTMStrategy,
    omit=_COMMON_OPERATIONAL_FIELDS | {"product_definition_id"},
)
SolutionArchitectureDraft = _draft_model(
    "SolutionArchitectureDraft",
    SolutionArchitecture,
    omit=_COMMON_OPERATIONAL_FIELDS | {"requirements_specification_id"},
)
AIArchitectureDraft = _draft_model(
    "AIArchitectureDraft",
    AIArchitecture,
    omit=_COMMON_OPERATIONAL_FIELDS | {"requirements_specification_id", "solution_architecture_id"},
)


def reconcile_product_definition_scope(payload: dict[str, Any]) -> dict[str, Any]:
    """Derive MVP/out-of-scope feature lists from each feature's own fields.

    ``ProductDefinition.validate_product_definition`` requires
    ``mvp_feature_ids``/``out_of_scope_feature_ids`` (top-level lists) to
    agree with each feature's own ``included_in_mvp``/``status`` fields.
    Asking an LLM to keep two redundant signals in sync across dozens of
    features is exactly the kind of cross-list bookkeeping it reliably
    drops under load — in practice this was the single most common
    self-consistency guardrail failure. Deriving the lists here instead
    makes them agree by construction, eliminating the failure mode rather
    than just retrying it.
    """

    features = payload.get("features") or []
    return {
        **payload,
        "mvp_feature_ids": [
            feature["id"] for feature in features if feature.get("included_in_mvp")
        ],
        "out_of_scope_feature_ids": [
            feature["id"] for feature in features if feature.get("status") == "excluded"
        ],
    }


def reconcile_requirements_specification_narratives(payload: dict[str, Any]) -> dict[str, Any]:
    """Derive each user story's narrative from its actor/capability/benefit.

    ``UserStory.validate_user_story`` requires ``narrative`` to literally
    contain the casefolded ``actor``, ``capability``, and ``benefit`` text.
    Asking an LLM to separately hand-author a narrative that verbatim-matches
    three other fields fights against how language models naturally compose
    readable prose — they paraphrase — so this was, in practice, the most
    persistent self-consistency guardrail failure observed (it survived
    every retry, not just some). Deriving the narrative here instead makes
    it agree by construction.
    """

    user_stories = payload.get("user_stories") or []
    return {
        **payload,
        "user_stories": [
            {
                **story,
                "narrative": (
                    f"As a {story['actor']}, I want {story['capability']}, "
                    f"so that {story['benefit']}."
                ),
            }
            for story in user_stories
        ],
    }


def assemble_product_definition(
    draft: BuildWiseModel,
    *,
    discovery: DiscoveryResult,
) -> ProductDefinition:
    result = ProductDefinition.model_validate(
        {
            **reconcile_product_definition_scope(draft.model_dump(mode="python")),
            "id": generate_uuid(),
            "session_id": discovery.session_id,
            "discovery_result_id": discovery.id,
            "source_metadata": discovery.source_metadata,
        }
    )
    ProductDefinition.validate_discovery_ownership(
        product_definition=result,
        discovery_result=discovery,
    )
    return result


def assemble_requirements_specification(
    draft: BuildWiseModel,
    *,
    product_definition: ProductDefinition,
) -> RequirementsSpecification:
    result = RequirementsSpecification.model_validate(
        {
            **reconcile_requirements_specification_narratives(draft.model_dump(mode="python")),
            "id": generate_uuid(),
            "session_id": product_definition.session_id,
            "product_definition_id": product_definition.id,
            "source_metadata": product_definition.source_metadata,
        }
    )
    RequirementsSpecification.validate_product_ownership(
        requirements_specification=result,
        product_definition=product_definition,
    )
    return result


def assemble_market_and_gtm_strategy(
    draft: BuildWiseModel,
    *,
    product_definition: ProductDefinition,
) -> MarketAndGTMStrategy:
    result = MarketAndGTMStrategy.model_validate(
        {
            **draft.model_dump(mode="python"),
            "id": generate_uuid(),
            "session_id": product_definition.session_id,
            "product_definition_id": product_definition.id,
            "source_metadata": product_definition.source_metadata,
        }
    )
    MarketAndGTMStrategy.validate_product_ownership(
        market_and_gtm_strategy=result,
        product_definition=product_definition,
    )
    return result


def assemble_solution_architecture(
    draft: BuildWiseModel,
    *,
    requirements: RequirementsSpecification,
) -> SolutionArchitecture:
    result = SolutionArchitecture.model_validate(
        {
            **draft.model_dump(mode="python"),
            "id": generate_uuid(),
            "session_id": requirements.session_id,
            "requirements_specification_id": requirements.id,
            "source_metadata": requirements.source_metadata,
        }
    )
    SolutionArchitecture.validate_requirements_ownership(
        solution_architecture=result,
        requirements_specification=requirements,
    )
    return result


def assemble_ai_architecture(
    draft: BuildWiseModel,
    *,
    requirements: RequirementsSpecification,
    solution: SolutionArchitecture,
) -> AIArchitecture:
    result = AIArchitecture.model_validate(
        {
            **draft.model_dump(mode="python"),
            "id": generate_uuid(),
            "session_id": requirements.session_id,
            "requirements_specification_id": requirements.id,
            "solution_architecture_id": solution.id,
            "source_metadata": requirements.source_metadata,
        }
    )
    AIArchitecture.validate_requirements_ownership(
        ai_architecture=result,
        requirements_specification=requirements,
    )
    AIArchitecture.validate_architecture_ownership(
        ai_architecture=result,
        solution_architecture=solution,
    )
    return result
