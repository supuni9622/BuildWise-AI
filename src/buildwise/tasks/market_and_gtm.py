"""Market and GTM task factory.

Creates the native CrewAI Task assigned to the Market and GTM Strategist. The
task evaluates market segments, competitors, positioning, pricing hypotheses,
channels, and launch experiments for the approved product.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    run_domain_validator,
)
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_market_and_gtm_task(
    *,
    agent: Agent,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Market and GTM task for the Market and GTM Strategist.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.MARKET_AND_GTM_STRATEGIST``. The agent already owns
            the web_search and web_scraper tools; this task does not
            instantiate or restrict them.
        product_definition: The approved ProductDefinition.
        requirements: The approved RequirementsSpecification.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``MarketAndGTMStrategy``.
    """

    if agent is None:
        raise ValueError("create_market_and_gtm_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    description = (
        "Objective: Evaluate the market and go-to-market strategy for the "
        "approved product.\n\n"
        "Available structured context:\n"
        f"ProductDefinition: {product_definition.model_dump_json()}\n"
        f"RequirementsSpecification: {requirements.model_dump_json()}\n\n"
        "Required decisions:\n"
        "- Identify target market segments and mark exactly one as primary.\n"
        "- Analyze direct, indirect, and substitute competitors when "
        "evidence supports doing so.\n"
        "- Recommend a market position and messaging foundation.\n"
        "- Propose pricing hypotheses appropriate to the pricing model.\n"
        "- Recommend acquisition, conversion, and retention channels.\n"
        "- Define bounded launch experiments that validate the riskiest "
        "assumptions.\n"
        "- Identify market and go-to-market risks.\n\n"
        "Required output: A schema-valid MarketAndGTMStrategy referencing "
        "this ProductDefinition by product_definition_id, where every claim "
        "not directly derivable from the supplied product definition and "
        "requirements is backed by an evidence entry.\n\n"
        "Important boundaries:\n"
        "- Do not redefine ProductDefinition scope, personas, or features.\n"
        "- Do not select software architecture or technology.\n"
        "- Do not present an inference as strong or externally verified "
        "evidence; use the web_search and web_scraper tools already "
        "attached to you when you need external market evidence.\n\n"
        "Failure or uncertainty handling: When market evidence is "
        "insufficient, record it under evidence_gaps and set decision to "
        "'requires_more_research' or 'requires_clarification' rather than "
        "fabricating market facts."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid MarketAndGTMStrategy JSON object matching the "
        "MarketAndGTMStrategy Pydantic model exactly, with no additional "
        "prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(MarketAndGTMStrategy),
        run_domain_validator(
            lambda output: MarketAndGTMStrategy.validate_product_ownership(
                market_and_gtm_strategy=output,
                product_definition=product_definition,
            )
        ),
    )

    return Task(
        name="market_and_gtm_strategy",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=MarketAndGTMStrategy,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )
