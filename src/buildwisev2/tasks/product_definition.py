"""Product Definition Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.tasks.formatting import revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("discovery_result",)
OPTIONAL_KICKOFF_KEYS = ("market_and_gtm_context",)

_DESCRIPTION_TEMPLATE = """\
Objective
Convert the approved discovery assessment into a complete product
definition: vision, personas, prioritized features, MVP scope, roadmap,
and success metrics.

Approved discovery assessment
{{discovery_result}}
{market_context_block}

Required decisions
- Define product vision and value proposition.
- Define 1-4 personas with goals and pain points.
- Define prioritized features (MoSCoW) and select the MVP subset by id.
- Define explicit exclusions, a phased roadmap, and success metrics.
- Carry forward risks and assumptions from discovery; add product-level ones.

Required output
A schema-valid ProductDefinition.

Important boundaries
Do not create detailed requirements, choose technology, design
architecture, perform market research yourself, or define security or QA
plans.

{revision_instructions}
"""


def create_product_definition_task(
    *,
    agent: Agent,
    market_and_gtm_task: Task | None = None,
    prior_market_and_gtm: MarketAndGTMStrategy | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Product Definition Task.

    Consumes ``discovery_result`` through Crew kickoff inputs. Market
    context can be supplied two ways, never both:

    - ``market_and_gtm_task``: the Market & GTM Task runs in this same Crew
      execution — wired as native CrewAI Task context.
    - ``prior_market_and_gtm``: an already-approved ``MarketAndGTMStrategy``
      from an earlier run that is NOT being regenerated this time (targeted
      revision) — embedded as a kickoff placeholder instead.
    """

    if market_and_gtm_task is not None and prior_market_and_gtm is not None:
        raise ValueError(
            "create_product_definition_task accepts at most one of "
            "market_and_gtm_task or prior_market_and_gtm."
        )

    if market_and_gtm_task is not None:
        market_context_block = (
            "\nEarly market context from this Crew's Market & GTM task is "
            "available above as prior Task context — use it to ground personas "
            "and positioning."
        )
    elif prior_market_and_gtm is not None:
        market_context_block = "\nPreviously approved market context\n{market_and_gtm_context}"
    else:
        market_context_block = ""

    description = _DESCRIPTION_TEMPLATE.format(
        market_context_block=market_context_block,
        revision_instructions=revision_section(revision_request),
    )

    return Task(
        name="product_definition",
        description=description,
        expected_output="A schema-valid ProductDefinition object.",
        agent=agent,
        context=[market_and_gtm_task] if market_and_gtm_task is not None else None,
        output_pydantic=ProductDefinition,
        guardrails=compose_guardrails(require_pydantic_output(ProductDefinition)),
        guardrail_max_retries=guardrail_max_retries,
    )
