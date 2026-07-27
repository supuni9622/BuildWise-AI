"""Reusable builders for valid DiscoveryResult / ProductPlanningResult pairs.

These builders exist only to give the specialist-planning unit and
integration tests small, valid instances of the heavily cross-validated
BuildWise domain models without repeating that construction in every test
module. Defaults describe a boring, low-signal "standard SaaS" product;
callers override specific fields to trigger individual planner policies.
"""

from __future__ import annotations

from buildwise.domain.common import SessionId, generate_uuid
from buildwise.domain.discovery import (
    CapabilityClassification,
    CompletenessResult,
    DiscoveryResult,
    DiscoveryRisk,
    Unknown,
)
from buildwise.domain.enums import (
    CapabilityType,
    ConfidenceLevel,
    FeatureCategory,
    RequirementPriority,
    RiskLikelihood,
    RiskSeverity,
    RoadmapHorizon,
)
from buildwise.domain.intake import ProductIdeaContext, ValidatedProductIdea
from buildwise.domain.product import (
    ProductDefinition,
    ProductFeature,
    ProductGoal,
    ProductRoadmapItem,
    UserPersona,
)
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import (
    AcceptanceCriterion,
    DataRequirement,
    EdgeCase,
    FunctionalRequirement,
    IntegrationRequirement,
    NonFunctionalRequirement,
    RequirementsSpecification,
    UserJourney,
    UserJourneyStep,
    UserStory,
)

_AI_CAPABILITIES = frozenset(
    {
        CapabilityType.AI_ASSISTED,
        CapabilityType.AI_CORE,
        CapabilityType.RAG,
        CapabilityType.AGENTIC_WORKFLOW,
    }
)

_CAPABILITY_COMPANION_FLAGS: dict[CapabilityType, str] = {
    CapabilityType.RAG: "rag_required",
    CapabilityType.AGENTIC_WORKFLOW: "agents_required",
    CapabilityType.AUTOMATION: "automation_required",
    CapabilityType.SENSITIVE_DATA: "sensitive_data_detected",
    CapabilityType.REGULATED: "regulated_domain_detected",
    CapabilityType.REAL_TIME: "real_time_processing_required",
    CapabilityType.INTEGRATION_HEAVY: "external_integrations_expected",
}


def build_validated_idea(*, session_id: SessionId) -> ValidatedProductIdea:
    """Build a minimal, valid ``ValidatedProductIdea``."""

    return ValidatedProductIdea(
        session_id=session_id,
        title="Team scheduling assistant",
        summary="A tool that helps small teams schedule shared work.",
        original_idea=(
            "We want a simple tool that helps small teams schedule shared "
            "work across time zones without spreadsheets."
        ),
        normalized_problem_statement=(
            "Small teams lack a lightweight way to coordinate shared schedules across time zones."
        ),
        target_users=["team leads", "individual contributors"],
        desired_outcomes=["Reduce scheduling back-and-forth."],
        idea_maturity="partially_defined",
    )


def build_product_idea_context(*, session_id: SessionId) -> ProductIdeaContext:
    """Build a minimal, valid ``ProductIdeaContext``."""

    return ProductIdeaContext(
        session_id=session_id,
        validated_idea=build_validated_idea(session_id=session_id),
        clarification_answers=[],
        clarification_round=0,
    )


