from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Protocol

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
from buildwise.domain.enums import (
    ConfidenceLevel,
    RequirementPriority,
    RiskLikelihood,
    RiskSeverity,
)


class _HasArtifactId(Protocol):
    """Structural type for market and GTM artifacts identified by ArtifactId."""

    id: ArtifactId


MarketEvidenceType = Literal[
    "user_input",
    "product_definition",
    "market_report",
    "industry_report",
    "competitor_website",
    "pricing_page",
    "customer_review",
    "public_dataset",
    "government_source",
    "research_publication",
    "expert_analysis",
    "inference",
    "other",
]

EvidenceStrength = Literal[
    "weak",
    "moderate",
    "strong",
]

MarketSegmentType = Literal[
    "primary",
    "secondary",
    "future",
    "excluded",
]

MarketMaturity = Literal[
    "emerging",
    "growing",
    "mature",
    "declining",
    "uncertain",
]

CompetitorType = Literal[
    "direct",
    "indirect",
    "substitute",
    "manual_process",
    "internal_solution",
]

CompetitorRelevance = Literal[
    "low",
    "medium",
    "high",
]

PositioningStrategy = Literal[
    "category_leader",
    "category_challenger",
    "niche_specialist",
    "cost_leader",
    "premium",
    "differentiated",
    "new_category",
    "complementary",
]

GTMChannelType = Literal[
    "organic_content",
    "seo",
    "paid_search",
    "paid_social",
    "social_media",
    "community",
    "email",
    "outbound_sales",
    "inbound_sales",
    "partnerships",
    "marketplaces",
    "events",
    "developer_relations",
    "product_led_growth",
    "referrals",
    "affiliate",
    "direct_sales",
    "other",
]

ChannelStage = Literal[
    "awareness",
    "acquisition",
    "activation",
    "conversion",
    "retention",
    "expansion",
    "referral",
]

PricingModel = Literal[
    "free",
    "freemium",
    "subscription",
    "usage_based",
    "seat_based",
    "tiered",
    "transaction_fee",
    "commission",
    "one_time",
    "license",
    "service_fee",
    "enterprise_contract",
    "hybrid",
    "not_decided",
]

LaunchPhase = Literal[
    "validation",
    "private_alpha",
    "private_beta",
    "public_beta",
    "general_availability",
    "growth",
]

ExperimentType = Literal[
    "customer_interview",
    "landing_page",
    "waitlist",
    "concierge_mvp",
    "prototype_test",
    "pricing_test",
    "message_test",
    "channel_test",
    "sales_outreach",
    "pilot",
    "retention_test",
    "other",
]

MarketRiskCategory = Literal[
    "demand",
    "competition",
    "positioning",
    "pricing",
    "distribution",
    "adoption",
    "retention",
    "trust",
    "regulation",
    "market_timing",
    "sales_cycle",
    "customer_concentration",
    "evidence_quality",
    "other",
]

MarketAndGTMDecision = Literal[
    "approved",
    "approved_with_assumptions",
    "requires_more_research",
    "requires_clarification",
    "cannot_recommend",
]


def _ensure_unique_values[T](
    value: list[T],
    *,
    field_name: str,
) -> list[T]:
    """Return a list after verifying that it contains unique values."""

    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must contain unique values.")

    return value


