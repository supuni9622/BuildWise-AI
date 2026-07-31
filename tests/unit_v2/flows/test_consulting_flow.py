"""Mocked end-to-end smoke test for ConsultingFlow.

Patches ``crewai.Crew.kickoff`` so the test exercises the real
``@start``/``@router``/``@listen`` wiring, real Crew/Task composition, and
real domain validation — without any live LLM call.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from crewai import Crew
from crewai.crews.crew_output import CrewOutput
from crewai.tasks.task_output import TaskOutput

from buildwisev2.domain.architecture import (
    DeploymentView,
    SolutionArchitecture,
    SolutionArchitectureDecision,
)
from buildwisev2.domain.common import FlowRuntimeLimits
from buildwisev2.domain.discovery import (
    CapabilityClassification,
    CompletenessAssessment,
    DiscoveryDecision,
    DiscoveryResult,
)
from buildwisev2.domain.intake import ClarificationAnswer, ProductIdeaContext, ProductIdeaRequest
from buildwisev2.domain.product import ProductDefinition, ProductDefinitionDecision
from buildwisev2.domain.requirements import RequirementsDecision, RequirementsSpecification
from buildwisev2.domain.review import LeadReview, ReviewDecision
from buildwisev2.flows.consulting_flow import ConsultingFlow
from buildwisev2.flows.state import FlowStage

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


def _task_output(name: str, pydantic_output) -> TaskOutput:
    return TaskOutput(description="test", agent="test-agent", name=name, pydantic=pydantic_output)


def _crew_output(
    *, pydantic_output=None, tasks_output: list[TaskOutput] | None = None
) -> CrewOutput:
    return CrewOutput(pydantic=pydantic_output, tasks_output=tasks_output or [])


def _happy_path_kickoff_factory(session_id):
    def fake_kickoff(self: Crew, inputs=None):
        names = [t.name for t in self.tasks]

        if names == ["product_discovery"]:
            discovery = DiscoveryResult(
                session_id=session_id,
                interpreted_idea="A simple internal tool.",
                capability_classification=CapabilityClassification(),
                completeness=CompletenessAssessment(can_continue=True, completeness_score=0.95),
                decision=DiscoveryDecision.CONTINUE,
                confidence=0.9,
            )
            return _crew_output(pydantic_output=discovery)

        if "product_definition" in names:
            product_definition = ProductDefinition(
                session_id=session_id,
                vision="v",
                value_proposition="vp",
                goals=["g"],
                personas=[],
                features=[],
                mvp_feature_ids=[],
                decision=ProductDefinitionDecision.APPROVED,
            )
            requirements = RequirementsSpecification(
                session_id=session_id,
                functional_requirements=[],
                non_functional_requirements=[],
                decision=RequirementsDecision.APPROVED,
            )
            return _crew_output(
                tasks_output=[
                    _task_output("product_definition", product_definition),
                    _task_output("requirements", requirements),
                ]
            )

        if names == ["solution_architecture"]:
            solution = SolutionArchitecture(
                session_id=session_id,
                system_context="A simple internal tool.",
                components=[],
                deployment=DeploymentView(description="single region"),
                scalability_strategy="n/a",
                reliability_strategy="n/a",
                observability_strategy="n/a",
                decision=SolutionArchitectureDecision.APPROVED,
            )
            return _crew_output(tasks_output=[_task_output("solution_architecture", solution)])

        if names == ["lead_review"]:
            review = LeadReview(
                session_id=session_id,
                implementation_readiness_score=0.9,
                decision=ReviewDecision.APPROVED,
                approved_for_blueprint=True,
            )
            return _crew_output(
                pydantic_output=review,
                tasks_output=[_task_output("lead_review", review)],
            )

        raise AssertionError(f"Unexpected crew task composition: {names}")

    return fake_kickoff


def test_consulting_flow_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = uuid4()
    monkeypatch.setattr(Crew, "kickoff", _happy_path_kickoff_factory(session_id))

    flow = ConsultingFlow()
    flow.state.product_idea = ProductIdeaRequest(
        session_id=session_id, raw_idea="A simple internal tool."
    )
    flow.state.limits = FlowRuntimeLimits()

    result = flow.kickoff()

    assert flow.state.stage == FlowStage.COMPLETED
    assert flow.state.discovery_result is not None
    assert flow.state.product_planning_result is not None
    assert flow.state.specialist_plan is not None
    assert flow.state.technical_planning_result is not None
    assert flow.state.lead_review is not None
    assert flow.state.lead_review.decision == ReviewDecision.APPROVED
    assert flow.state.blueprint is not None
    assert result.session_id == session_id
    assert result.generated_markdown.startswith("#")


def test_consulting_flow_requires_product_idea_before_kickoff() -> None:
    flow = ConsultingFlow()

    with pytest.raises(ValueError):
        flow.kickoff()


def _persistently_incomplete_kickoff_factory(session_id):
    """Discovery always asks for clarification and never reports
    completeness, no matter what answers it receives — reproduces a real
    session that exhausts the clarification-round budget while Discovery
    still considers itself incomplete.
    """

    def fake_kickoff(self: Crew, inputs=None):
        names = [t.name for t in self.tasks]
        if names == ["product_discovery"]:
            discovery = DiscoveryResult(
                session_id=session_id,
                interpreted_idea="An underspecified tool.",
                capability_classification=CapabilityClassification(),
                completeness=CompletenessAssessment(can_continue=False, completeness_score=0.3),
                decision=DiscoveryDecision.CLARIFICATION_REQUIRED,
                clarification_questions=["What platform?"],
                confidence=0.3,
            )
            return _crew_output(pydantic_output=discovery)
        return _happy_path_kickoff_factory(session_id)(self, inputs)

    return fake_kickoff


def test_consulting_flow_force_continues_after_clarification_rounds_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: previously, exhausting the clarification-round
    budget while Discovery still reported ``can_continue=False`` crashed
    ``run_specialist_planning`` (the planner rejects incomplete Discovery
    results), stranding the consultation in a failed state. The Flow must
    reconcile the artifact before handing it downstream instead.
    """

    session_id = uuid4()
    monkeypatch.setattr(Crew, "kickoff", _persistently_incomplete_kickoff_factory(session_id))

    flow = ConsultingFlow()
    flow.state.product_idea = ProductIdeaRequest(
        session_id=session_id, raw_idea="An underspecified tool."
    )
    flow.state.limits = FlowRuntimeLimits(maximum_clarification_rounds=1)

    flow.kickoff()
    assert flow.state.stage == FlowStage.AWAITING_CLARIFICATION

    flow.state.clarification_context = ProductIdeaContext(
        session_id=session_id,
        clarification_answers=[ClarificationAnswer(question="What platform?", answer="Web.")],
        clarification_round=1,
    )
    flow.kickoff()

    assert flow.state.discovery_result is not None
    assert flow.state.discovery_result.decision == DiscoveryDecision.CONTINUE_WITH_LIMITATIONS
    assert flow.state.discovery_result.completeness.can_continue is True
    assert flow.state.stage in (FlowStage.COMPLETED, FlowStage.COMPLETED_WITH_LIMITATIONS)
    assert flow.state.blueprint is not None