def build_capability_classification(
    *,
    capabilities: list[CapabilityType] | None = None,
    ai_required: bool = False,
    rag_required: bool = False,
    agents_required: bool = False,
    automation_required: bool = False,
    sensitive_data_detected: bool = False,
    regulated_domain_detected: bool = False,
    real_time_processing_required: bool = False,
    external_integrations_expected: bool = False,
    specialist_signals: dict[str, bool] | None = None,
) -> CapabilityClassification:
    """Build a valid ``CapabilityClassification``.

    Companion capabilities required by the domain model's cross-field
    validators are added automatically so callers only need to toggle the
    boolean flag they care about.
    """

    capability_set = set(capabilities or [CapabilityType.STANDARD_SOFTWARE])

    flag_by_capability = {
        CapabilityType.RAG: rag_required,
        CapabilityType.AGENTIC_WORKFLOW: agents_required,
        CapabilityType.AUTOMATION: automation_required,
        CapabilityType.SENSITIVE_DATA: sensitive_data_detected,
        CapabilityType.REGULATED: regulated_domain_detected,
        CapabilityType.REAL_TIME: real_time_processing_required,
        CapabilityType.INTEGRATION_HEAVY: external_integrations_expected,
    }

    for capability, flag_is_set in flag_by_capability.items():
        if flag_is_set:
            capability_set.add(capability)

    if capability_set.intersection(_AI_CAPABILITIES):
        ai_required = True

    primary_capability = next(iter(capability_set))

    return CapabilityClassification(
        capabilities=sorted(capability_set, key=lambda item: item.value),
        primary_capability=primary_capability,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.85,
        classification_source="hybrid",
        rationale="Deterministic test fixture classification.",
        ai_required=ai_required,
        rag_required=rag_required,
        agents_required=agents_required,
        automation_required=automation_required,
        sensitive_data_detected=sensitive_data_detected,
        regulated_domain_detected=regulated_domain_detected,
        real_time_processing_required=real_time_processing_required,
        external_integrations_expected=external_integrations_expected,
        specialist_signals=specialist_signals or {},
    )


def build_completeness_result(
    *,
    can_continue: bool = True,
    blocking_unknown_keys: list[str] | None = None,
) -> CompletenessResult:
    """Build a valid ``CompletenessResult``.

    ``clarification_required`` is driven only by blocking unknowns, matching
    ``DiscoveryResult``'s own validation: a Discovery that cannot continue
    for a reason other than a blocking unknown (for example, an
    irrecoverable failure) does not require clarification questions.
    """

    blocking = blocking_unknown_keys or []
    clarification_required = bool(blocking)
    is_complete = can_continue and not clarification_required

    return CompletenessResult(
        score=0.9 if is_complete else 0.4,
        percentage=90.0 if is_complete else 40.0,
        is_complete=is_complete,
        can_continue=can_continue,
        clarification_required=clarification_required,
        blocking_unknown_keys=blocking,
        rationale="Deterministic test fixture completeness assessment.",
    )


def build_discovery_result(
    *,
    session_id: SessionId | None = None,
    capabilities: list[CapabilityType] | None = None,
    ai_required: bool = False,
    rag_required: bool = False,
    agents_required: bool = False,
    automation_required: bool = False,
    sensitive_data_detected: bool = False,
    regulated_domain_detected: bool = False,
    real_time_processing_required: bool = False,
    external_integrations_expected: bool = False,
    specialist_signals: dict[str, bool] | None = None,
    risks: list[DiscoveryRisk] | None = None,
    unknowns: list[Unknown] | None = None,
    can_continue: bool = True,
) -> DiscoveryResult:
    """Build a valid, low-signal-by-default ``DiscoveryResult``."""

    resolved_session_id = session_id or generate_uuid()
    idea_context = build_product_idea_context(session_id=resolved_session_id)

    classification = build_capability_classification(
        capabilities=capabilities,
        ai_required=ai_required,
        rag_required=rag_required,
        agents_required=agents_required,
        automation_required=automation_required,
        sensitive_data_detected=sensitive_data_detected,
        regulated_domain_detected=regulated_domain_detected,
        real_time_processing_required=real_time_processing_required,
        external_integrations_expected=external_integrations_expected,
        specialist_signals=specialist_signals,
    )

    resolved_unknowns = unknowns or []
    completeness = build_completeness_result(
        can_continue=can_continue,
        blocking_unknown_keys=[unknown.key for unknown in resolved_unknowns if unknown.blocking],
    )

    recommended_next_step = "continue_to_product_definition" if can_continue else "fail_discovery"

    return DiscoveryResult(
        session_id=resolved_session_id,
        idea_context=idea_context,
        summary="A team scheduling assistant for small distributed teams.",
        problem_interpretation="Teams struggle to coordinate shared schedules.",
        target_user_interpretation="Team leads and individual contributors.",
        desired_outcome_interpretation="Faster, lower-friction scheduling.",
        known_facts=[],
        assumptions=[],
        unknowns=resolved_unknowns,
        risks=risks or [],
        completeness=completeness,
        clarification_questions=None,
        capability_classification=classification,
        recommended_next_step=recommended_next_step,
        limitations=[],
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.85,
    )


