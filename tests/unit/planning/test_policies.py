from __future__ import annotations

from buildwise.domain.enums import (
    BudgetDecisionType,
    CapabilityType,
    SpecialistSelectionReason,
    SpecialistType,
)
from buildwise.domain.specialist_planning import SpecialistRecommendation
from buildwise.flows.state import FlowRuntimeLimits
from buildwise.planning import policies
from fixtures.planning import (
    build_complex_failure_edge_case,
    build_critical_quality_requirement,
    build_llm_provider_integration_requirement,
    build_market_risk,
    build_market_unknown,
    build_privileged_integration_requirement,
    build_product_planning_inputs,
    build_security_risk,
    build_sensitive_data_requirement,
)


class TestShouldIncludeEarlyMarketContext:
    def test_explicit_request_selects_market(self) -> None:
        discovery, _ = build_product_planning_inputs()

        assert (
            policies.should_include_early_market_context(discovery, explicitly_requested=True)
            is True
        )

    def test_technical_only_tool_does_not_select_market(self) -> None:
        discovery, _ = build_product_planning_inputs()

        assert policies.should_include_early_market_context(discovery) is False

    def test_material_market_risk_selects_market(self) -> None:
        discovery, _ = build_product_planning_inputs(
            discovery_kwargs={"risks": [build_market_risk()]},
        )

        assert policies.should_include_early_market_context(discovery) is True

    def test_market_specialist_signal_selects_market(self) -> None:
        discovery, _ = build_product_planning_inputs(
            discovery_kwargs={"specialist_signals": {"pricing_strategy_required": True}},
        )

        assert policies.should_include_early_market_context(discovery) is True

    def test_weakly_defined_target_market_selects_market(self) -> None:
        discovery, _ = build_product_planning_inputs(
            discovery_kwargs={"unknowns": [build_market_unknown()]},
        )

        assert policies.should_include_early_market_context(discovery) is True

    def test_explicit_exclusion_overrides_signals(self) -> None:
        discovery, _ = build_product_planning_inputs(
            discovery_kwargs={"risks": [build_market_risk()]},
        )

        assert (
            policies.should_include_early_market_context(discovery, explicitly_excluded=True)
            is False
        )


class TestEvaluateSolutionArchitecture:
    def test_always_required(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_solution_architecture(discovery, product_planning)

        assert recommendation.specialist is SpecialistType.SOLUTION_ARCHITECTURE
        assert recommendation.required is True
        assert recommendation.reason is SpecialistSelectionReason.ALWAYS_REQUIRED

    def test_high_effort_for_real_time_processing(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={
                "real_time_processing_required": True,
                "capabilities": [CapabilityType.REAL_TIME],
            },
        )

        recommendation = policies.evaluate_solution_architecture(discovery, product_planning)

        assert recommendation.estimated_effort == "high"

    def test_medium_effort_by_default(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_solution_architecture(discovery, product_planning)

        assert recommendation.estimated_effort == "medium"


class TestEvaluateAiArchitecture:
    def test_ai_core_capability_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={"capabilities": [CapabilityType.AI_CORE]},
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.specialist is SpecialistType.AI_ARCHITECTURE
        assert recommendation.reason is SpecialistSelectionReason.AI_CAPABILITY_REQUIRED
        assert recommendation.estimated_effort == "high"

    def test_rag_capability_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={"capabilities": [CapabilityType.RAG], "rag_required": True},
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None

    def test_agentic_workflow_capability_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={
                "capabilities": [CapabilityType.AGENTIC_WORKFLOW],
                "agents_required": True,
            },
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None

    def test_ai_enabled_mvp_feature_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            ai_enabled_mvp_feature=True,
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.estimated_effort == "medium"

    def test_ai_functional_requirement_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            functional_requirement_category="ai",
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None

    def test_llm_provider_integration_selects_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            integration_requirements=[build_llm_provider_integration_requirement()],
        )

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is not None

    def test_no_ai_signal_does_not_select_ai(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_ai_architecture(discovery, product_planning)

        assert recommendation is None


class TestEvaluateSecurityArchitecture:
    def test_sensitive_data_selects_security(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            data_requirements=[build_sensitive_data_requirement()],
        )

        recommendation = policies.evaluate_security_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.SENSITIVE_DATA
        assert recommendation.estimated_effort == "high"

    def test_regulated_domain_selects_security(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={
                "regulated_domain_detected": True,
                "capabilities": [CapabilityType.REGULATED],
            },
        )

        recommendation = policies.evaluate_security_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.REGULATED_DOMAIN

    def test_privileged_integration_selects_security(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            integration_requirements=[build_privileged_integration_requirement()],
        )

        recommendation = policies.evaluate_security_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.EXTERNAL_INTEGRATIONS
        assert recommendation.estimated_effort == "medium"

    def test_high_security_risk_selects_security(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={"risks": [build_security_risk()]},
        )

        recommendation = policies.evaluate_security_architecture(discovery, product_planning)

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.HIGH_RISK

    def test_low_risk_prototype_omits_security(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_security_architecture(discovery, product_planning)

        assert recommendation is None


class TestEvaluateQaAndEvaluation:
    def test_ai_selection_selects_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=True,
            security_selected=False,
        )

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.AI_CAPABILITY_REQUIRED

    def test_critical_quality_requirement_selects_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            extra_non_functional_requirements=[build_critical_quality_requirement()],
        )

        recommendation = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=False,
            security_selected=False,
        )

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.PRODUCT_COMPLEXITY

    def test_high_risk_workflow_selects_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            discovery_kwargs={"risks": [build_security_risk()]},
        )

        recommendation = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=False,
            security_selected=False,
        )

        assert recommendation is not None
        assert recommendation.reason is SpecialistSelectionReason.HIGH_RISK

    def test_complex_failure_edge_case_selects_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs(
            edge_cases=[build_complex_failure_edge_case()],
        )

        recommendation = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=False,
            security_selected=False,
        )

        assert recommendation is not None

    def test_lightweight_prototype_omits_qa(self) -> None:
        discovery, product_planning = build_product_planning_inputs()

        recommendation = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=False,
            security_selected=False,
        )

        assert recommendation is None


