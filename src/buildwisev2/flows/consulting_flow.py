"""The BuildWise v2 Consulting Flow — the sole orchestrator.

Owns state, routing, Crew execution order, conditional specialist
execution, and revision routing. Contains no specialist-selection policy
(that lives in ``buildwisev2.planning``) and no specialist reasoning (that
lives in the Crews/Tasks/Agents layers).

Pause/resume for clarification is in-process only: the Flow instance is
kept alive by the caller between the "awaiting_clarification" stage and a
second ``kickoff()`` call carrying a populated ``clarification_context``.

Cross-process crash recovery is supported when a ``persistence`` backend
is supplied: after every stage transition, ``self.state`` is checkpointed
via the native ``crewai.flow.persistence.FlowPersistence`` interface. A
restored session picks up from ``run_discovery`` again on the next
``kickoff()`` call (CrewAI's persistence restores ``self.state`` but not
already-completed-method bookkeeping — see ``PROGRESS.md`` for the exact
resume contract).
"""

from __future__ import annotations

from crewai import Crew
from crewai.crews.crew_output import CrewOutput
from crewai.flow.flow import Flow, listen, router, start
from crewai.flow.persistence import FlowPersistence
from pydantic import BaseModel

from buildwisev2.agents.factory import AgentFactory
from buildwisev2.config.settings import Settings, get_settings
from buildwisev2.crews.discovery import build_discovery_kickoff_inputs, create_discovery_crew
from buildwisev2.crews.lead_review import build_lead_review_kickoff_inputs, create_lead_review_crew
from buildwisev2.crews.product_planning import (
    build_product_planning_kickoff_inputs,
    create_product_planning_crew,
)
from buildwisev2.crews.technical_planning import (
    build_technical_planning_kickoff_inputs,
    create_technical_planning_crew,
)
from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.blueprint import ProductBlueprint
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.planning_results import ProductPlanningResult, TechnicalPlanningResult
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.qa import QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.review import LeadReview, RevisionRequest
from buildwisev2.domain.security_architecture import SecurityArchitecture
from buildwisev2.flows.routing import (
    DiscoveryRoute,
    ReviewRoute,
    force_continue_discovery,
    group_revisions_by_crew,
    route_discovery,
    route_lead_review,
)
from buildwisev2.flows.state import ConsultingFlowState, FlowStage
from buildwisev2.planning.planner import SPECIALIST_PLANNER, SpecialistPlanner
from buildwisev2.reporting.blueprint_builder import build_blueprint


def _output_by_name(crew_output: CrewOutput, name: str) -> BaseModel | None:
    for task_output in crew_output.tasks_output:
        if task_output.name == name and task_output.pydantic is not None:
            return task_output.pydantic
    return None


def _kickoff(crew: Crew, inputs: dict[str, str]) -> CrewOutput:
    """Run a Crew and narrow the result to ``CrewOutput``.

    No BuildWise v2 Crew enables ``stream=True``, so ``kickoff`` always
    returns ``CrewOutput`` at runtime; this only satisfies the static type
    checker without a per-call ``# type: ignore``.
    """

    output = crew.kickoff(inputs=inputs)
    if not isinstance(output, CrewOutput):
        raise RuntimeError("Streaming Crew output is not supported by ConsultingFlow.")
    return output