def build_market_risk(*, severity: RiskSeverity = RiskSeverity.HIGH) -> DiscoveryRisk:
    """Build a material market-category Discovery risk."""

    return DiscoveryRisk(
        title="Unvalidated market demand",
        description="The target market's willingness to pay is unvalidated.",
        category="market",
        severity=severity,
        likelihood=RiskLikelihood.POSSIBLE,
        rationale="No market evidence has been gathered yet.",
        potential_impact="The product may not find a paying market.",
    )


def build_security_risk(*, severity: RiskSeverity = RiskSeverity.HIGH) -> DiscoveryRisk:
    """Build a high-severity security-category Discovery risk."""

    return DiscoveryRisk(
        title="Unreviewed trust boundary",
        description="External access paths have not been reviewed.",
        category="security",
        severity=severity,
        likelihood=RiskLikelihood.POSSIBLE,
        rationale="No security review has occurred yet.",
        potential_impact="Unauthorized access could occur.",
    )


def build_market_unknown() -> Unknown:
    """Build a non-blocking Unknown whose impact area includes 'market'."""

    return Unknown(
        key="target_market_definition",
        description="The precise target market segment is not yet defined.",
        reason_missing="The user has not specified a target segment.",
        impact_areas=["market"],
        blocking=False,
        can_proceed_with_assumption=True,
        recommended_assumption="Assume a general small-team target market.",
        clarification_required=False,
    )


def _default_acceptance_criterion(title: str) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        title=title,
        description=f"{title} behaves as specified.",
    )