def _solution_recommendation() -> SpecialistRecommendation:
    return SpecialistRecommendation(
        specialist=SpecialistType.SOLUTION_ARCHITECTURE,
        required=True,
        reason=SpecialistSelectionReason.ALWAYS_REQUIRED,
        explanation="Every blueprint requires solution architecture.",
        estimated_effort="medium",
    )


def _qa_recommendation(
    reason: SpecialistSelectionReason = SpecialistSelectionReason.PRODUCT_COMPLEXITY,
) -> SpecialistRecommendation:
    return SpecialistRecommendation(
        specialist=SpecialistType.QA_AND_EVALUATION,
        required=False,
        reason=reason,
        explanation="QA validates the release.",
        estimated_effort="medium",
    )


def _security_recommendation(
    reason: SpecialistSelectionReason = SpecialistSelectionReason.EXTERNAL_INTEGRATIONS,
) -> SpecialistRecommendation:
    return SpecialistRecommendation(
        specialist=SpecialistType.SECURITY_ARCHITECTURE,
        required=False,
        reason=reason,
        explanation="Security reviews the integration surface.",
        estimated_effort="medium",
    )


class TestApplyBudgetPolicy:
    def test_approved_full_plan(self) -> None:
        recommendations = [_solution_recommendation(), _qa_recommendation()]

        selected, budget = policies.apply_budget_policy(
            recommendations,
            limits=FlowRuntimeLimits(),
            explicitly_requested=set(),
        )

        assert budget.decision is BudgetDecisionType.APPROVED
        assert budget.excluded_specialists == []
        assert {recommendation.specialist for recommendation in selected} == {
            SpecialistType.SOLUTION_ARCHITECTURE,
            SpecialistType.QA_AND_EVALUATION,
        }

    def test_approved_with_optional_exclusions(self) -> None:
        recommendations = [
            _solution_recommendation(),
            _security_recommendation(),
            _qa_recommendation(),
        ]
        limits = FlowRuntimeLimits(maximum_agent_executions=2)

        selected, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=set(),
        )

        assert budget.decision is BudgetDecisionType.APPROVED_WITH_LIMITS
        assert SpecialistType.QA_AND_EVALUATION in budget.excluded_specialists
        assert budget.limitations
        assert {recommendation.specialist for recommendation in selected} == {
            SpecialistType.SOLUTION_ARCHITECTURE,
            SpecialistType.SECURITY_ARCHITECTURE,
        }

    def test_explicit_request_survives_budget_pressure(self) -> None:
        recommendations = [
            _solution_recommendation(),
            _security_recommendation(),
            _qa_recommendation(),
        ]
        limits = FlowRuntimeLimits(maximum_agent_executions=2)

        _, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested={SpecialistType.QA_AND_EVALUATION},
        )

        assert budget.decision is BudgetDecisionType.APPROVED_WITH_LIMITS
        assert SpecialistType.QA_AND_EVALUATION not in budget.excluded_specialists
        assert SpecialistType.SECURITY_ARCHITECTURE in budget.excluded_specialists

    def test_deferred_when_protected_coverage_exceeds_limits(self) -> None:
        recommendations = [
            _solution_recommendation(),
            _security_recommendation(reason=SpecialistSelectionReason.SENSITIVE_DATA),
            _qa_recommendation(reason=SpecialistSelectionReason.AI_CAPABILITY_REQUIRED),
        ]
        limits = FlowRuntimeLimits(maximum_agent_executions=1)

        selected, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=set(),
        )

        assert budget.decision is BudgetDecisionType.DEFERRED
        assert selected == []

    def test_rejected_when_cost_floor_exceeds_limit(self) -> None:
        recommendations = [_solution_recommendation()]
        limits = FlowRuntimeLimits(maximum_estimated_cost_usd=0.0)

        selected, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=set(),
        )

        assert budget.decision is BudgetDecisionType.REJECTED
        assert selected == []

    def test_every_exclusion_has_a_limitation(self) -> None:
        recommendations = [
            _solution_recommendation(),
            _security_recommendation(),
            _qa_recommendation(),
        ]
        limits = FlowRuntimeLimits(maximum_agent_executions=1)

        _, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=set(),
        )

        assert len(budget.limitations) == len(budget.excluded_specialists)
