"""Main CrewAI Flow for a BuildWise consulting session."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, Protocol, cast

import structlog
from crewai import Crew, CrewOutput
from crewai.flow.flow import Flow, listen, or_, router, start
from crewai.flow.persistence import persist
from crewai.flow.persistence.base import FlowPersistence
from pydantic import BaseModel, PrivateAttr

from buildwise.agents.factory import AgentFactory
from buildwise.application.cost_aggregator import ProjectCostAggregator
from buildwise.application.usage_aggregator import UsageAggregator
from buildwise.config.settings import Settings, get_settings
from buildwise.crews.discovery import (
    bind_discovery_session,
    create_discovery_crew,
    merge_discovery_refinement,
)
from buildwise.crews.lead_review import create_lead_review_crew
from buildwise.crews.product_planning import (
    assemble_product_planning_result,
    create_product_planning_crew,
)
from buildwise.crews.technical_planning import (
    assemble_technical_planning_result,
    create_technical_planning_crew,
)
from buildwise.domain.blueprint import ProductBlueprint
from buildwise.domain.common import WarningMessage, generate_uuid
from buildwise.domain.costs import CostSummary
from buildwise.domain.discovery import DiscoveryRefinement, DiscoveryResult
from buildwise.domain.enums import (
    ReviewDecision,
    SessionStage,
    SessionStatus,
    SpecialistType,
)
from buildwise.domain.intake import ClarificationAnswer, ProductIdeaContext
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.review import LeadReview, RevisionRequest
from buildwise.domain.session import SessionError
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.domain.usage import UsageSummary
from buildwise.flows.revisions import (
    PRODUCT_REVISION_TARGETS,
    TECHNICAL_REVISION_TARGETS,
    route_targeted_revision,
)
from buildwise.flows.routing import (
    FlowRoute,
    apply_specialist_execution_plan,
    route_after_discovery,
    route_after_review,
    route_after_specialist_planning,
    route_after_specialists,
)
from buildwise.flows.state import BuildWiseFlowState
from buildwise.planning.planner import SpecialistPlanner
from buildwise.reporting.assembler import BlueprintAssembler
from buildwise.reporting.storage import (
    BlueprintReportStorage,
    create_blueprint_report_storage,
)
from buildwise.validation.output_validator import validate_output

logger = structlog.get_logger(__name__)

CrewFactory = Callable[..., Crew]


class _NullFlowPersistence(FlowPersistence):
    """Enable persistence hooks while making persistence opt-in per Flow instance."""

    persistence_type: str = "_NullFlowPersistence"

    def init_db(self) -> None:
        pass

    def save_state(
        self,
        flow_uuid: str,
        method_name: str,
        state_data: dict[str, Any] | BaseModel,
    ) -> None:
        del flow_uuid, method_name, state_data

    def load_state(self, flow_uuid: str) -> dict[str, Any] | None:
        del flow_uuid
        return None


class BlueprintBuilder(Protocol):
    """Boundary for deterministic blueprint assembly."""

    def build(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        specialist_plan: SpecialistExecutionPlan,
        technical_planning: TechnicalPlanningResult,
        cost_summary: CostSummary,
        lead_review: LeadReview,
        usage_summary: UsageSummary,
    ) -> ProductBlueprint:
        """Build the approved final blueprint."""


@persist(_NullFlowPersistence())
class BuildWiseConsultingFlow(Flow[BuildWiseFlowState]):
    """Native CrewAI Flow connecting BuildWise's four business Crews."""

    _settings: Settings = PrivateAttr()
    _agent_factory: AgentFactory = PrivateAttr()
    _planner: SpecialistPlanner = PrivateAttr()
    _project_cost_aggregator: ProjectCostAggregator = PrivateAttr()
    _usage_aggregator: UsageAggregator = PrivateAttr()
    _blueprint_builder: BlueprintBuilder = PrivateAttr()
    _blueprint_report_storage: BlueprintReportStorage = PrivateAttr()
    _discovery_crew_factory: CrewFactory = PrivateAttr()
    _product_planning_crew_factory: CrewFactory = PrivateAttr()
    _technical_planning_crew_factory: CrewFactory = PrivateAttr()
    _lead_review_crew_factory: CrewFactory = PrivateAttr()

    def __init__(
        self,
        *,
        initial_state: BuildWiseFlowState | None = None,
        settings: Settings | None = None,
        agent_factory: AgentFactory | None = None,
        planner: SpecialistPlanner | None = None,
        blueprint_builder: BlueprintBuilder | None = None,
        blueprint_report_storage: BlueprintReportStorage | None = None,
        discovery_crew_factory: CrewFactory = create_discovery_crew,
        product_planning_crew_factory: CrewFactory = create_product_planning_crew,
        technical_planning_crew_factory: CrewFactory = create_technical_planning_crew,
        lead_review_crew_factory: CrewFactory = create_lead_review_crew,
        persistence: FlowPersistence | None = None,
    ) -> None:
        resolved_settings = settings or get_settings()
        super().__init__(
            initial_state=initial_state or BuildWiseFlowState(),
            persistence=persistence,
            tracing=resolved_settings.crewai_tracing_enabled,
        )
        self._settings = resolved_settings
        self._agent_factory = agent_factory or AgentFactory(settings=resolved_settings)
        self._planner = planner or SpecialistPlanner()
        self._project_cost_aggregator = ProjectCostAggregator()
        self._usage_aggregator = UsageAggregator()
        self._blueprint_builder = blueprint_builder or BlueprintAssembler()
        self._blueprint_report_storage = (
            blueprint_report_storage or create_blueprint_report_storage(resolved_settings)
        )
        self._discovery_crew_factory = discovery_crew_factory
        self._product_planning_crew_factory = product_planning_crew_factory
        self._technical_planning_crew_factory = technical_planning_crew_factory
        self._lead_review_crew_factory = lead_review_crew_factory

    @start()
    def initialize(self) -> SessionStatus:
        """Validate the entry state for a new or resumed execution."""

        if self.state.status is SessionStatus.CREATED:
            if self.state.intake_request is None:
                raise ValueError("A consulting Flow requires an intake_request.")
            self.state.start_flow()
            logger.info("flow_started", session_id=str(self.state.session_id))
        elif self.state.status is SessionStatus.RESUMING:
            if self.state.intake_request is None:
                raise ValueError("A resumed consulting Flow requires its intake_request.")
        else:
            raise ValueError("A consulting Flow kickoff requires created or resuming typed state.")
        return self.state.status

    @router(initialize)
    def route_from_entry(self) -> str:
        """Send both new and resumed sessions into Discovery."""

        return FlowRoute.RUN_DISCOVERY.value

    @listen(FlowRoute.RUN_DISCOVERY.value)
    def execute_discovery(self) -> DiscoveryResult:
        """Execute Discovery with accumulated clarification context."""

        self._transition(SessionStage.DISCOVERY, SessionStatus.PROCESSING)
        intake = self._require(self.state.intake_request, "intake_request")
        clarification_context = self._clarification_context()
        previous_discovery = self.state.discovery_result
        crew = self._discovery_crew_factory(
            session_id=self.state.session_id,
            product_idea=intake,
            clarification_context=clarification_context,
            previous_discovery=previous_discovery,
            maximum_clarification_rounds=self.state.limits.maximum_clarification_rounds,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        output = self._kickoff(crew, stage="discovery")
        if previous_discovery is not None and clarification_context is not None:
            if isinstance(output.pydantic, DiscoveryRefinement):
                result = merge_discovery_refinement(
                    previous_discovery,
                    clarification_context,
                    output.pydantic,
                    session_id=self.state.session_id,
                )
            else:
                # Preserve compatibility with injected Crew doubles and
                # previously configured custom Discovery crews.
                result = bind_discovery_session(
                    self._require_output(output, DiscoveryResult, "Discovery Crew"),
                    session_id=self.state.session_id,
                )
        else:
            result = bind_discovery_session(
                self._require_output(output, DiscoveryResult, "Discovery Crew"),
                session_id=self.state.session_id,
            )
        self.state.set_product_context(result.idea_context)
        self.state.set_discovery_result(result)
        logger.info("discovery_completed", session_id=str(self.state.session_id))
        return result

    @router(execute_discovery)
    def route_discovery(self) -> str:
        return route_after_discovery(self.state).value

    @listen(FlowRoute.REQUEST_CLARIFICATION.value)
    def pause_for_clarification(self) -> BuildWiseFlowState:
        """Enter the durable pause boundary with structured questions."""

        discovery = self._require(self.state.discovery_result, "discovery_result")
        questions = self._require(
            discovery.clarification_questions,
            "discovery_result.clarification_questions",
        )
        self.state.request_clarification(question_set=questions)
        logger.info(
            "clarification_requested",
            session_id=str(self.state.session_id),
            round=questions.round_number,
        )
        return cast(BuildWiseFlowState, self.state)

    @listen(FlowRoute.RUN_PRODUCT_DEFINITION.value)
    def run_product_planning(self) -> ProductPlanningResult:
        """Run the Product Planning Crew after the early-market decision."""

        self._transition(SessionStage.PRODUCT_DEFINITION, SessionStatus.PROCESSING)
        discovery = self._require(self.state.discovery_result, "discovery_result")
        include_market = self._planner.should_include_early_market_context(discovery=discovery)
        crew = self._product_planning_crew_factory(
            discovery_result=discovery,
            include_market_and_gtm=include_market,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        output = self._kickoff(crew, stage="product_planning")
        result = assemble_product_planning_result(
            output,
            session_id=self.state.session_id,
        )
        self.state.set_product_planning_result(result)
        logger.info("product_planning_completed", session_id=str(self.state.session_id))
        return result

    @listen(run_product_planning)
    def plan_specialists(self) -> SpecialistExecutionPlan:
        """Call the deterministic planner without duplicating its policies."""

        self._transition(SessionStage.SPECIALIST_PLANNING, SessionStatus.PROCESSING)
        discovery = self._require(self.state.discovery_result, "discovery_result")
        product_planning = self._require(
            self.state.product_planning_result,
            "product_planning_result",
        )
        plan = self._planner.create_execution_plan(
            discovery=discovery,
            product_planning=product_planning,
            limits=self.state.limits,
        )
        self.state.set_specialist_execution_plan(plan)
        apply_specialist_execution_plan(state=self.state, plan=plan)
        route_after_specialist_planning(self.state)
        logger.info("specialist_plan_created", session_id=str(self.state.session_id))
        return plan

    @listen(plan_specialists)
    def run_technical_planning(self) -> TechnicalPlanningResult:
        """Execute exactly the technical specialists selected by the planner."""

        self._transition(SessionStage.SPECIALIST_EXECUTION, SessionStatus.PROCESSING)
        product_planning = self._require(
            self.state.product_planning_result,
            "product_planning_result",
        )
        plan = self._require(
            self.state.specialist_execution_plan,
            "specialist_execution_plan",
        )
        self._mark_selected_specialists_running()
        crew = self._technical_planning_crew_factory(
            requirements=product_planning.requirements,
            specialist_plan=plan,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        output = self._kickoff(crew, stage="technical_planning")
        result = assemble_technical_planning_result(
            output,
            session_id=self.state.session_id,
        )
        self._complete_specialist_executions(result)
        self.state.set_technical_planning_result(result)
        self._aggregate_project_costs()
        route_after_specialists(self.state)
        logger.info("technical_planning_completed", session_id=str(self.state.session_id))
        return result

    @listen(or_(run_technical_planning, FlowRoute.RUN_LEAD_REVIEW.value))
    def execute_lead_review(self) -> LeadReview:
        """Run the Lead Reviewer with the latest canonical aggregates."""

        self._transition(SessionStage.LEAD_REVIEW, SessionStatus.REVIEWING)
        discovery = self._require(self.state.discovery_result, "discovery_result")
        product = self._require(
            self.state.product_planning_result,
            "product_planning_result",
        )
        plan = self._require(
            self.state.specialist_execution_plan,
            "specialist_execution_plan",
        )
        technical = self._require(
            self.state.technical_planning_result,
            "technical_planning_result",
        )
        cost_summary = self._require(self.state.cost_summary, "cost_summary")
        crew = self._lead_review_crew_factory(
            discovery_result=discovery,
            product_definition=product.product_definition,
            requirements=product.requirements,
            specialist_plan=plan,
            market_and_gtm=product.market_and_gtm,
            solution_architecture=technical.solution_architecture,
            ai_architecture=technical.ai_architecture,
            security_architecture=technical.security_architecture,
            qa_evaluation=technical.qa_evaluation,
            cost_summary=cost_summary,
            revision_history=self.state.revision_history,
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        output = self._kickoff(crew, stage="lead_review")
        review = self._require_output(output, LeadReview, "Lead Review Crew")
        self.state.set_lead_review(review)
        logger.info("lead_review_completed", session_id=str(self.state.session_id))
        return review

    @router(execute_lead_review)
    def route_review(self) -> str:
        review = self._require(self.state.lead_review, "lead_review")
        return route_after_review(review).value

    @router(FlowRoute.RUN_TARGETED_REVISION.value)
    def execute_targeted_revision(self) -> str:
        """Re-run only the business Crew affected by the review requests."""

        review = self._require(self.state.lead_review, "lead_review")
        requests = review.revision_requests
        if not requests:
            raise ValueError("A revision-required review must include revision requests.")
        try:
            revision_route = route_targeted_revision(state=self.state, requests=requests)
        except ValueError as error:
            if "maximum number" in str(error):
                return FlowRoute.FAIL_FLOW.value
            raise

        self.state.revision_count += 1
        self._transition(SessionStage.REFINEMENT, SessionStatus.PROCESSING)
        logger.info(
            "revision_started",
            session_id=str(self.state.session_id),
            revision=self.state.revision_count,
        )
        if revision_route.product_targets:
            self._rerun_product_planning(requests)
        elif revision_route.technical_targets:
            self._rerun_technical_planning(
                requests,
                specialists=set(revision_route.technical_specialists),
            )
        elif revision_route.rebuild_cost_summary:
            self._aggregate_project_costs()
        return FlowRoute.RUN_LEAD_REVIEW.value

    @listen(FlowRoute.ASSEMBLE_BLUEPRINT.value)
    def build_blueprint(self) -> ProductBlueprint:
        """Invoke the blueprint boundary only after Lead Review approval."""

        validate_output(self.state)
        self._transition(SessionStage.BLUEPRINT_ASSEMBLY, SessionStatus.PROCESSING)
        blueprint = self._blueprint_builder.build(
            discovery=self._require(self.state.discovery_result, "discovery_result"),
            product_planning=self._require(
                self.state.product_planning_result,
                "product_planning_result",
            ),
            specialist_plan=self._require(
                self.state.specialist_execution_plan,
                "specialist_execution_plan",
            ),
            technical_planning=self._require(
                self.state.technical_planning_result,
                "technical_planning_result",
            ),
            cost_summary=self._require(self.state.cost_summary, "cost_summary"),
            lead_review=self._require(self.state.lead_review, "lead_review"),
            usage_summary=self.state.usage,
        )
        self.state.product_blueprint = blueprint
        review = self._require(self.state.lead_review, "lead_review")
        if review.decision is ReviewDecision.APPROVED_WITH_LIMITATIONS:
            for index, limitation in enumerate(review.limitations, start=1):
                self.state.add_warning(
                    WarningMessage(
                        code=f"review_limitation_{index}",
                        message=limitation,
                        stage=SessionStage.LEAD_REVIEW.value,
                        source="lead_reviewer",
                    )
                )
            if not review.limitations:
                self.state.add_warning(
                    WarningMessage(
                        code="review_approved_with_limitations",
                        message="The Lead Reviewer approved the blueprint with limitations.",
                        stage=SessionStage.LEAD_REVIEW.value,
                        source="lead_reviewer",
                    )
                )
        review_id = self.state.review_artifact_id or generate_uuid()
        self.state.blueprint_report = self._blueprint_report_storage.store(
            consultation_id=self.state.session_id,
            blueprint=blueprint,
            lead_review_id=review_id,
        )
        blueprint_id = generate_uuid()
        self.state.mark_completed(
            blueprint_artifact_id=blueprint_id,
            review_artifact_id=review_id,
            completed_with_limitations=(
                review.decision is ReviewDecision.APPROVED_WITH_LIMITATIONS
            ),
        )
        logger.info("flow_completed", session_id=str(self.state.session_id))
        return blueprint

    @listen(FlowRoute.FAIL_FLOW.value)
    def terminate_flow(self) -> BuildWiseFlowState:
        """Terminate a deterministically rejected or revision-exhausted Flow."""

        review = self.state.lead_review
        message = (
            "The Lead Reviewer rejected the consultation."
            if review is not None and review.decision is ReviewDecision.REJECTED
            else "The consulting Flow could not continue within its revision limits."
        )
        self.state.mark_failed(
            error=SessionError(
                code="consulting_flow_rejected",
                message=message,
                stage=self.state.stage,
            )
        )
        logger.info("flow_failed", session_id=str(self.state.session_id))
        return cast(BuildWiseFlowState, self.state)

    def submit_clarification_answers(
        self,
        answers: list[ClarificationAnswer],
    ) -> None:
        """Apply structured answers before reconstructing and kicking off the Flow."""

        self.state.receive_clarification_answers(answers=answers)

    def _rerun_product_planning(self, requests: list[RevisionRequest]) -> None:
        discovery = self._require(self.state.discovery_result, "discovery_result")
        previous = self._require(
            self.state.product_planning_result,
            "product_planning_result",
        )
        crew = self._product_planning_crew_factory(
            discovery_result=discovery,
            include_market_and_gtm=previous.market_and_gtm is not None,
            revision_requests=[
                request for request in requests if request.target in PRODUCT_REVISION_TARGETS
            ],
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        result = assemble_product_planning_result(
            self._kickoff(crew, stage="product_revision"),
            session_id=self.state.session_id,
        )
        self.state.set_product_planning_result(result)

        # Product changes can alter technical selection and invalidate all
        # downstream artifacts, so recalculate and rerun the technical Crew.
        plan = self._planner.create_execution_plan(
            discovery=discovery,
            product_planning=result,
            limits=self.state.limits,
        )
        self.state.specialist_executions = []
        self.state.set_specialist_execution_plan(plan)
        apply_specialist_execution_plan(state=self.state, plan=plan)
        self._rerun_technical_planning(requests)

    def _rerun_technical_planning(
        self,
        requests: list[RevisionRequest],
        *,
        specialists: set[SpecialistType] | None = None,
    ) -> None:
        product = self._require(
            self.state.product_planning_result,
            "product_planning_result",
        )
        plan = self._require(
            self.state.specialist_execution_plan,
            "specialist_execution_plan",
        )
        previous = self._require(
            self.state.technical_planning_result,
            "technical_planning_result",
        )
        specialists = specialists or set(self.state.selected_specialists)
        for execution in self.state.specialist_executions:
            if execution.status == "completed" and execution.specialist in specialists:
                execution.prepare_revision()
        self._mark_selected_specialists_running(specialists=specialists)
        crew = self._technical_planning_crew_factory(
            requirements=product.requirements,
            specialist_plan=plan,
            revision_specialists=specialists,
            previous_result=previous,
            revision_requests=[
                request for request in requests if request.target in TECHNICAL_REVISION_TARGETS
            ],
            agent_factory=self._agent_factory,
            settings=self._settings,
        )
        result = assemble_technical_planning_result(
            self._kickoff(crew, stage="technical_revision"),
            session_id=self.state.session_id,
            previous_result=previous,
        )
        self._complete_specialist_executions(result)
        self.state.set_technical_planning_result(result)
        self._aggregate_project_costs()

    def _clarification_context(self) -> ProductIdeaContext | None:
        if not self.state.clarification_answers:
            return cast(ProductIdeaContext | None, self.state.product_context)
        prior = self._require(self.state.product_context, "product_context")
        return cast(
            ProductIdeaContext,
            prior.model_copy(
                update={
                    "clarification_answers": list(self.state.clarification_answers),
                    "clarification_round": self.state.clarification_round,
                    "context_version": prior.context_version + 1,
                }
            ),
        )

    def _aggregate_project_costs(self) -> None:
        summary = self._project_cost_aggregator.aggregate(
            product_planning=self._require(
                self.state.product_planning_result,
                "product_planning_result",
            ),
            technical_planning=self._require(
                self.state.technical_planning_result,
                "technical_planning_result",
            ),
        )
        self.state.set_cost_summary(summary)

    def _mark_selected_specialists_running(
        self,
        *,
        specialists: set[SpecialistType] | None = None,
    ) -> None:
        for execution in self.state.specialist_executions:
            if execution.status in {"pending", "failed"} and (
                specialists is None or execution.specialist in specialists
            ):
                self.state.mark_specialist_running(specialist=execution.specialist)

    def _complete_specialist_executions(
        self,
        result: TechnicalPlanningResult,
    ) -> None:
        artifacts = {
            SpecialistType.SOLUTION_ARCHITECTURE: result.solution_architecture,
            SpecialistType.AI_ARCHITECTURE: result.ai_architecture,
            SpecialistType.SECURITY_ARCHITECTURE: result.security_architecture,
            SpecialistType.QA_AND_EVALUATION: result.qa_evaluation,
        }
        for specialist, artifact in artifacts.items():
            if artifact is not None:
                self.state.mark_specialist_completed(
                    specialist=specialist,
                    artifact_id=getattr(artifact, "id", generate_uuid()),
                )

    def _kickoff(self, crew: Crew, *, stage: str) -> CrewOutput:
        started_at = perf_counter()
        output = crew.kickoff()
        duration_ms = round((perf_counter() - started_at) * 1000)
        if not isinstance(output, CrewOutput):
            raise TypeError("BuildWise Crews must use non-streaming CrewOutput.")
        self._usage_aggregator.append(
            summary=self.state.usage,
            metrics=output.token_usage,
            task_name=stage,
            execution_duration_ms=duration_ms,
        )
        usage = self.state.usage
        if usage.total_tokens > self.state.limits.maximum_session_tokens:
            raise RuntimeError("The maximum session token budget was exceeded.")
        if (
            usage.estimated_cost_usd is not None
            and usage.estimated_cost_usd > self.state.limits.maximum_estimated_cost_usd
        ):
            raise RuntimeError("The maximum estimated session cost was exceeded.")
        return output

    def _transition(self, stage: SessionStage, status: SessionStatus) -> None:
        if self.state.stage is stage and self.state.status is status:
            return
        self.state.transition_to(
            stage=stage,
            status=status,
            reason="stage_completed",
            description=f"The Flow entered the {stage.value} stage.",
        )

    @staticmethod
    def _require[T](value: T | None, name: str) -> T:
        if value is None:
            raise ValueError(f"The consulting Flow requires {name}.")
        return value

    @staticmethod
    def _require_output[T](
        output: CrewOutput,
        expected_type: type[T],
        crew_name: str,
    ) -> T:
        value = output.pydantic
        if not isinstance(value, expected_type):
            raise ValueError(
                f"{crew_name} must return {expected_type.__name__} as structured output."
            )
        return value