def build_product_planning_inputs(
    *,
    session_id: SessionId | None = None,
    discovery_kwargs: dict[str, object] | None = None,
    ai_enabled_mvp_feature: bool = False,
    functional_requirement_category: str = "requirements",
    data_requirements: list[DataRequirement] | None = None,
    integration_requirements: list[IntegrationRequirement] | None = None,
    extra_non_functional_requirements: list[NonFunctionalRequirement] | None = None,
    edge_cases: list[EdgeCase] | None = None,
) -> tuple[DiscoveryResult, ProductPlanningResult]:
    """Build a valid ``(DiscoveryResult, ProductPlanningResult)`` pair.

    ``discovery_kwargs`` is forwarded to :func:`build_discovery_result`.
    The remaining parameters let a test trigger a single specialist policy
    signal (AI-enabled MVP feature, a security-relevant data/integration
    requirement, an extra quality NFR, or a complex-failure edge case)
    without hand-building the full ``ProductPlanningResult`` graph.
    """

    resolved_session_id = session_id or generate_uuid()

    discovery = build_discovery_result(
        session_id=resolved_session_id,
        **(discovery_kwargs or {}),
    )

    goal = ProductGoal(
        title="Reduce scheduling overhead",
        description="Help teams agree on shared availability quickly.",
        category="product",
        success_measure="Time to agree on a shared slot drops by 50%.",
        rationale="Scheduling overhead is the primary reported pain point.",
    )

    persona = UserPersona(
        name="Team Lead Tara",
        persona_type="primary",
        description="Leads a small distributed team and owns scheduling.",
        primary=True,
        goals=["Coordinate the team's shared schedule."],
        needs=["A fast way to find shared availability."],
        pain_points=["Manually reconciling time zones in spreadsheets."],
    )

    feature = ProductFeature(
        name="Shared availability view",
        description="Shows overlapping availability across the team.",
        category=FeatureCategory.CORE,
        priority=RequirementPriority.MUST_HAVE,
        status="proposed",
        user_value="See shared availability at a glance.",
        rationale="This is the core value proposition of the product.",
        included_in_mvp=True,
        ai_enabled=ai_enabled_mvp_feature,
        target_persona_ids=[persona.id],
        supporting_goal_ids=[goal.id],
    )

    roadmap_item = ProductRoadmapItem(
        title="MVP launch",
        description="Ship the shared availability view to early customers.",
        horizon=RoadmapHorizon.MVP,
        priority=RequirementPriority.MUST_HAVE,
        outcome="Early customers can coordinate shared availability.",
        rationale="Validates the core value proposition first.",
        feature_ids=[feature.id],
        completion_criteria=["Shared availability view is usable end to end."],
    )

    product_definition = ProductDefinition(
        session_id=resolved_session_id,
        discovery_result_id=discovery.id,
        product_name="TeamSync",
        vision="Make shared team scheduling effortless.",
        value_proposition="One shared view of team availability.",
        problem_statement="Teams struggle to coordinate shared schedules.",
        goals=[goal],
        personas=[persona],
        features=[feature],
        roadmap=[roadmap_item],
        mvp_feature_ids=[feature.id],
        product_principles=["Keep scheduling effortless."],
        success_metrics=["Time to agree on a shared slot."],
        decision="approved",
        decision_rationale="The product definition is well supported by discovery.",
        confidence_score=0.85,
    )

    functional_requirement = FunctionalRequirement(
        key="view_shared_availability",
        title="View shared availability",
        description="Users can view overlapping team availability.",
        category=functional_requirement_category,
        priority=RequirementPriority.MUST_HAVE,
        actor="Team lead",
        trigger="The team lead opens the shared availability view.",
        main_flow=["The team lead opens the app.", "The shared availability view renders."],
        postconditions=["The team lead sees overlapping availability."],
        acceptance_criteria=[_default_acceptance_criterion("Shared availability renders")],
        feature_ids=[feature.id],
        persona_ids=[persona.id],
        rationale="This is the core MVP capability.",
        confidence_score=0.85,
    )

    non_functional_requirement = NonFunctionalRequirement(
        key="availability_view_latency",
        title="Shared availability view latency",
        description="The shared availability view loads quickly.",
        category="performance",
        priority=RequirementPriority.SHOULD_HAVE,
        quality_attribute="latency",
        metric="p95 load time",
        target="under 1 second",
        measurement_method="Synthetic load testing.",
        scope="The shared availability view.",
        rationale="Slow loading undermines the core value proposition.",
        acceptance_criteria=[_default_acceptance_criterion("View loads within target latency")],
        confidence_score=0.85,
    )

    non_functional_requirements = [
        non_functional_requirement,
        *(extra_non_functional_requirements or []),
    ]

    user_journey_step = UserJourneyStep(
        sequence=1,
        title="Open shared availability view",
        actor_action="The team lead opens the shared availability view.",
        system_response="The system renders overlapping availability.",
    )

    user_journey = UserJourney(
        name="Coordinate a shared meeting slot",
        description="A team lead finds a shared meeting slot.",
        persona_id=persona.id,
        trigger="The team lead needs to schedule a meeting.",
        expected_outcome="The team lead finds a shared slot quickly.",
        steps=[user_journey_step],
        postconditions=["A shared slot is identified."],
        related_feature_ids=[feature.id],
        related_requirement_ids=[functional_requirement.id],
        success_metric="Time to identify a shared slot.",
    )

    user_story = UserStory(
        key="team_lead_views_shared_availability",
        title="Team lead views shared availability",
        persona_id=persona.id,
        actor="team lead",
        capability="view the team's shared availability",
        benefit="quickly find a shared meeting slot",
        narrative=(
            "As a team lead, I want to view the team's shared availability "
            "so that I can quickly find a shared meeting slot."
        ),
        priority=RequirementPriority.MUST_HAVE,
        feature_ids=[feature.id],
        functional_requirement_ids=[functional_requirement.id],
        acceptance_criteria=[_default_acceptance_criterion("Shared availability is visible")],
    )

    requirements = RequirementsSpecification(
        session_id=resolved_session_id,
        product_definition_id=product_definition.id,
        title="TeamSync Requirements",
        summary="Requirements for the TeamSync MVP.",
        scope="The shared availability MVP.",
        functional_requirements=[functional_requirement],
        non_functional_requirements=non_functional_requirements,
        data_requirements=data_requirements or [],
        integration_requirements=integration_requirements or [],
        edge_cases=edge_cases or [],
        user_journeys=[user_journey],
        user_stories=[user_story],
        decision="approved",
        decision_rationale="The requirements are well supported by the product definition.",
        confidence_score=0.85,
    )

    product_planning = ProductPlanningResult(
        session_id=resolved_session_id,
        product_definition=product_definition,
        requirements=requirements,
    )

    return discovery, product_planning


