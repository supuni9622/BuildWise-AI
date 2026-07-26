"""Lead Review Crew factory.

Combines the Lead Reviewer agent with the Lead Review task into a single,
focused, native CrewAI Crew that produces the final ``LeadReview``. This
Crew never rewrites specialist outputs, invokes specialist Crews, or
assembles the blueprint; it only evaluates already-persisted structured
artifacts and returns bounded revision requests for the Flow to route.
"""

from __future__ import annotations

from crewai import Crew, Process

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import AgentType
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.tasks.lead_review import create_lead_review_task


def create_lead_review_crew(
    *,
    discovery_result: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    market_and_gtm: MarketAndGTMStrategy | None,
    solution_architecture: SolutionArchitecture | None,
    ai_architecture: AIArchitecture | None,
    security_architecture: SecurityArchitecture | None,
    qa_evaluation: QAEvaluationPlan | None,
    revision_history: list[RevisionRequest],
    agent_factory: AgentFactory,
    settings: Settings,
) -> Crew:
    """Build the Lead Review Crew.

    Args:
        discovery_result: The completed DiscoveryResult.
        product_definition: The approved ProductDefinition.
        requirements: The approved RequirementsSpecification.
        specialist_plan: The specialist selection and execution plan.
        market_and_gtm: The completed MarketAndGTMStrategy, when selected.
            ``None`` when it was not.
        solution_architecture: The completed SolutionArchitecture, when
            selected. ``None`` when it was not.
        ai_architecture: The completed AIArchitecture, when selected.
            ``None`` when it was not.
        security_architecture: The completed SecurityArchitecture, when
            selected. ``None`` when it was not.
        qa_evaluation: The completed QAEvaluationPlan, when selected.
            ``None`` when it was not.
        revision_history: Revision requests already issued in prior review
            rounds.
        agent_factory: Factory used to construct the native Lead Reviewer
            agent.
        settings: Application settings supplying retry and verbosity policy.

    Returns:
        A native ``crewai.Crew`` with one agent and one task, producing a
        ``LeadReview``.
    """

    agent = agent_factory.create(AgentType.LEAD_REVIEWER)

    task = create_lead_review_task(
        agent=agent,
        discovery=discovery_result,
        product_definition=product_definition,
        requirements=requirements,
        specialist_plan=specialist_plan,
        market_and_gtm=market_and_gtm,
        solution_architecture=solution_architecture,
        ai_architecture=ai_architecture,
        security_architecture=security_architecture,
        qa_evaluation=qa_evaluation,
        revision_history=revision_history,
        guardrail_max_retries=settings.max_retries_per_operation,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
    )
