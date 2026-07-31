"""Lead Review Crew: one Lead Reviewer, one Lead Review Task."""

from __future__ import annotations

from crewai import Crew, Process
from pydantic import BaseModel

from buildwisev2.agents import AgentFactory, AgentType
from buildwisev2.config import Settings, get_settings
from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.qa import QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.domain.security_architecture import SecurityArchitecture
from buildwisev2.domain.specialist_planning import SpecialistExecutionPlan
from buildwisev2.tasks.lead_review import create_lead_review_task


def create_lead_review_crew(
    *,
    agent_factory: AgentFactory,
    settings: Settings | None = None,
) -> Crew:
    """Perform the final holistic quality review across all approved artifacts."""

    settings = settings or get_settings()
    agent = agent_factory.create(AgentType.LEAD_REVIEWER)
    task = create_lead_review_task(
        agent=agent,
        guardrail_max_retries=settings.max_retries_per_operation,
    )
    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=settings.crew_cache,
        memory=settings.crew_memory,
    )


def build_lead_review_kickoff_inputs(
    *,
    discovery_result: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    solution_architecture: SolutionArchitecture,
    market_and_gtm: MarketAndGTMStrategy | None = None,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    qa_evaluation: QAEvaluationPlan | None = None,
    revision_history: list[RevisionRequest] | None = None,
) -> dict[str, str]:
    """Build the ``crew.kickoff(inputs=...)`` dict for the Lead Review Crew.

    Optional artifacts that were correctly not selected are serialized as
    an explicit "Not selected." marker, not omitted — the Lead Reviewer
    must be able to tell "not selected" apart from "missing".
    """

    def dump_optional(model: BaseModel | None) -> str:
        if model is None:
            return "Not selected."
        return model.model_dump_json(indent=2)

    history = revision_history or []
    revision_history_text = (
        "[" + ", ".join(request.model_dump_json() for request in history) + "]"
        if history
        else "No prior revisions."
    )

    return {
        "discovery_result": discovery_result.model_dump_json(indent=2),
        "product_definition": product_definition.model_dump_json(indent=2),
        "requirements": requirements.model_dump_json(indent=2),
        "specialist_plan": specialist_plan.model_dump_json(indent=2),
        "market_and_gtm": dump_optional(market_and_gtm),
        "solution_architecture": solution_architecture.model_dump_json(indent=2),
        "ai_architecture": dump_optional(ai_architecture),
        "security_architecture": dump_optional(security_architecture),
        "qa_evaluation": dump_optional(qa_evaluation),
        "revision_history": revision_history_text,
    }
