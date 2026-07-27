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

from crewai import Crew, CrewOutput, Process, Task

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.common import SessionId
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import AgentType, RevisionTarget
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
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

    product_manager_agent = agent_factory.create(AgentType.PRODUCT_MANAGER)
    business_analyst_agent = agent_factory.create(AgentType.BUSINESS_ANALYST)

    product_definition_task = create_product_definition_task(
        agent=product_manager_agent,
        discovery_result=discovery_result,
        revision_request=_find_revision(revision_requests, RevisionTarget.PRODUCT_DEFINITION),
        guardrail_max_retries=settings.max_retries_per_operation,
    )

    requirements_task = create_requirements_task(
        agent=business_analyst_agent,
        product_definition_task=product_definition_task,
        revision_request=_find_revision(revision_requests, RevisionTarget.REQUIREMENTS),
        guardrail_max_retries=settings.max_retries_per_operation,
    )

    agents = [product_manager_agent, business_analyst_agent]
    tasks: list[Task] = [product_definition_task, requirements_task]

    if include_market_and_gtm:
        market_and_gtm_agent = agent_factory.create(AgentType.MARKET_AND_GTM_STRATEGIST)

        market_and_gtm_task = create_market_and_gtm_task(
            agent=market_and_gtm_agent,
            product_definition_task=product_definition_task,
            requirements_task=requirements_task,
            revision_request=_find_revision(revision_requests, RevisionTarget.MARKET_AND_GTM),
            guardrail_max_retries=settings.max_retries_per_operation,
        )

        agents.append(market_and_gtm_agent)
        tasks.append(market_and_gtm_task)

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
        tracing=settings.crewai_tracing_enabled,
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

    product_definition: ProductDefinition | None = None
    requirements: RequirementsSpecification | None = None
    market_and_gtm: MarketAndGTMStrategy | None = None

    for task_output in crew_output.tasks_output:
        output = task_output.pydantic

        if isinstance(output, ProductDefinition):
            product_definition = output
        elif isinstance(output, RequirementsSpecification):
            requirements = output
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
