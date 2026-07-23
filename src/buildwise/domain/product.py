from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    ArtifactId,
    BuildWiseModel,
    CostEstimate,
    MediumText,
    NormalizedScore,
    SessionId,
    ShortText,
    SourceMetadata,
    generate_uuid,
    utc_now,
)
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import (
    ConfidenceLevel,
    FeatureCategory,
    RequirementPriority,
    RiskLikelihood,
    RiskSeverity,
    RoadmapHorizon,
)


PersonaType = Literal[
    "primary",
    "secondary",
    "administrator",
    "internal",
    "buyer",
    "decision_maker",
    "support",
]

GoalCategory = Literal[
    "user",
    "business",
    "product",
    "operational",
    "technical",
    "compliance",
]

FeatureStatus = Literal[
    "proposed",
    "validated",
    "deferred",
    "excluded",
]

RiskCategory = Literal[
    "product",
    "user_adoption",
    "business",
    "market",
    "delivery",
    "technical",
    "integration",
    "data",
    "ai",
    "security",
    "privacy",
    "compliance",
    "quality",
    "cost",
    "operations",
]

RoadmapItemStatus = Literal[
    "planned",
    "blocked",
    "deferred",
    "completed",
]

ProductDefinitionDecision = Literal[
    "approved",
    "approved_with_assumptions",
    "requires_clarification",
    "cannot_proceed",
]


