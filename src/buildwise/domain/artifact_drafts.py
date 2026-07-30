"""Compact top-level generation contracts for canonical planning artifacts.

Nested semantic structures remain strongly typed. Ownership identifiers,
timestamps, and source metadata are injected from authoritative upstream
artifacts after generation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

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


def _draft_model(
    name: str,
    canonical: type[BaseModel],
    *,
    omit: set[str],
) -> type[BuildWiseModel]:
    fields: dict[str, Any] = {}
    for field_name, field in canonical.model_fields.items():
        if field_name in omit:
            continue
        fields[field_name] = (field.annotation, deepcopy(field))
    return create_model(name, __base__=BuildWiseModel, **fields)


ProductDefinitionDraft = _draft_model(
    "ProductDefinitionDraft",
    ProductDefinition,
    omit=_COMMON_OPERATIONAL_FIELDS | {"discovery_result_id"},
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


def assemble_product_definition(
    draft: BuildWiseModel,
    *,
    discovery: DiscoveryResult,
) -> ProductDefinition:
    result = ProductDefinition.model_validate(
        {
            **draft.model_dump(mode="python"),
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
            **draft.model_dump(mode="python"),
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
