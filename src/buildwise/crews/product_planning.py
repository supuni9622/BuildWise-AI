"""Product Planning Crew factory.

Combines the Product Manager, Business Analyst, and (when selected) Market
and GTM Strategist into one collaborative native CrewAI Crew that converts
an approved ``DiscoveryResult`` into a ``ProductDefinition`` and
``RequirementsSpecification``, plus a ``MarketAndGTMStrategy`` when market
context is requested.

Market and GTM always runs last within this Crew: ``MarketAndGTMStrategy``
validates its segment/opportunity references against a real
``ProductDefinition`` and consumes ``RequirementsSpecification``, so it
cannot run before either artifact exists.
"""

from __future__ import annotations

from crewai import Agent, Crew, CrewOutput, Process, Task

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.artifact_drafts import (
    MarketAndGTMStrategyDraft,
    ProductDefinitionDraft,
    RequirementsSpecificationDraft,
    assemble_market_and_gtm_strategy,
    assemble_product_definition,
    assemble_requirements_specification,
)
from buildwise.domain.common import SessionId
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import AgentType, RevisionTarget
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.planning.specialist_context import (
    ProductDefinitionProjection,
    RequirementsProjection,
)
from buildwise.tasks.context_wiring import (
    PRODUCT_DEFINITION_CONTEXT_PLACEHOLDER,
    REQUIREMENTS_CONTEXT_PLACEHOLDER,
    wire_compact_context,
)
from buildwise.tasks.market_and_gtm import create_market_and_gtm_task
from buildwise.tasks.product_definition import create_product_definition_task
from buildwise.tasks.requirements import create_requirements_task


def create_product_planning_crew(
    *,
    discovery_result: DiscoveryResult,
    include_market_and_gtm: bool,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_requests: list[RevisionRequest] | None = None,
    execution_target: RevisionTarget | None = None,
    previous_result: ProductPlanningResult | None = None,
) -> Crew:
    """Build the Product Planning Crew.

    Always produces a ``ProductDefinition`` and a
    ``RequirementsSpecification``. When ``include_market_and_gtm`` is true,
    also produces a ``MarketAndGTMStrategy`` as the final task, since it
    depends on both prior artifacts.

    Args:
        discovery_result: The completed DiscoveryResult from the Discovery
            Crew.
        include_market_and_gtm: Whether to include the Market and GTM
            Strategist in this planning round.
        agent_factory: Factory used to construct native specialist agents.
        settings: Application settings supplying retry and verbosity policy.
        revision_requests: Bounded revision requests from the Lead Reviewer.
            Each request is routed only to the task it targets
            (``product_definition``, ``requirements``, or
            ``market_and_gtm``); at most one request per target is
            supported in a single Crew run.

    Returns:
        A native ``crewai.Crew`` whose task outputs are, in order,
        ``ProductDefinition``, ``RequirementsSpecification``, and (when
        ``include_market_and_gtm`` is true) ``MarketAndGTMStrategy``.
    """

    agents: list[Agent] = []
    tasks: list[Task] = []
    product_definition_task: Task | None = None
    requirements_task: Task | None = None
    market_and_gtm_task: Task | None = None

    if execution_target in {None, RevisionTarget.PRODUCT_DEFINITION}:
        product_manager_agent = agent_factory.create(AgentType.PRODUCT_MANAGER)
        product_definition_task = create_product_definition_task(
            agent=product_manager_agent,
            discovery_result=discovery_result,
            revision_request=_find_revision(revision_requests, RevisionTarget.PRODUCT_DEFINITION),
            guardrail_max_retries=settings.max_retries_per_operation,
        )
        agents.append(product_manager_agent)
        tasks.append(product_definition_task)

    if execution_target in {None, RevisionTarget.REQUIREMENTS}:
        business_analyst_agent = agent_factory.create(AgentType.BUSINESS_ANALYST)
        if product_definition_task is not None:
            requirements_task = create_requirements_task(
                agent=business_analyst_agent,
                product_definition_task=product_definition_task,
                revision_request=_find_revision(revision_requests, RevisionTarget.REQUIREMENTS),
                guardrail_max_retries=settings.max_retries_per_operation,
            )
        elif previous_result is not None:
            requirements_task = create_requirements_task(
                agent=business_analyst_agent,
                product_definition=previous_result.product_definition,
                revision_request=_find_revision(revision_requests, RevisionTarget.REQUIREMENTS),
                guardrail_max_retries=settings.max_retries_per_operation,
            )
        else:
            raise ValueError("Requirements execution requires a Product Definition.")
        agents.append(business_analyst_agent)
        tasks.append(requirements_task)

    if include_market_and_gtm and execution_target in {
        None,
        RevisionTarget.MARKET_AND_GTM,
    }:
        market_and_gtm_agent = agent_factory.create(AgentType.MARKET_AND_GTM_STRATEGIST)
        if product_definition_task is not None and requirements_task is not None:
            market_and_gtm_task = create_market_and_gtm_task(
                agent=market_and_gtm_agent,
                product_definition_task=product_definition_task,
                requirements_task=requirements_task,
                revision_request=_find_revision(revision_requests, RevisionTarget.MARKET_AND_GTM),
                guardrail_max_retries=settings.max_retries_per_operation,
            )
        elif previous_result is not None:
            market_and_gtm_task = create_market_and_gtm_task(
                agent=market_and_gtm_agent,
                product_definition=previous_result.product_definition,
                requirements=previous_result.requirements,
                revision_request=_find_revision(revision_requests, RevisionTarget.MARKET_AND_GTM),
                guardrail_max_retries=settings.max_retries_per_operation,
            )
        else:
            raise ValueError("Market execution requires product planning context.")

        agents.append(market_and_gtm_agent)
        tasks.append(market_and_gtm_task)

    _wire_same_crew_context(
        product_definition_task=product_definition_task,
        requirements_task=requirements_task,
        market_and_gtm_task=market_and_gtm_task,
    )

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
        tracing=settings.crewai_tracing_enabled,
    )