class ProductGoal(BuildWiseModel):
    """A measurable product, user, business, or operational goal."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: GoalCategory

    success_measure: MediumText
    target_value: ShortText | None = None
    target_timeframe: ShortText | None = None

    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE
    measurable: bool = True

    rationale: MediumText
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate source references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_measurement_details(self) -> ProductGoal:
        """Ensure measurable goals include a meaningful success measure."""

        if self.measurable and not self.success_measure.strip():
            raise ValueError(
                "A measurable product goal requires a success_measure."
            )

        if not self.measurable and self.target_value is not None:
            raise ValueError(
                "target_value cannot be provided when measurable is false."
            )

        return self


class UserPersona(BuildWiseModel):
    """A canonical product persona derived from discovery evidence."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    persona_type: PersonaType
    description: MediumText

    primary: bool = False

    goals: list[MediumText] = Field(min_length=1)
    needs: list[MediumText] = Field(min_length=1)
    pain_points: list[MediumText] = Field(min_length=1)

    behaviors: list[MediumText] = Field(default_factory=list)
    motivations: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)

    technical_proficiency: Literal[
        "low",
        "medium",
        "high",
        "mixed",
        "unknown",
    ] = "unknown"

    accessibility_needs: list[MediumText] = Field(default_factory=list)
    representative_scenario: MediumText | None = None

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    @field_validator(
        "goals",
        "needs",
        "pain_points",
        "behaviors",
        "motivations",
        "constraints",
        "accessibility_needs",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate persona values."""

        if len(value) != len(set(value)):
            raise ValueError("Persona list values must be unique.")

        return value

    @field_validator("source_reference_ids")
    @classmethod
    def ensure_unique_source_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate persona source references."""

        if len(value) != len(set(value)):
            raise ValueError("source_reference_ids must be unique.")

        return value

    @model_validator(mode="after")
    def validate_primary_persona_type(self) -> UserPersona:
        """Prevent support and administrative personas becoming primary users."""

        non_primary_types = {
            "administrator",
            "support",
        }

        if self.primary and self.persona_type in non_primary_types:
            raise ValueError(
                "Administrative and support personas cannot be marked primary."
            )

        return self


class ProductFeature(BuildWiseModel):
    """A user-facing or operational capability in the product scope."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    description: MediumText

    category: FeatureCategory
    priority: RequirementPriority
    status: FeatureStatus = "proposed"

    user_value: MediumText
    business_value: MediumText | None = None
    rationale: MediumText

    included_in_mvp: bool = False
    ai_enabled: bool = False

    target_persona_ids: list[ArtifactId] = Field(min_length=1)
    supporting_goal_ids: list[ArtifactId] = Field(min_length=1)

    dependencies: list[ArtifactId] = Field(default_factory=list)
    exclusions: list[MediumText] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)

    success_indicators: list[MediumText] = Field(default_factory=list)
    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "target_persona_ids",
        "supporting_goal_ids",
        "dependencies",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate feature identifier references."""

        if len(value) != len(set(value)):
            raise ValueError("Feature identifier lists must contain unique values.")

        return value

    @field_validator(
        "exclusions",
        "assumptions",
        "success_indicators",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicated feature metadata."""

        if len(value) != len(set(value)):
            raise ValueError("Feature text lists must contain unique values.")

        return value

    @model_validator(mode="after")
    def validate_feature_scope(self) -> ProductFeature:
        """Validate MVP inclusion, priority, and feature status."""

        if self.included_in_mvp and self.priority is RequirementPriority.WONT_HAVE:
            raise ValueError(
                "A feature included in the MVP cannot have wont_have priority."
            )

        if self.included_in_mvp and self.status in {"deferred", "excluded"}:
            raise ValueError(
                "A deferred or excluded feature cannot be included in the MVP."
            )

        if self.status == "excluded" and self.included_in_mvp:
            raise ValueError(
                "An excluded feature cannot be included in the MVP."
            )

        if self.id in self.dependencies:
            raise ValueError("A product feature cannot depend on itself.")

        return self


class ProductRoadmapItem(BuildWiseModel):
    """A roadmap item that sequences delivery of product scope."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText

    horizon: RoadmapHorizon
    priority: RequirementPriority
    status: RoadmapItemStatus = "planned"

    outcome: MediumText
    rationale: MediumText

    feature_ids: list[ArtifactId] = Field(default_factory=list)
    dependency_ids: list[ArtifactId] = Field(default_factory=list)

    estimated_duration: ShortText | None = None
    entry_criteria: list[MediumText] = Field(default_factory=list)
    completion_criteria: list[MediumText] = Field(min_length=1)

    risks: list[MediumText] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)

    @field_validator(
        "feature_ids",
        "dependency_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicated roadmap references."""

        if len(value) != len(set(value)):
            raise ValueError("Roadmap identifier lists must be unique.")

        return value

    @field_validator(
        "entry_criteria",
        "completion_criteria",
        "risks",
        "assumptions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate roadmap statements."""

        if len(value) != len(set(value)):
            raise ValueError("Roadmap text lists must contain unique values.")

        return value

    @model_validator(mode="after")
    def validate_roadmap_item(self) -> ProductRoadmapItem:
        """Validate roadmap priority and dependency consistency."""

        if self.id in self.dependency_ids:
            raise ValueError("A roadmap item cannot depend on itself.")

        if (
            self.horizon is RoadmapHorizon.MVP
            and self.priority is RequirementPriority.WONT_HAVE
        ):
            raise ValueError(
                "An MVP roadmap item cannot have wont_have priority."
            )

        if self.status == "completed" and not self.completion_criteria:
            raise ValueError(
                "A completed roadmap item requires completion criteria."
            )

        return self


class ProductRisk(BuildWiseModel):
    """A product-level risk owned by the Product Manager.

    This model captures scope, user, adoption, delivery, and product viability
    risks. Specialist reports may later provide deeper technical, AI, security,
    QA, and market risk analyses.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: RiskCategory

    severity: RiskSeverity
    likelihood: RiskLikelihood

    potential_impact: MediumText
    mitigation: MediumText
    contingency: MediumText | None = None

    owner: ShortText | None = None
    affected_goal_ids: list[ArtifactId] = Field(default_factory=list)
    affected_feature_ids: list[ArtifactId] = Field(default_factory=list)

    accepted: bool = False
    acceptance_rationale: MediumText | None = None

    source_reference_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "affected_goal_ids",
        "affected_feature_ids",
        "source_reference_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate product-risk references."""

        if len(value) != len(set(value)):
            raise ValueError("Product risk references must be unique.")

        return value

    @model_validator(mode="after")
    def validate_risk_acceptance(self) -> ProductRisk:
        """Require rationale when a risk is explicitly accepted."""

        if self.accepted and self.acceptance_rationale is None:
            raise ValueError(
                "acceptance_rationale is required when a risk is accepted."
            )

        if not self.accepted and self.acceptance_rationale is not None:
            raise ValueError(
                "acceptance_rationale cannot be provided when accepted is false."
            )

        if (
            self.accepted
            and self.severity is RiskSeverity.CRITICAL
            and self.likelihood
            in {
                RiskLikelihood.LIKELY,
                RiskLikelihood.ALMOST_CERTAIN,
            }
        ):
            raise ValueError(
                "A likely or almost-certain critical risk cannot be accepted "
                "at product-definition stage."
            )

        return self


class ProductDefinition(BuildWiseModel):
    """Canonical structured output produced by the Product Manager.

    This model defines product direction, personas, goals, features, MVP scope,
    roadmap, risks, success criteria, and product-owned cost estimates. It does
    not define detailed technical or AI architecture.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId
    discovery_result_id: ArtifactId

    product_name: ShortText
    vision: MediumText
    value_proposition: MediumText

    problem_statement: MediumText
    target_market_summary: MediumText | None = None

    goals: list[ProductGoal] = Field(min_length=1)
    personas: list[UserPersona] = Field(min_length=1)
    features: list[ProductFeature] = Field(min_length=1)
    roadmap: list[ProductRoadmapItem] = Field(min_length=1)
    risks: list[ProductRisk] = Field(default_factory=list)

    mvp_feature_ids: list[ArtifactId] = Field(min_length=1)
    out_of_scope_feature_ids: list[ArtifactId] = Field(default_factory=list)

    product_principles: list[MediumText] = Field(min_length=1)
    success_metrics: list[MediumText] = Field(min_length=1)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    open_questions: list[MediumText] = Field(default_factory=list)

    product_cost_estimates: list[CostEstimate] = Field(default_factory=list)

    decision: ProductDefinitionDecision
    decision_rationale: MediumText

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at")
    @classmethod
    def normalize_generated_at(cls, value: datetime) -> datetime:
        """Require product-definition timestamps to be timezone-aware."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware.")

        return value.astimezone(UTC)

    @field_validator(
        "goals",
        "personas",
        "features",
        "roadmap",
        "risks",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[object],
    ) -> list[object]:
        """Prevent duplicate domain artifact identifiers."""

        artifact_ids = [getattr(item, "id") for item in value]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(
                "Product-definition artifact IDs must be unique "
                "within each collection."
            )

        return value

    @field_validator(
        "mvp_feature_ids",
        "out_of_scope_feature_ids",
    )
    @classmethod
    def ensure_unique_feature_references(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate feature scope references."""

        if len(value) != len(set(value)):
            raise ValueError("Feature scope references must be unique.")

        return value

    @field_validator(
        "product_principles",
        "success_metrics",
        "assumptions",
        "constraints",
        "open_questions",
        "limitations",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate product-definition statements."""

        if len(value) != len(set(value)):
            raise ValueError(
                "Product-definition text lists must contain unique values."
            )

        return value

    @model_validator(mode="after")
    def validate_product_definition(self) -> ProductDefinition:
        """Validate references, scope, ownership, and decision consistency."""

        goal_ids = {goal.id for goal in self.goals}
        persona_ids = {persona.id for persona in self.personas}
        feature_ids = {feature.id for feature in self.features}
        roadmap_ids = {item.id for item in self.roadmap}

        primary_personas = [
            persona for persona in self.personas if persona.primary
        ]

        if len(primary_personas) != 1:
            raise ValueError(
                "ProductDefinition must contain exactly one primary persona."
            )

        missing_mvp_features = set(self.mvp_feature_ids).difference(feature_ids)

        if missing_mvp_features:
            formatted = ", ".join(
                sorted(str(identifier) for identifier in missing_mvp_features)
            )
            raise ValueError(
                "mvp_feature_ids reference features not present in the "
                f"definition: {formatted}."
            )

        missing_out_of_scope_features = set(
            self.out_of_scope_feature_ids
        ).difference(feature_ids)

        if missing_out_of_scope_features:
            formatted = ", ".join(
                sorted(
                    str(identifier)
                    for identifier in missing_out_of_scope_features
                )
            )
            raise ValueError(
                "out_of_scope_feature_ids reference features not present in "
                f"the definition: {formatted}."
            )

        overlapping_scope = set(self.mvp_feature_ids).intersection(
            self.out_of_scope_feature_ids
        )

        if overlapping_scope:
            formatted = ", ".join(
                sorted(str(identifier) for identifier in overlapping_scope)
            )
            raise ValueError(
                "Features cannot be both in MVP and out of scope: "
                f"{formatted}."
            )

        for feature in self.features:
            missing_personas = set(feature.target_persona_ids).difference(
                persona_ids
            )

            if missing_personas:
                formatted = ", ".join(
                    sorted(str(identifier) for identifier in missing_personas)
                )
                raise ValueError(
                    f"Feature '{feature.name}' references unknown personas: "
                    f"{formatted}."
                )

            missing_goals = set(feature.supporting_goal_ids).difference(
                goal_ids
            )

            if missing_goals:
                formatted = ", ".join(
                    sorted(str(identifier) for identifier in missing_goals)
                )
                raise ValueError(
                    f"Feature '{feature.name}' references unknown goals: "
                    f"{formatted}."
                )

            missing_dependencies = set(feature.dependencies).difference(
                feature_ids
            )

            if missing_dependencies:
                formatted = ", ".join(
                    sorted(
                        str(identifier)
                        for identifier in missing_dependencies
                    )
                )
                raise ValueError(
                    f"Feature '{feature.name}' references unknown feature "
                    f"dependencies: {formatted}."
                )

            listed_as_mvp = feature.id in self.mvp_feature_ids

            if feature.included_in_mvp != listed_as_mvp:
                raise ValueError(
                    f"Feature '{feature.name}' included_in_mvp does not "
                    "match mvp_feature_ids."
                )

            listed_as_out_of_scope = feature.id in self.out_of_scope_feature_ids

            if listed_as_out_of_scope and feature.status != "excluded":
                raise ValueError(
                    f"Out-of-scope feature '{feature.name}' must use "
                    "status='excluded'."
                )

        for roadmap_item in self.roadmap:
            missing_features = set(roadmap_item.feature_ids).difference(
                feature_ids
            )

            if missing_features:
                formatted = ", ".join(
                    sorted(str(identifier) for identifier in missing_features)
                )
                raise ValueError(
                    f"Roadmap item '{roadmap_item.title}' references unknown "
                    f"features: {formatted}."
                )

            missing_dependencies = set(
                roadmap_item.dependency_ids
            ).difference(roadmap_ids)

            if missing_dependencies:
                formatted = ", ".join(
                    sorted(
                        str(identifier)
                        for identifier in missing_dependencies
                    )
                )
                raise ValueError(
                    f"Roadmap item '{roadmap_item.title}' references unknown "
                    f"roadmap dependencies: {formatted}."
                )

        for risk in self.risks:
            missing_goals = set(risk.affected_goal_ids).difference(goal_ids)

            if missing_goals:
                formatted = ", ".join(
                    sorted(str(identifier) for identifier in missing_goals)
                )
                raise ValueError(
                    f"Risk '{risk.title}' references unknown goals: "
                    f"{formatted}."
                )

            missing_features = set(
                risk.affected_feature_ids
            ).difference(feature_ids)

            if missing_features:
                formatted = ", ".join(
                    sorted(str(identifier) for identifier in missing_features)
                )
                raise ValueError(
                    f"Risk '{risk.title}' references unknown features: "
                    f"{formatted}."
                )

        mvp_roadmap_items = [
            item for item in self.roadmap if item.horizon is RoadmapHorizon.MVP
        ]

        if not mvp_roadmap_items:
            raise ValueError(
                "ProductDefinition must contain at least one MVP roadmap item."
            )

        if self.decision == "approved" and self.open_questions:
            raise ValueError(
                "An approved ProductDefinition cannot contain open questions."
            )

        if (
            self.decision == "approved_with_assumptions"
            and not self.assumptions
        ):
            raise ValueError(
                "approved_with_assumptions requires at least one assumption."
            )

        if (
            self.decision == "requires_clarification"
            and not self.open_questions
        ):
            raise ValueError(
                "requires_clarification requires at least one open question."
            )

        if self.decision == "cannot_proceed" and not self.limitations:
            raise ValueError(
                "cannot_proceed requires at least one documented limitation."
            )

        return self

    @classmethod
    def validate_discovery_ownership(
        cls,
        *,
        product_definition: ProductDefinition,
        discovery_result: DiscoveryResult,
    ) -> None:
        """Validate that a definition belongs to the supplied Discovery result.

        This cross-artifact check remains explicit because ProductDefinition
        stores the Discovery identifier rather than embedding the full
        Discovery result.
        """

        if product_definition.session_id != discovery_result.session_id:
            raise ValueError(
                "ProductDefinition and DiscoveryResult session IDs must match."
            )

        if product_definition.discovery_result_id != discovery_result.id:
            raise ValueError(
                "ProductDefinition.discovery_result_id must match "
                "DiscoveryResult.id."
            )