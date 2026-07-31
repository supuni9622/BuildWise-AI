"""Market & GTM Task factory.

Runs as the early-market-context step of the Product Planning Crew, before
Product Definition — see ``04_crews_refactor_plan.md`` section 9.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.tasks.formatting import revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("discovery_result",)

_DESCRIPTION_TEMPLATE = """\
Objective
Produce evidence-aware market and go-to-market recommendations for the
product idea interpreted during discovery.

Discovery assessment
{{discovery_result}}

Required decisions
- Identify market segments and select one primary segment.
- Research competitors and substitutes using your web tools; cite source
  URLs. If you cannot find evidence, record it as an evidence gap instead
  of inventing a claim.
- Define positioning, messaging pillars, and pricing hypotheses (label
  each with an evidence_confidence level).
- Recommend channels and 1-3 launch experiments with decision criteria.
- Identify commercial/GTM risks.

Required output
A schema-valid MarketAndGTMStrategy.

Important boundaries
Do not change product scope, select implementation technology, or
estimate engineering effort.

{revision_instructions}
"""


def create_market_and_gtm_task(
    *,
    agent: Agent,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Market & GTM Task. Consumes ``discovery_result`` via kickoff inputs."""

    description = _DESCRIPTION_TEMPLATE.format(
        revision_instructions=revision_section(revision_request),
    )
    return Task(
        name="market_and_gtm",
        description=description,
        expected_output="A schema-valid MarketAndGTMStrategy object.",
        agent=agent,
        output_pydantic=MarketAndGTMStrategy,
        guardrails=compose_guardrails(require_pydantic_output(MarketAndGTMStrategy)),
        guardrail_max_retries=guardrail_max_retries,
    )