def _wire_same_crew_context(
    *,
    product_definition_task: Task | None,
    requirements_task: Task | None,
    market_and_gtm_task: Task | None,
) -> None:
    """Wire compact context into every downstream task chained within this Crew.

    Each downstream task factory embeds a placeholder token in its
    description exactly when it was built with a same-Crew ``*_task``
    argument (see ``tasks.context_wiring``). This replaces those
    placeholders with the compact projection of the real completed draft
    once its source task finishes, instead of leaving CrewAI's native
    ``context=[task]`` mechanism inject the full raw upstream output.
    """

    if product_definition_task is not None:
        for target in (requirements_task, market_and_gtm_task):
            if target is not None:
                wire_compact_context(
                    source_task=product_definition_task,
                    target_task=target,
                    placeholder=PRODUCT_DEFINITION_CONTEXT_PLACEHOLDER,
                    project=ProductDefinitionProjection.from_artifact,
                )

    if requirements_task is not None and market_and_gtm_task is not None:
        wire_compact_context(
            source_task=requirements_task,
            target_task=market_and_gtm_task,
            placeholder=REQUIREMENTS_CONTEXT_PLACEHOLDER,
            project=RequirementsProjection.from_artifact,
        )


def _find_revision(
    revision_requests: list[RevisionRequest] | None,
    target: RevisionTarget,
) -> RevisionRequest | None:
    """Return the single revision request targeting one RevisionTarget, if any."""

    if not revision_requests:
        return None

    matches = [request for request in revision_requests if request.target is target]

    if not matches:
        return None

    if len(matches) > 1:
        raise ValueError(
            f"Multiple revision requests target '{target.value}'; only one "
            "revision request per target is supported in a single Crew run."
        )

    return matches[0]


def assemble_product_planning_result(
    crew_output: CrewOutput,
    *,
    session_id: SessionId,
    discovery_result: DiscoveryResult | None = None,
    previous_result: ProductPlanningResult | None = None,
) -> ProductPlanningResult:
    """Assemble a ``ProductPlanningResult`` from a completed Crew run.

    Matches each task output by its structured type rather than by
    position, so this works regardless of whether Market and GTM was
    included. The Flow should call this immediately after
    ``crew.kickoff()`` for a Crew built by ``create_product_planning_crew``.

    Args:
        crew_output: The native ``CrewOutput`` returned by
            ``Crew.kickoff()``.
        session_id: The consulting session that owns these artifacts.

    Returns:
        A schema-valid ``ProductPlanningResult``.

    Raises:
        ValueError: If a required task output is missing, or a task
            produced an output of an unexpected type.
    """

    product_definition = previous_result.product_definition if previous_result else None
    requirements = previous_result.requirements if previous_result else None
    market_and_gtm = previous_result.market_and_gtm if previous_result else None

    for task_output in crew_output.tasks_output:
        output = task_output.pydantic

        if isinstance(output, ProductDefinitionDraft):
            if discovery_result is None:
                raise ValueError("Product Definition draft assembly requires Discovery.")
            product_definition = assemble_product_definition(
                output,
                discovery=discovery_result,
            )
        elif isinstance(output, ProductDefinition):
            product_definition = output
        elif isinstance(output, RequirementsSpecificationDraft):
            if product_definition is None:
                raise ValueError("Requirements draft requires Product Definition.")
            requirements = assemble_requirements_specification(
                output,
                product_definition=product_definition,
            )
        elif isinstance(output, RequirementsSpecification):
            requirements = output
        elif isinstance(output, MarketAndGTMStrategyDraft):
            if product_definition is None:
                raise ValueError("Market draft requires Product Definition.")
            market_and_gtm = assemble_market_and_gtm_strategy(
                output,
                product_definition=product_definition,
            )
        elif isinstance(output, MarketAndGTMStrategy):
            market_and_gtm = output
        else:
            raise ValueError(
                "Product Planning Crew produced an unexpected task output "
                f"type: {type(output).__name__}."
            )

    if product_definition is None:
        raise ValueError("Product Planning Crew output is missing a ProductDefinition task output.")

    if requirements is None:
        raise ValueError(
            "Product Planning Crew output is missing a RequirementsSpecification task output."
        )

    return ProductPlanningResult(
        session_id=session_id,
        product_definition=product_definition,
        requirements=requirements,
        market_and_gtm=market_and_gtm,
    )