def _normalize_datetime(
    value: datetime,
    *,
    field_name: str,
) -> datetime:
    """Require a timezone-aware datetime and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return value.astimezone(UTC)


class MarketEvidence(BuildWiseModel):
    """A source or inference supporting a market or GTM claim."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    evidence_type: MarketEvidenceType
    title: ShortText
    summary: MediumText

    source_name: ShortText | None = None
    source_url: str | None = Field(
        default=None,
        min_length=8,
        max_length=2_000,
    )
    published_at: datetime | None = None

    strength: EvidenceStrength
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    supports_claims: list[MediumText] = Field(min_length=1)
    limitations: list[MediumText] = Field(default_factory=list)

    externally_verified: bool = False

    @field_validator("published_at")
    @classmethod
    def normalize_published_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Normalize evidence publication time when supplied."""

        if value is None:
            return None

        return _normalize_datetime(
            value,
            field_name="published_at",
        )

    @field_validator(
        "supports_claims",
        "limitations",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate evidence claims and limitations."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_evidence(self) -> MarketEvidence:
        """Validate evidence provenance and verification claims."""

        external_types = {
            "market_report",
            "industry_report",
            "competitor_website",
            "pricing_page",
            "customer_review",
            "public_dataset",
            "government_source",
            "research_publication",
            "expert_analysis",
        }

        if self.evidence_type in external_types and self.source_name is None:
            raise ValueError("External market evidence requires source_name.")

        if self.externally_verified and self.source_url is None:
            raise ValueError("Externally verified evidence requires source_url.")

        if self.evidence_type == "inference":
            if self.externally_verified:
                raise ValueError("An inference cannot be marked externally verified.")

            if self.strength == "strong":
                raise ValueError("Inference-only evidence cannot have strong strength.")

        return self


class MarketSegment(BuildWiseModel):
    """A market segment evaluated for product targeting."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    segment_type: MarketSegmentType
    description: MediumText

    target_persona_ids: list[ArtifactId] = Field(min_length=1)

    defining_characteristics: list[MediumText] = Field(min_length=1)
    needs: list[MediumText] = Field(min_length=1)
    pain_points: list[MediumText] = Field(min_length=1)
    buying_triggers: list[MediumText] = Field(default_factory=list)
    objections: list[MediumText] = Field(default_factory=list)

    market_maturity: MarketMaturity
    willingness_to_pay: Literal[
        "low",
        "medium",
        "high",
        "unknown",
    ] = "unknown"

    attractiveness_score: NormalizedScore
    priority: RequirementPriority

    rationale: MediumText
    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "target_persona_ids",
        "evidence_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
        info: object,
    ) -> list[ArtifactId]:
        """Prevent duplicate market-segment references."""

        field_name = getattr(info, "field_name", "identifier values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator(
        "defining_characteristics",
        "needs",
        "pain_points",
        "buying_triggers",
        "objections",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate segment statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_segment(self) -> MarketSegment:
        """Validate segment scope and priority."""

        if self.segment_type == "excluded" and self.priority is not RequirementPriority.WONT_HAVE:
            raise ValueError("An excluded market segment must use wont_have priority.")

        if self.segment_type == "primary" and self.priority is RequirementPriority.WONT_HAVE:
            raise ValueError("A primary market segment cannot use wont_have priority.")

        return self


class CompetitorProfile(BuildWiseModel):
    """A direct competitor, indirect alternative, or substitute."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    competitor_type: CompetitorType
    description: MediumText

    website_url: str | None = Field(
        default=None,
        min_length=8,
        max_length=2_000,
    )

    target_customers: list[MediumText] = Field(default_factory=list)
    primary_use_cases: list[MediumText] = Field(min_length=1)

    strengths: list[MediumText] = Field(min_length=1)
    weaknesses: list[MediumText] = Field(min_length=1)

    pricing_summary: MediumText | None = None
    positioning_summary: MediumText

    differentiators_against: list[MediumText] = Field(min_length=1)
    risks_created: list[MediumText] = Field(default_factory=list)

    relevance: CompetitorRelevance
    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    @field_validator(
        "target_customers",
        "primary_use_cases",
        "strengths",
        "weaknesses",
        "differentiators_against",
        "risks_created",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate competitor observations."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator("evidence_ids")
    @classmethod
    def ensure_unique_evidence_ids(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate competitor evidence references."""

        return _ensure_unique_values(
            value,
            field_name="evidence_ids",
        )


class MarketOpportunity(BuildWiseModel):
    """A market opportunity supported by evidence and product relevance."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText

    target_segment_ids: list[ArtifactId] = Field(min_length=1)
    related_feature_ids: list[ArtifactId] = Field(default_factory=list)

    unmet_need: MediumText
    value_capture_hypothesis: MediumText

    urgency: Literal[
        "low",
        "medium",
        "high",
    ]
    opportunity_size: Literal[
        "small",
        "medium",
        "large",
        "unknown",
    ]

    attractiveness_score: NormalizedScore
    feasibility_score: NormalizedScore

    assumptions: list[MediumText] = Field(default_factory=list)
    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "target_segment_ids",
        "related_feature_ids",
        "evidence_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
        info: object,
    ) -> list[ArtifactId]:
        """Prevent duplicate opportunity references."""

        field_name = getattr(info, "field_name", "identifier values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator("assumptions")
    @classmethod
    def ensure_unique_assumptions(
        cls,
        value: list[MediumText],
    ) -> list[MediumText]:
        """Prevent duplicate opportunity assumptions."""

        return _ensure_unique_values(
            value,
            field_name="assumptions",
        )


class PositioningRecommendation(BuildWiseModel):
    """Recommended market position and messaging foundation."""

    strategy: PositioningStrategy

    category: ShortText
    target_customer: MediumText
    customer_problem: MediumText

    value_promise: MediumText
    primary_differentiator: MediumText

    supporting_differentiators: list[MediumText] = Field(min_length=1)
    reasons_to_believe: list[MediumText] = Field(min_length=1)

    positioning_statement: MediumText
    messaging_pillars: list[MediumText] = Field(min_length=1)

    claims_to_avoid: list[MediumText] = Field(default_factory=list)
    assumptions: list[MediumText] = Field(default_factory=list)

    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "supporting_differentiators",
        "reasons_to_believe",
        "messaging_pillars",
        "claims_to_avoid",
        "assumptions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate positioning statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator("evidence_ids")
    @classmethod
    def ensure_unique_evidence_ids(
        cls,
        value: list[ArtifactId],
    ) -> list[ArtifactId]:
        """Prevent duplicate positioning evidence references."""

        return _ensure_unique_values(
            value,
            field_name="evidence_ids",
        )


class PricingHypothesis(BuildWiseModel):
    """A pricing hypothesis for validation, not a guaranteed market price."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    pricing_model: PricingModel
    name: ShortText
    description: MediumText

    target_segment_ids: list[ArtifactId] = Field(min_length=1)

    value_metric: ShortText | None = None
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
    )

    proposed_price: float | None = Field(default=None, ge=0.0)
    proposed_price_range_min: float | None = Field(
        default=None,
        ge=0.0,
    )
    proposed_price_range_max: float | None = Field(
        default=None,
        ge=0.0,
    )

    billing_frequency: Literal[
        "one_time",
        "monthly",
        "quarterly",
        "annually",
        "per_usage",
        "per_transaction",
        "custom",
        "not_applicable",
    ] = "monthly"

    included_value: list[MediumText] = Field(min_length=1)
    pricing_assumptions: list[MediumText] = Field(min_length=1)
    validation_method: MediumText

    evidence_ids: list[ArtifactId] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize an ISO-style currency code."""

        normalized = value.strip().upper()

        if not normalized.isalpha():
            raise ValueError("currency must contain alphabetic characters only.")

        return normalized

    @field_validator(
        "target_segment_ids",
        "evidence_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
        info: object,
    ) -> list[ArtifactId]:
        """Prevent duplicate pricing references."""

        field_name = getattr(info, "field_name", "identifier values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator(
        "included_value",
        "pricing_assumptions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate pricing statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_pricing_hypothesis(self) -> PricingHypothesis:
        """Validate fixed and ranged pricing representations."""

        has_fixed_price = self.proposed_price is not None
        has_range = (
            self.proposed_price_range_min is not None or self.proposed_price_range_max is not None
        )

        if has_fixed_price and has_range:
            raise ValueError("Provide either proposed_price or a proposed price range, not both.")

        if has_range:
            if self.proposed_price_range_min is None:
                raise ValueError("proposed_price_range_min is required for ranged pricing.")

            if self.proposed_price_range_max is None:
                raise ValueError("proposed_price_range_max is required for ranged pricing.")

            if self.proposed_price_range_max < self.proposed_price_range_min:
                raise ValueError(
                    "proposed_price_range_max cannot be lower than proposed_price_range_min."
                )

        free_models = {
            "free",
            "freemium",
        }

        if self.pricing_model == "free" and self.proposed_price not in {None, 0.0}:
            raise ValueError("A free pricing model cannot define a positive price.")

        if self.pricing_model in free_models and (
            self.proposed_price_range_min is not None
            or self.proposed_price_range_max is not None
        ):
            raise ValueError(
                "Free and freemium hypotheses cannot use a price range "
                "as their only definition."
            )

        if self.pricing_model == "not_decided" and (has_fixed_price or has_range):
            raise ValueError("An undecided pricing model cannot define prices.")

        return self


class GTMChannelRecommendation(BuildWiseModel):
    """A recommended acquisition, conversion, or retention channel."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    channel: GTMChannelType
    name: ShortText
    description: MediumText

    funnel_stages: list[ChannelStage] = Field(min_length=1)
    target_segment_ids: list[ArtifactId] = Field(min_length=1)

    channel_hypothesis: MediumText
    proposed_tactics: list[MediumText] = Field(min_length=1)

    success_metrics: list[MediumText] = Field(min_length=1)
    expected_cost_level: Literal[
        "low",
        "medium",
        "high",
        "unknown",
    ]
    expected_time_to_signal: ShortText

    priority: RequirementPriority
    assumptions: list[MediumText] = Field(default_factory=list)
    risks: list[MediumText] = Field(default_factory=list)

    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    @field_validator(
        "funnel_stages",
        "target_segment_ids",
        "evidence_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[object],
        info: object,
    ) -> list[object]:
        """Prevent duplicate channel references and funnel stages."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator(
        "proposed_tactics",
        "success_metrics",
        "assumptions",
        "risks",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate channel statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )


class LaunchExperiment(BuildWiseModel):
    """A bounded experiment for validating a market or GTM hypothesis."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    name: ShortText
    experiment_type: ExperimentType
    launch_phase: LaunchPhase

    hypothesis: MediumText
    target_segment_ids: list[ArtifactId] = Field(min_length=1)

    method: MediumText
    success_metrics: list[MediumText] = Field(min_length=1)
    pass_criteria: list[MediumText] = Field(min_length=1)
    failure_criteria: list[MediumText] = Field(min_length=1)

    estimated_duration: ShortText
    estimated_cost_level: Literal[
        "low",
        "medium",
        "high",
    ]

    dependencies: list[ArtifactId] = Field(default_factory=list)
    risks: list[MediumText] = Field(default_factory=list)

    priority: RequirementPriority

    @field_validator(
        "target_segment_ids",
        "dependencies",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
        info: object,
    ) -> list[ArtifactId]:
        """Prevent duplicate experiment references."""

        field_name = getattr(info, "field_name", "identifier values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @field_validator(
        "success_metrics",
        "pass_criteria",
        "failure_criteria",
        "risks",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate experiment statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_experiment(self) -> LaunchExperiment:
        """Validate experiment dependency consistency."""

        if self.id in self.dependencies:
            raise ValueError("A launch experiment cannot depend on itself.")

        return self


class MarketRisk(BuildWiseModel):
    """A market or go-to-market risk and its mitigation plan."""

    id: ArtifactId = Field(default_factory=generate_uuid)

    title: ShortText
    description: MediumText
    category: MarketRiskCategory

    severity: RiskSeverity
    likelihood: RiskLikelihood

    potential_impact: MediumText
    mitigation: MediumText
    validation_action: MediumText | None = None
    contingency: MediumText | None = None

    affected_segment_ids: list[ArtifactId] = Field(default_factory=list)
    affected_channel_ids: list[ArtifactId] = Field(default_factory=list)
    evidence_ids: list[ArtifactId] = Field(default_factory=list)

    accepted: bool = False
    acceptance_rationale: MediumText | None = None

    @field_validator(
        "affected_segment_ids",
        "affected_channel_ids",
        "evidence_ids",
    )
    @classmethod
    def ensure_unique_identifier_values(
        cls,
        value: list[ArtifactId],
        info: object,
    ) -> list[ArtifactId]:
        """Prevent duplicate risk references."""

        field_name = getattr(info, "field_name", "identifier values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_market_risk(self) -> MarketRisk:
        """Validate risk acceptance and validation actions."""

        if self.accepted and self.acceptance_rationale is None:
            raise ValueError("acceptance_rationale is required when a risk is accepted.")

        if not self.accepted and self.acceptance_rationale is not None:
            raise ValueError("acceptance_rationale cannot be provided when accepted is false.")

        if (
            self.severity
            in {
                RiskSeverity.HIGH,
                RiskSeverity.CRITICAL,
            }
            and self.validation_action is None
        ):
            raise ValueError("High and critical market risks require a validation action.")

        if (
            self.accepted
            and self.severity is RiskSeverity.CRITICAL
            and self.likelihood
            in {
                RiskLikelihood.LIKELY,
                RiskLikelihood.ALMOST_CERTAIN,
            }
        ):
            raise ValueError("A likely or almost-certain critical market risk cannot be accepted.")

        return self


class MarketAndGTMStrategy(BuildWiseModel):
    """Canonical structured output of the Market and GTM Strategist.

    This artifact evaluates market segments, competition, positioning,
    pricing hypotheses, channels, launch experiments, and market risks.

    It does not redefine ProductDefinition scope, select software
    architecture, or guarantee market facts when evidence is unavailable.
    """

    id: ArtifactId = Field(default_factory=generate_uuid)
    session_id: SessionId
    product_definition_id: ArtifactId

    title: ShortText
    executive_summary: MediumText

    market_category: ShortText
    market_maturity: MarketMaturity
    market_problem_summary: MediumText

    segments: list[MarketSegment] = Field(min_length=1)
    primary_segment_id: ArtifactId

    competitors: list[CompetitorProfile] = Field(default_factory=list)
    opportunities: list[MarketOpportunity] = Field(min_length=1)

    positioning: PositioningRecommendation

    pricing_hypotheses: list[PricingHypothesis] = Field(
        default_factory=list,
    )
    channel_recommendations: list[GTMChannelRecommendation] = Field(
        min_length=1,
    )
    launch_experiments: list[LaunchExperiment] = Field(min_length=1)

    launch_strategy: MediumText
    initial_customer_acquisition_plan: MediumText
    retention_and_expansion_hypothesis: MediumText

    risks: list[MarketRisk] = Field(default_factory=list)
    evidence: list[MarketEvidence] = Field(default_factory=list)

    assumptions: list[MediumText] = Field(default_factory=list)
    constraints: list[MediumText] = Field(default_factory=list)
    evidence_gaps: list[MediumText] = Field(default_factory=list)
    open_questions: list[MediumText] = Field(default_factory=list)

    gtm_cost_estimates: list[CostEstimate] = Field(default_factory=list)

    decision: MarketAndGTMDecision
    decision_rationale: MediumText

    limitations: list[MediumText] = Field(default_factory=list)
    source_metadata: list[SourceMetadata] = Field(default_factory=list)

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: NormalizedScore

    generated_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at", "updated_at")
    @classmethod
    def normalize_strategy_timestamp(
        cls,
        value: datetime,
        info: object,
    ) -> datetime:
        """Normalize strategy timestamps to UTC."""

        field_name = getattr(info, "field_name", "timestamp")

        return _normalize_datetime(
            value,
            field_name=field_name,
        )

    @field_validator(
        "segments",
        "competitors",
        "opportunities",
        "pricing_hypotheses",
        "channel_recommendations",
        "launch_experiments",
        "risks",
        "evidence",
    )
    @classmethod
    def ensure_unique_artifact_ids(
        cls,
        value: list[_HasArtifactId],
    ) -> list[_HasArtifactId]:
        """Prevent duplicate artifact IDs within each collection."""

        artifact_ids = [item.id for item in value]

        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("Market and GTM artifact IDs must be unique within each collection.")

        return value

    @field_validator(
        "assumptions",
        "constraints",
        "evidence_gaps",
        "open_questions",
        "limitations",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicate strategy statements."""

        field_name = getattr(info, "field_name", "values")

        return _ensure_unique_values(
            value,
            field_name=field_name,
        )

    @model_validator(mode="after")
    def validate_market_and_gtm_strategy(
        self,
    ) -> MarketAndGTMStrategy:
        """Validate references, evidence, and decision consistency."""

        if self.updated_at < self.generated_at:
            raise ValueError("updated_at cannot be earlier than generated_at.")

        segment_ids = {segment.id for segment in self.segments}
        competitor_ids = {competitor.id for competitor in self.competitors}
        opportunity_ids = {opportunity.id for opportunity in self.opportunities}
        channel_ids = {channel.id for channel in self.channel_recommendations}
        experiment_ids = {experiment.id for experiment in self.launch_experiments}
        evidence_ids = {evidence.id for evidence in self.evidence}

        del competitor_ids
        del opportunity_ids

        if self.primary_segment_id not in segment_ids:
            raise ValueError("primary_segment_id must reference an existing segment.")

        primary_segments = [
            segment for segment in self.segments if segment.segment_type == "primary"
        ]

        if len(primary_segments) != 1:
            raise ValueError(
                "MarketAndGTMStrategy must contain exactly one primary market segment."
            )

        if primary_segments[0].id != self.primary_segment_id:
            raise ValueError("primary_segment_id must match the segment marked primary.")

        for segment in self.segments:
            missing_evidence = set(segment.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"Market segment '{segment.name}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        for competitor in self.competitors:
            missing_evidence = set(competitor.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"Competitor '{competitor.name}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        for opportunity in self.opportunities:
            missing_segments = set(opportunity.target_segment_ids).difference(segment_ids)

            if missing_segments:
                self._raise_missing_reference_error(
                    owner=f"Market opportunity '{opportunity.title}'",
                    reference_type="segments",
                    identifiers=missing_segments,
                )

            missing_evidence = set(opportunity.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"Market opportunity '{opportunity.title}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        missing_positioning_evidence = set(self.positioning.evidence_ids).difference(evidence_ids)

        if missing_positioning_evidence:
            self._raise_missing_reference_error(
                owner="Positioning recommendation",
                reference_type="evidence",
                identifiers=missing_positioning_evidence,
            )

        for pricing in self.pricing_hypotheses:
            missing_segments = set(pricing.target_segment_ids).difference(segment_ids)

            if missing_segments:
                self._raise_missing_reference_error(
                    owner=f"Pricing hypothesis '{pricing.name}'",
                    reference_type="segments",
                    identifiers=missing_segments,
                )

            missing_evidence = set(pricing.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"Pricing hypothesis '{pricing.name}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        for channel in self.channel_recommendations:
            missing_segments = set(channel.target_segment_ids).difference(segment_ids)

            if missing_segments:
                self._raise_missing_reference_error(
                    owner=f"GTM channel '{channel.name}'",
                    reference_type="segments",
                    identifiers=missing_segments,
                )

            missing_evidence = set(channel.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"GTM channel '{channel.name}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        for experiment in self.launch_experiments:
            missing_segments = set(experiment.target_segment_ids).difference(segment_ids)

            if missing_segments:
                self._raise_missing_reference_error(
                    owner=f"Launch experiment '{experiment.name}'",
                    reference_type="segments",
                    identifiers=missing_segments,
                )

            missing_dependencies = set(experiment.dependencies).difference(experiment_ids)

            if missing_dependencies:
                self._raise_missing_reference_error(
                    owner=f"Launch experiment '{experiment.name}'",
                    reference_type="experiment dependencies",
                    identifiers=missing_dependencies,
                )

        for risk in self.risks:
            missing_segments = set(risk.affected_segment_ids).difference(segment_ids)

            if missing_segments:
                self._raise_missing_reference_error(
                    owner=f"Market risk '{risk.title}'",
                    reference_type="segments",
                    identifiers=missing_segments,
                )

            missing_channels = set(risk.affected_channel_ids).difference(channel_ids)

            if missing_channels:
                self._raise_missing_reference_error(
                    owner=f"Market risk '{risk.title}'",
                    reference_type="channels",
                    identifiers=missing_channels,
                )

            missing_evidence = set(risk.evidence_ids).difference(evidence_ids)

            if missing_evidence:
                self._raise_missing_reference_error(
                    owner=f"Market risk '{risk.title}'",
                    reference_type="evidence",
                    identifiers=missing_evidence,
                )

        evidence_required_decisions = {
            "approved",
            "approved_with_assumptions",
        }

        if self.decision in evidence_required_decisions and not self.evidence:
            raise ValueError("An approved MarketAndGTMStrategy requires supporting evidence.")

        if self.decision == "approved" and self.open_questions:
            raise ValueError("An approved MarketAndGTMStrategy cannot contain open questions.")

        if self.decision == "approved_with_assumptions" and not self.assumptions:
            raise ValueError("approved_with_assumptions requires at least one assumption.")

        if self.decision == "requires_more_research" and not self.evidence_gaps:
            raise ValueError("requires_more_research requires at least one evidence gap.")

        if self.decision == "requires_clarification" and not self.open_questions:
            raise ValueError("requires_clarification requires at least one open question.")

        if self.decision == "cannot_recommend" and not self.limitations:
            raise ValueError("cannot_recommend requires at least one limitation.")

        return self

    @staticmethod
    def _raise_missing_reference_error(
        *,
        owner: str,
        reference_type: str,
        identifiers: set[ArtifactId],
    ) -> None:
        """Raise a consistently formatted reference error."""

        formatted_identifiers = ", ".join(sorted(str(identifier) for identifier in identifiers))

        raise ValueError(f"{owner} references unknown {reference_type}: {formatted_identifiers}.")

    @classmethod
    def validate_product_ownership(
        cls,
        *,
        market_and_gtm_strategy: MarketAndGTMStrategy,
        product_definition: object,
    ) -> None:
        """Validate market strategy references against ProductDefinition."""

        from buildwise.domain.product import ProductDefinition

        if not isinstance(product_definition, ProductDefinition):
            raise TypeError("product_definition must be a ProductDefinition instance.")

        if market_and_gtm_strategy.session_id != product_definition.session_id:
            raise ValueError("MarketAndGTMStrategy and ProductDefinition session IDs must match.")

        if market_and_gtm_strategy.product_definition_id != product_definition.id:
            raise ValueError(
                "MarketAndGTMStrategy.product_definition_id must match ProductDefinition.id."
            )

        persona_ids = {persona.id for persona in product_definition.personas}
        feature_ids = {feature.id for feature in product_definition.features}

        referenced_persona_ids = {
            persona_id
            for segment in market_and_gtm_strategy.segments
            for persona_id in segment.target_persona_ids
        }

        referenced_feature_ids = {
            feature_id
            for opportunity in market_and_gtm_strategy.opportunities
            for feature_id in opportunity.related_feature_ids
        }

        missing_personas = referenced_persona_ids.difference(persona_ids)

        if missing_personas:
            cls._raise_missing_reference_error(
                owner="MarketAndGTMStrategy",
                reference_type="ProductDefinition personas",
                identifiers=missing_personas,
            )

        missing_features = referenced_feature_ids.difference(feature_ids)

        if missing_features:
            cls._raise_missing_reference_error(
                owner="MarketAndGTMStrategy",
                reference_type="ProductDefinition features",
                identifiers=missing_features,
            )