class ConsultingFlow(Flow[ConsultingFlowState]):
    """Native CrewAI Flow orchestrating Discovery -> Product Planning ->
    Specialist Planning -> Technical Planning -> Lead Review -> revision
    routing -> blueprint assembly.
    """

    def __init__(
        self,
        *,
        agent_factory: AgentFactory | None = None,
        settings: Settings | None = None,
        planner: SpecialistPlanner | None = None,
        persistence: FlowPersistence | None = None,
    ) -> None:
        super().__init__(persistence=persistence)
        self._settings = settings or get_settings()
        self._agent_factory = agent_factory or AgentFactory(self._settings)
        self._planner = planner or SPECIALIST_PLANNER
        self._include_market_and_gtm = False

    def _checkpoint(self, method_name: str) -> None:
        """Best-effort state checkpoint after a stage transition.

        No-op when no ``persistence`` backend was supplied. Failures are
        swallowed rather than raised — a checkpoint failure must never
        abort an otherwise-successful consultation stage.
        """

        if self.persistence is None:
            return
        try:
            self.persistence.save_state(
                flow_uuid=self.state.id,
                method_name=method_name,
                state_data=self.state.model_dump(mode="json"),
            )
        except Exception:  # checkpointing must never break the Flow
            self.state.warnings.append(f"Failed to checkpoint state after {method_name}.")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    @start()
    def run_discovery(self) -> DiscoveryResult:
        self.state.stage = FlowStage.DISCOVERY
        if self.state.product_idea is None:
            raise ValueError("ConsultingFlow requires state.product_idea before kickoff.")

        crew = create_discovery_crew(agent_factory=self._agent_factory, settings=self._settings)
        inputs = build_discovery_kickoff_inputs(
            product_idea=self.state.product_idea,
            clarification_context=self.state.clarification_context,
        )
        output = _kickoff(crew, inputs)
        result = output.pydantic
        if not isinstance(result, DiscoveryResult):
            raise RuntimeError("Discovery Crew did not return a DiscoveryResult.")

        self.state.discovery_result = result
        self._checkpoint("run_discovery")
        return result

    @router(run_discovery)
    def route_after_discovery(self) -> str:
        discovery = self.state.discovery_result
        assert discovery is not None
        round_number = (
            self.state.clarification_context.clarification_round
            if self.state.clarification_context is not None
            else 0
        )
        route = route_discovery(
            discovery, clarification_round=round_number, limits=self.state.limits
        )
        if route == DiscoveryRoute.CONTINUE and not discovery.completeness.can_continue:
            # Round budget exhausted while Discovery still reports incompleteness.
            # Reconcile the artifact so downstream components (the planner in
            # particular) don't reject it as internally inconsistent.
            self.state.discovery_result = force_continue_discovery(discovery)
            self._checkpoint("route_after_discovery")
        return route.value

    @listen(DiscoveryRoute.FAIL.value)
    def handle_discovery_failure(self) -> None:
        self.state.stage = FlowStage.FAILED
        self.state.errors.append("Discovery Crew could not produce a usable assessment.")
        self._checkpoint("handle_discovery_failure")

    @listen(DiscoveryRoute.CLARIFY.value)
    def handle_clarification_needed(self) -> None:
        self.state.stage = FlowStage.AWAITING_CLARIFICATION
        # The Flow pauses here. The caller resumes by supplying a populated
        # ProductIdeaContext and calling kickoff() again on this same
        # instance, which re-runs run_discovery with the new context.
        self._checkpoint("handle_clarification_needed")

    # ------------------------------------------------------------------
    # Product Planning
    # ------------------------------------------------------------------

    @listen(DiscoveryRoute.CONTINUE.value)
    def run_product_planning(self) -> ProductPlanningResult:
        self.state.stage = FlowStage.PRODUCT_PLANNING
        discovery = self.state.discovery_result
        assert discovery is not None

        self._include_market_and_gtm = self._planner.should_include_early_market_context(
            discovery=discovery
        )

        crew = create_product_planning_crew(
            include_market_and_gtm=self._include_market_and_gtm,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        inputs = build_product_planning_kickoff_inputs(discovery_result=discovery)
        output = _kickoff(crew, inputs)

        result = self._assemble_product_planning_result(discovery, output)
        self.state.product_planning_result = result
        self._checkpoint("run_product_planning")
        return result

    def _assemble_product_planning_result(
        self,
        discovery: DiscoveryResult,
        output: CrewOutput,
        *,
        prior_result: ProductPlanningResult | None = None,
    ) -> ProductPlanningResult:
        """Assemble the aggregate result, falling back to ``prior_result`` for
        any task the Crew skipped this run (revision-aware composition)."""

        product_definition = _output_by_name(output, "product_definition") or (
            prior_result.product_definition if prior_result is not None else None
        )
        requirements = _output_by_name(output, "requirements") or (
            prior_result.requirements if prior_result is not None else None
        )
        if not isinstance(product_definition, ProductDefinition) or not isinstance(
            requirements, RequirementsSpecification
        ):
            raise RuntimeError("Product Planning Crew did not produce both required artifacts.")
        market_and_gtm = _output_by_name(output, "market_and_gtm") or (
            prior_result.market_and_gtm if prior_result is not None else None
        )
        return ProductPlanningResult(
            session_id=discovery.session_id,
            market_and_gtm=market_and_gtm
            if isinstance(market_and_gtm, MarketAndGTMStrategy)
            else None,
            product_definition=product_definition,
            requirements=requirements,
        )

    # ------------------------------------------------------------------
    # Specialist Planning (deterministic, not a Crew)
    # ------------------------------------------------------------------

    @listen(run_product_planning)
    def run_specialist_planning(self) -> None:
        self.state.stage = FlowStage.SPECIALIST_PLANNING
        discovery = self.state.discovery_result
        product_planning = self.state.product_planning_result
        assert discovery is not None
        assert product_planning is not None

        self.state.specialist_plan = self._planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=self.state.limits,
        )
        self._checkpoint("run_specialist_planning")

    # ------------------------------------------------------------------
    # Technical Planning
    # ------------------------------------------------------------------

    @listen(run_specialist_planning)
    def run_technical_planning(self) -> TechnicalPlanningResult:
        self.state.stage = FlowStage.TECHNICAL_PLANNING
        plan = self.state.specialist_plan
        product_planning = self.state.product_planning_result
        assert plan is not None
        assert product_planning is not None

        crew = create_technical_planning_crew(
            specialist_plan=plan,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        inputs = build_technical_planning_kickoff_inputs(requirements=product_planning.requirements)
        output = _kickoff(crew, inputs)

        result = self._assemble_technical_planning_result(product_planning, output)
        self.state.technical_planning_result = result
        self._checkpoint("run_technical_planning")
        return result

    def _assemble_technical_planning_result(
        self,
        product_planning: ProductPlanningResult,
        output: CrewOutput,
        *,
        prior_result: TechnicalPlanningResult | None = None,
    ) -> TechnicalPlanningResult:
        """Assemble the aggregate result, falling back to ``prior_result`` for
        any task the Crew skipped this run (revision-aware composition)."""

        solution_architecture = _output_by_name(output, "solution_architecture") or (
            prior_result.solution_architecture if prior_result is not None else None
        )
        if not isinstance(solution_architecture, SolutionArchitecture):
            raise RuntimeError("Technical Planning Crew did not produce a SolutionArchitecture.")
        ai_architecture = _output_by_name(output, "ai_architecture") or (
            prior_result.ai_architecture if prior_result is not None else None
        )
        security_architecture = _output_by_name(output, "security_architecture") or (
            prior_result.security_architecture if prior_result is not None else None
        )
        qa_evaluation = _output_by_name(output, "qa_evaluation") or (
            prior_result.qa_evaluation if prior_result is not None else None
        )
        return TechnicalPlanningResult(
            session_id=product_planning.session_id,
            solution_architecture=solution_architecture,
            ai_architecture=ai_architecture
            if isinstance(ai_architecture, AIArchitecture)
            else None,
            security_architecture=(
                security_architecture
                if isinstance(security_architecture, SecurityArchitecture)
                else None
            ),
            qa_evaluation=qa_evaluation if isinstance(qa_evaluation, QAEvaluationPlan) else None,
        )

    # ------------------------------------------------------------------
    # Lead Review
    # ------------------------------------------------------------------

    @listen(run_technical_planning)
    def run_lead_review(self) -> LeadReview:
        return self._execute_lead_review()

    def _execute_lead_review(self) -> LeadReview:
        self.state.stage = FlowStage.LEAD_REVIEW
        discovery = self.state.discovery_result
        product_planning = self.state.product_planning_result
        plan = self.state.specialist_plan
        technical_planning = self.state.technical_planning_result
        assert discovery is not None
        assert product_planning is not None
        assert plan is not None
        assert technical_planning is not None

        crew = create_lead_review_crew(agent_factory=self._agent_factory, settings=self._settings)
        inputs = build_lead_review_kickoff_inputs(
            discovery_result=discovery,
            product_definition=product_planning.product_definition,
            requirements=product_planning.requirements,
            specialist_plan=plan,
            solution_architecture=technical_planning.solution_architecture,
            market_and_gtm=product_planning.market_and_gtm,
            ai_architecture=technical_planning.ai_architecture,
            security_architecture=technical_planning.security_architecture,
            qa_evaluation=technical_planning.qa_evaluation,
            revision_history=self.state.revision_history,
        )
        output = _kickoff(crew, inputs)
        result = output.pydantic
        if not isinstance(result, LeadReview):
            raise RuntimeError("Lead Review Crew did not return a LeadReview.")

        self.state.lead_review = result
        self._checkpoint("_execute_lead_review")
        return result

    @router(run_lead_review)
    def route_after_review(self) -> str:
        return self._decide_review_route()

    def _decide_review_route(self) -> str:
        review = self.state.lead_review
        assert review is not None
        return route_lead_review(
            review,
            revision_count=self.state.revision_count,
            limits=self.state.limits,
        ).value

    # ------------------------------------------------------------------
    # Revision loop
    # ------------------------------------------------------------------

    @listen(ReviewRoute.REVISE.value)
    def run_revisions(self) -> None:
        self.state.stage = FlowStage.REVISION
        review = self.state.lead_review
        assert review is not None

        self.state.revision_count += 1
        self.state.revision_history.extend(review.revision_requests)
        product_requests, technical_requests = group_revisions_by_crew(review.revision_requests)

        if product_requests:
            self._rerun_product_planning(product_requests)
        if technical_requests:
            self._rerun_technical_planning(technical_requests)
        self._checkpoint("run_revisions")

    def _rerun_product_planning(self, revision_requests: list[RevisionRequest]) -> None:
        discovery = self.state.discovery_result
        prior_result = self.state.product_planning_result
        assert discovery is not None
        assert prior_result is not None
        crew = create_product_planning_crew(
            include_market_and_gtm=self._include_market_and_gtm,
            agent_factory=self._agent_factory,
            settings=self._settings,
            revision_requests=revision_requests,
            prior_result=prior_result,
        )
        inputs = build_product_planning_kickoff_inputs(
            discovery_result=discovery,
            prior_result=prior_result,
        )
        output = _kickoff(crew, inputs)
        self.state.product_planning_result = self._assemble_product_planning_result(
            discovery, output, prior_result=prior_result
        )
        # Requirements were derived from Product Definition; re-run specialist
        # planning too since capability-affecting requirements may have changed.
        self.state.specialist_plan = self._planner.create_execution_plan(
            discovery=discovery,
            product_planning=self.state.product_planning_result,
            limits=self.state.limits,
        )
        self._checkpoint("_rerun_product_planning")

    def _rerun_technical_planning(self, revision_requests: list[RevisionRequest]) -> None:
        plan = self.state.specialist_plan
        product_planning = self.state.product_planning_result
        prior_result = self.state.technical_planning_result
        assert plan is not None
        assert product_planning is not None
        assert prior_result is not None
        crew = create_technical_planning_crew(
            specialist_plan=plan,
            agent_factory=self._agent_factory,
            settings=self._settings,
            revision_requests=revision_requests,
            prior_result=prior_result,
        )
        inputs = build_technical_planning_kickoff_inputs(
            requirements=product_planning.requirements,
            prior_result=prior_result,
        )
        output = _kickoff(crew, inputs)
        self.state.technical_planning_result = self._assemble_technical_planning_result(
            product_planning, output, prior_result=prior_result
        )
        self._checkpoint("_rerun_technical_planning")

    @listen(run_revisions)
    def rerun_lead_review(self) -> LeadReview:
        return self._execute_lead_review()

    @router(rerun_lead_review)
    def route_after_revision_review(self) -> str:
        return self._decide_review_route()

    # ------------------------------------------------------------------
    # Terminal states
    # ------------------------------------------------------------------

    @listen(ReviewRoute.REJECT.value)
    def handle_rejection(self) -> None:
        self.state.stage = FlowStage.REJECTED
        review = self.state.lead_review
        if review is not None and review.rejection_rationale:
            self.state.errors.append(review.rejection_rationale)
        self._checkpoint("handle_rejection")

    @listen(ReviewRoute.ASSEMBLE_BLUEPRINT.value)
    def on_blueprint_ready(self) -> ProductBlueprint:
        """Deterministic blueprint assembly boundary.

        Calls ``reporting.build_blueprint`` — a pure rendering step, no LLM
        call — per ``06_consulting_flow_prd.md`` item 14 ("Call
        blueprint_builder.build(...) after approval.").
        """

        review = self.state.lead_review
        discovery = self.state.discovery_result
        product_planning = self.state.product_planning_result
        plan = self.state.specialist_plan
        technical_planning = self.state.technical_planning_result
        assert review is not None
        assert discovery is not None
        assert product_planning is not None
        assert plan is not None
        assert technical_planning is not None

        if review.decision.value == "approved_with_limitations" or (
            self.state.revision_count >= self.state.limits.maximum_specialist_revisions
            and review.decision.value == "revision_required"
        ):
            self.state.stage = FlowStage.COMPLETED_WITH_LIMITATIONS
        else:
            self.state.stage = FlowStage.COMPLETED

        blueprint = build_blueprint(
            discovery=discovery,
            product_definition=product_planning.product_definition,
            requirements=product_planning.requirements,
            specialist_plan=plan,
            solution_architecture=technical_planning.solution_architecture,
            lead_review=review,
            market_and_gtm=product_planning.market_and_gtm,
            ai_architecture=technical_planning.ai_architecture,
            security_architecture=technical_planning.security_architecture,
            qa_evaluation=technical_planning.qa_evaluation,
        )
        self.state.blueprint = blueprint
        self._checkpoint("on_blueprint_ready")
        return blueprint