def build_sensitive_data_requirement() -> DataRequirement:
    """Build a DataRequirement that should trigger the SENSITIVE_DATA signal."""

    return DataRequirement(
        name="Team member schedule",
        description="Stores each team member's availability schedule.",
        entity_name="ScheduleEntry",
        data_classification="sensitive_personal",
        operations=["create", "read"],
        contains_personal_data=True,
        contains_sensitive_data=True,
        encrypted_at_rest=True,
        encrypted_in_transit=True,
    )


def build_privileged_integration_requirement() -> IntegrationRequirement:
    """Build an IntegrationRequirement that should trigger EXTERNAL_INTEGRATIONS."""

    return IntegrationRequirement(
        key="calendar_sync",
        name="Calendar sync",
        description="Synchronizes availability with an external calendar provider.",
        system_name="External Calendar Provider",
        integration_type="rest_api",
        direction="bidirectional",
        purpose="Keep shared availability in sync with external calendars.",
        data_exchanged=["Availability windows"],
        authentication_method="oauth2",
        timeout_seconds=30,
        fallback_behavior="Fall back to manually entered availability.",
        failure_behavior="Show a sync error and retain the last known availability.",
        rationale="Calendar sync is a differentiating MVP capability.",
    )


def build_llm_provider_integration_requirement() -> IntegrationRequirement:
    """Build an IntegrationRequirement that should trigger the AI signal."""

    return IntegrationRequirement(
        key="llm_summary_provider",
        name="LLM summary provider",
        description="Calls an external LLM provider to summarize schedule conflicts.",
        system_name="External LLM Provider",
        integration_type="llm_provider",
        direction="outbound",
        purpose="Summarize scheduling conflicts for the team lead.",
        data_exchanged=["Availability windows", "Conflict summary"],
        authentication_method="api_key",
        timeout_seconds=30,
        fallback_behavior="Show raw conflicts without a generated summary.",
        failure_behavior="Show raw conflicts without a generated summary.",
        rationale="AI-generated summaries reduce time to resolve conflicts.",
    )


def build_complex_failure_edge_case() -> EdgeCase:
    """Build an EdgeCase that should trigger the QA complex-failure signal."""

    return EdgeCase(
        title="Concurrent availability edits",
        description="Two team members edit their availability at the same time.",
        category="concurrency",
        trigger="Two team members submit availability updates concurrently.",
        expected_behavior="retry",
        expected_result="Both updates are applied without data loss.",
        recovery_action="Retry the losing update after the winning update commits.",
    )


def build_critical_quality_requirement() -> NonFunctionalRequirement:
    """Build a must-have NFR in a QA-triggering quality category."""

    return NonFunctionalRequirement(
        key="availability_view_reliability",
        title="Shared availability view reliability",
        description="The shared availability view must stay available.",
        category="reliability",
        priority=RequirementPriority.MUST_HAVE,
        quality_attribute="availability",
        metric="uptime",
        target="99.9%",
        measurement_method="Uptime monitoring.",
        scope="The shared availability view.",
        rationale="Team leads depend on this view during live scheduling.",
        acceptance_criteria=[_default_acceptance_criterion("View remains available")],
        confidence_score=0.85,
    )
