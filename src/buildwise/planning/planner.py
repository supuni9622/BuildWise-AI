"""Deterministic Specialist Planner application service.

``SpecialistPlanner`` is the only component that decides which technical
specialists run, why, in what order, and what must be omitted under runtime
or budget pressure. It is ordinary, framework-independent Python: it never
constructs a CrewAI Agent, Task, or Crew, never calls an LLM, and never
touches the database or Flow state.
"""

from __future__ import annotations

from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import SpecialistSelectionReason, SpecialistType
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.specialist_planning import (
    BudgetDecision,
    SpecialistExecutionPlan,
    SpecialistRecommendation,
)
from buildwise.flows.state import FlowRuntimeLimits
from buildwise.planning import execution_graph, policies

_TECHNICAL_SPECIALISTS = frozenset(
    {
        SpecialistType.SOLUTION_ARCHITECTURE,
        SpecialistType.AI_ARCHITECTURE,
        SpecialistType.SECURITY_ARCHITECTURE,
        SpecialistType.QA_AND_EVALUATION,
    }
)

_DEFAULT_EXPLICIT_REQUEST_EFFORT = "medium"


class SpecialistPlanningError(RuntimeError):
    """Raised when the deterministic Specialist Planner cannot produce a plan."""


class SpecialistPlanner:
    """Deterministic policy service for specialist selection and execution planning.

    Two distinct decisions are exposed as separate methods, matching the two
    points in the Flow where they are needed:

    - ``should_include_early_market_context`` runs before the Product
      Planning Crew is constructed and only has ``DiscoveryResult``
      available.
    - ``create_execution_plan`` runs after Product Planning completes and
      selects the technical specialists for the Technical Planning Crew.
    """

    def should_include_early_market_context(
        self,
        *,
        discovery: DiscoveryResult,
        explicitly_requested: bool = False,
        explicitly_excluded: bool = False,
    ) -> bool:
        """Decide whether Market & GTM should join the Product Planning Crew."""

        return policies.should_include_early_market_context(
            discovery,
            explicitly_requested=explicitly_requested,
            explicitly_excluded=explicitly_excluded,
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
        """Build the deterministic technical specialist execution plan.

        Raises:
            SpecialistPlanningError: If the inputs do not share a session,
                Discovery cannot safely continue, a specialist is both
                requested and excluded, a non-technical specialist is
                requested or excluded here, or a mandatory or
                safety-critical specialist would be excluded.
        """

        requested = set(explicitly_requested or ())
        excluded = set(explicitly_excluded or ())

        self._validate_request(
            discovery=discovery,
            product_planning=product_planning,
            requested=requested,
            excluded=excluded,
        )

        recommendations, user_excluded = self._select_recommendations(
            discovery=discovery,
            product_planning=product_planning,
            requested=requested,
            excluded=excluded,
        )

        selected, budget = policies.apply_budget_policy(
            recommendations,
            limits=limits,
            explicitly_requested=requested,
        )

        selected_specialists = {recommendation.specialist for recommendation in selected}

        dependencies = execution_graph.build_dependencies(
            selected_specialists=selected_specialists,
        )
        groups = execution_graph.build_execution_groups(
            selected_specialists=selected_specialists,
            dependencies=dependencies,
        )
        execution_graph.validate_execution_graph(
            selected_specialists=selected_specialists,
            dependencies=dependencies,
            execution_groups=groups,
        )

        execution_summary = self._build_execution_summary(
            selected=selected,
            budget=budget,
            user_excluded=user_excluded,
        )

        return SpecialistExecutionPlan(
            recommendations=selected,
            execution_groups=groups,
            dependencies=dependencies,
            budget=budget,
            execution_summary=execution_summary,
        )

    def _validate_request(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        requested: set[SpecialistType],
        excluded: set[SpecialistType],
    ) -> None:
        if discovery.session_id != product_planning.session_id:
            raise SpecialistPlanningError(
                "DiscoveryResult and ProductPlanningResult must share the same session_id."
            )

        if not discovery.completeness.can_continue:
            raise SpecialistPlanningError(
                "Discovery contains blocking unknowns; specialist planning "
                "cannot continue until Discovery can_continue is true."
            )

        contradictory = requested.intersection(excluded)

        if contradictory:
            formatted = ", ".join(sorted(specialist.value for specialist in contradictory))
            raise SpecialistPlanningError(
                f"Specialists cannot be both explicitly requested and excluded: {formatted}."
            )

        non_technical_requested = requested.difference(_TECHNICAL_SPECIALISTS)
        non_technical_excluded = excluded.difference(_TECHNICAL_SPECIALISTS)

        if non_technical_requested or non_technical_excluded:
            formatted = ", ".join(
                sorted(
                    specialist.value
                    for specialist in non_technical_requested.union(non_technical_excluded)
                )
            )
            raise SpecialistPlanningError(
                "create_execution_plan only accepts technical specialists "
                f"(solution, ai, security, qa); received: {formatted}. Market "
                "& GTM is decided by should_include_early_market_context."
            )

    def _select_recommendations(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        requested: set[SpecialistType],
        excluded: set[SpecialistType],
    ) -> tuple[list[SpecialistRecommendation], list[SpecialistType]]:
        solution = policies.evaluate_solution_architecture(discovery, product_planning)
        ai = policies.evaluate_ai_architecture(discovery, product_planning)
        security = policies.evaluate_security_architecture(discovery, product_planning)
        qa = policies.evaluate_qa_and_evaluation(
            discovery,
            product_planning,
            ai_selected=ai is not None,
            security_selected=security is not None,
        )

        user_excluded: list[SpecialistType] = []
        recommendations: list[SpecialistRecommendation] = []

        for specialist, baseline in (
            (SpecialistType.SOLUTION_ARCHITECTURE, solution),
            (SpecialistType.AI_ARCHITECTURE, ai),
            (SpecialistType.SECURITY_ARCHITECTURE, security),
            (SpecialistType.QA_AND_EVALUATION, qa),
        ):
            reconciled = self._reconcile(
                specialist=specialist,
                baseline=baseline,
                requested=requested,
                excluded=excluded,
            )

            if reconciled is None:
                if baseline is not None:
                    user_excluded.append(specialist)
                continue

            recommendations.append(reconciled)

        return recommendations, user_excluded

    def _reconcile(
        self,
        *,
        specialist: SpecialistType,
        baseline: SpecialistRecommendation | None,
        requested: set[SpecialistType],
        excluded: set[SpecialistType],
    ) -> SpecialistRecommendation | None:
        """Merge a policy baseline recommendation with explicit user intent."""

        if baseline is not None and specialist in excluded:
            if policies.is_protected_from_exclusion(baseline):
                raise SpecialistPlanningError(
                    f"{specialist.value} cannot be excluded: {baseline.explanation}"
                )

            return None

        if baseline is None and specialist in requested:
            return SpecialistRecommendation(
                specialist=specialist,
                required=False,
                reason=SpecialistSelectionReason.EXPLICIT_USER_REQUEST,
                explanation=(f"{specialist.value} was explicitly requested for this consultation."),
                estimated_effort=_DEFAULT_EXPLICIT_REQUEST_EFFORT,
            )

        return baseline

    def _build_execution_summary(
        self,
        *,
        selected: list[SpecialistRecommendation],
        budget: BudgetDecision,
        user_excluded: list[SpecialistType],
    ) -> str:
        if not selected:
            return (
                f"No specialists are selected for execution. Budget decision: "
                f"{budget.decision.value}. {budget.explanation}"
            )

        selected_summary = ", ".join(recommendation.specialist.value for recommendation in selected)

        parts = [
            f"Selected {len(selected)} technical specialist(s) for this "
            f"consultation: {selected_summary}.",
            f"Budget decision: {budget.decision.value}.",
        ]

        if user_excluded:
            formatted = ", ".join(sorted(specialist.value for specialist in user_excluded))
            parts.append(f"Excluded by explicit user request: {formatted}.")

        if budget.excluded_specialists:
            formatted = ", ".join(
                sorted(specialist.value for specialist in budget.excluded_specialists)
            )
            parts.append(f"Excluded by budget policy: {formatted}.")

        return " ".join(parts)
