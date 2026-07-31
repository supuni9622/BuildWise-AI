"""Product Planning Crew: optional Market & GTM Strategist -> Product Manager
-> Business Analyst.

Revision-aware composition: a task regenerates only when its own
``RevisionTarget`` was requested, or an upstream dependency within this
Crew is also regenerating. Tasks that are not regenerating are skipped
entirely — their previously approved artifact is reused as-is (no LLM
call), per ``prior_result``. See ``PROGRESS.md`` for the exact cascade
rule.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from buildwisev2.agents import AgentFactory, AgentType
from buildwisev2.config import Settings, get_settings
from buildwisev2.crews._shared import find_revision
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.planning_results import ProductPlanningResult
from buildwisev2.domain.review import RevisionRequest, RevisionTarget
from buildwisev2.tasks.market_and_gtm import create_market_and_gtm_task
from buildwisev2.tasks.product_definition import create_product_definition_task
from buildwisev2.tasks.requirements import create_requirements_task


def create_product_planning_crew(
    *,
    include_market_and_gtm: bool,
    agent_factory: AgentFactory,
    settings: Settings | None = None,
    revision_requests: list[RevisionRequest] | None = None,
    prior_result: ProductPlanningResult | None = None,
) -> Crew:
    """Convert an approved ``DiscoveryResult`` into a ``ProductPlanningResult``.

    ``include_market_and_gtm`` is decided by the Flow before construction
    (via ``SpecialistPlanner.should_include_early_market_context``), not by
    this Crew. ``prior_result`` is required whenever ``revision_requests``
    is non-empty, so tasks that are not being regenerated this round have
    a prior artifact to reuse.
    """

    settings = settings or get_settings()
    targets = {request.target for request in (revision_requests or [])}
    if revision_requests and prior_result is None:
        raise ValueError("prior_result is required when revision_requests is supplied.")

    regenerate_market = include_market_and_gtm and (
        not revision_requests or RevisionTarget.MARKET_AND_GTM in targets
    )
    regenerate_product = not revision_requests or (
        RevisionTarget.PRODUCT_DEFINITION in targets or regenerate_market
    )
    regenerate_requirements = not revision_requests or (
        RevisionTarget.REQUIREMENTS in targets or regenerate_product
    )

    agents: list[Agent] = []
    tasks: list[Task] = []

    market_task: Task | None = None
    if regenerate_market:
        market_agent = agent_factory.create(AgentType.MARKET_AND_GTM_STRATEGIST)
        market_task = create_market_and_gtm_task(
            agent=market_agent,
            revision_request=find_revision(revision_requests, RevisionTarget.MARKET_AND_GTM),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(market_agent)
        tasks.append(market_task)

    product_task: Task | None = None
    if regenerate_product:
        product_manager = agent_factory.create(AgentType.PRODUCT_MANAGER)
        prior_market = None
        if market_task is None and include_market_and_gtm and prior_result is not None:
            prior_market = prior_result.market_and_gtm
        product_task = create_product_definition_task(
            agent=product_manager,
            market_and_gtm_task=market_task,
            prior_market_and_gtm=prior_market,
            revision_request=find_revision(revision_requests, RevisionTarget.PRODUCT_DEFINITION),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(product_manager)
        tasks.append(product_task)

    if regenerate_requirements:
        business_analyst = agent_factory.create(AgentType.BUSINESS_ANALYST)
        prior_product_definition = None
        if product_task is None and prior_result is not None:
            prior_product_definition = prior_result.product_definition
        requirements_task = create_requirements_task(
            agent=business_analyst,
            product_definition_task=product_task,
            prior_product_definition=prior_product_definition,
            revision_request=find_revision(revision_requests, RevisionTarget.REQUIREMENTS),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(business_analyst)
        tasks.append(requirements_task)

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=settings.crew_cache,
        memory=settings.crew_memory,
    )


def build_product_planning_kickoff_inputs(
    *,
    discovery_result: DiscoveryResult,
    prior_result: ProductPlanningResult | None = None,
) -> dict[str, str]:
    """Build the ``crew.kickoff(inputs=...)`` dict for the Product Planning Crew.

    Always includes the prior-artifact placeholders when ``prior_result``
    is supplied — harmless when the selected Tasks this round don't
    reference them, and required when they do.
    """

    inputs = {"discovery_result": discovery_result.model_dump_json(indent=2)}
    if prior_result is not None:
        inputs["product_definition"] = prior_result.product_definition.model_dump_json(indent=2)
        inputs["market_and_gtm_context"] = (
            prior_result.market_and_gtm.model_dump_json(indent=2)
            if prior_result.market_and_gtm is not None
            else "Not selected."
        )
    return inputs
