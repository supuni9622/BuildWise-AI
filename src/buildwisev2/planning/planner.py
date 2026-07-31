"""The deterministic Specialist Planner — public application service.

Pure Python, no CrewAI imports, no LLM calls, no side effects. Converts
validated Discovery + Product Planning signals into the single canonical
``SpecialistExecutionPlan`` consumed by the Technical Planning Crew.
"""

from __future__ import annotations

from buildwisev2.domain.common import FlowRuntimeLimits, SpecialistType
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.planning_results import ProductPlanningResult
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    EffortLevel,
    SpecialistExecutionPlan,
    SpecialistRecommendation,
    SpecialistSelectionReason,
)
from buildwisev2.planning import execution_graph, policies


class SpecialistPlanner:
    """Stateless, deterministic specialist-planning service."""

    def should_include_early_market_context(
        self,
        *,
        discovery: DiscoveryResult,
        explicitly_requested: bool = False,
    ) -> bool:
        return policies.should_include_early_market_context(
            discovery,
            explicitly_requested=explicitly_requested,
        )

    def create_execution_plan(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        limits: FlowRuntimeLimits,
        explicitly_requested: set[SpecialistType] | None = None,
        explicitly_excluded: set[SpecialistType] | None = None,
    ) -> SpecialistExecutionPlan:
        if discovery.session_id != product_planning.session_id:
            raise ValueError(
                "Discovery and Product Planning results belong to different sessions: "
                f"{discovery.session_id} != {product_planning.session_id}"
            )
        if not discovery.completeness.can_continue:
            raise ValueError(
                "Discovery has unresolved blocking unknowns; the planner cannot run until "
                "Discovery reports completeness.can_continue=True."
            )

        requested = explicitly_requested or set()
        excluded = explicitly_excluded or set()
        conflicting = requested & excluded
        if conflicting:
            raise ValueError(
                f"Specialists cannot be both requested and excluded: {sorted(conflicting)}"
            )

        recommendations = self._collect_recommendations(discovery, product_planning, requested)
        self._enforce_exclusions(recommendations, excluded)

        kept_recommendations, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=requested,
        )

        selected = {rec.specialist for rec in kept_recommendations} - set(
            budget.excluded_specialists
        )

        if budget.decision.value in {"deferred", "rejected"}:
            return SpecialistExecutionPlan(
                recommendations=kept_recommendations,
                execution_groups=[],
                dependencies=[],
                budget=budget,
                execution_summary=self._summarize(kept_recommendations, budget, selected=set()),
            )

        dependencies = execution_graph.build_dependencies(selected_specialists=selected)
        groups = execution_graph.build_execution_groups(
            selected_specialists=selected,
            dependencies=dependencies,
        )
        execution_graph.validate_execution_graph(
            selected_specialists=selected,
            dependencies=dependencies,
            execution_groups=groups,
        )

        return SpecialistExecutionPlan(
            recommendations=kept_recommendations,
            execution_groups=groups,
            dependencies=dependencies,
            budget=budget,
            execution_summary=self._summarize(kept_recommendations, budget, selected=selected),
        )

    def _collect_recommendations(
        self,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        requested: set[SpecialistType],
    ) -> list[SpecialistRecommendation]:
        recommendations = [policies.evaluate_solution_architecture(discovery, product_planning)]

        ai_rec = policies.evaluate_ai_architecture(discovery, product_planning)
        ai_rec = ai_rec or self._explicit_fallback(SpecialistType.AI_ARCHITECTURE, requested)
        if ai_rec is not None:
            recommendations.append(ai_rec)

        security_rec = policies.evaluate_security_architecture(discovery, product_planning)
        security_rec = security_rec or self._explicit_fallback(
            SpecialistType.SECURITY_ARCHITECTURE, requested
        )
        if security_rec is not None:
            recommendations.append(security_rec)

        qa_rec = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=ai_rec is not None,
            security_selected=security_rec is not None,
        )
        qa_rec = qa_rec or self._explicit_fallback(SpecialistType.QA_AND_EVALUATION, requested)
        if qa_rec is not None:
            recommendations.append(qa_rec)

        return recommendations

    @staticmethod
    def _explicit_fallback(
        specialist: SpecialistType,
        requested: set[SpecialistType],
    ) -> SpecialistRecommendation | None:
        if specialist not in requested:
            return None
        return SpecialistRecommendation(
            specialist=specialist,
            required=False,
            reason=SpecialistSelectionReason.EXPLICIT_USER_REQUEST,
            explanation=f"The user explicitly requested {specialist.value}.",
            estimated_effort=EffortLevel.MEDIUM,
        )

    @staticmethod
    def _enforce_exclusions(
        recommendations: list[SpecialistRecommendation],
        excluded: set[SpecialistType],
    ) -> None:
        by_specialist = {rec.specialist: rec for rec in recommendations}
        for specialist in excluded:
            rec = by_specialist.get(specialist)
            if rec is not None and rec.required:
                raise ValueError(
                    f"{specialist.value} is mandatory for this consultation and cannot be "
                    "explicitly excluded."
                )

    @staticmethod
    def _summarize(
        recommendations: list[SpecialistRecommendation],
        budget: BudgetDecision,
        *,
        selected: set[SpecialistType],
    ) -> str:
        selected_names = ", ".join(sorted(s.value for s in selected)) or "none"
        parts = [f"Selected specialists: {selected_names}."]
        for rec in recommendations:
            status = "selected" if rec.specialist in selected else "excluded by budget"
            parts.append(f"{rec.specialist.value} ({status}): {rec.explanation}")
        parts.append(f"Budget decision: {budget.decision.value} — {budget.explanation}")
        if budget.limitations:
            parts.append("Limitations: " + "; ".join(budget.limitations))
        return " ".join(parts)


SPECIALIST_PLANNER = SpecialistPlanner()
