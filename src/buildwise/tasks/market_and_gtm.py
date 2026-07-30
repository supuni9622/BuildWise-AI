"""Market and GTM task factory.

Creates the native CrewAI Task assigned to the Market and GTM Strategist. The
task evaluates market segments, competitors, positioning, pricing hypotheses,
channels, and launch experiments for the approved product.

``MarketAndGTMStrategy`` validates its references against a real
``ProductDefinition`` (persona and feature IDs), so this task always runs
after Product Definition and Requirements exist. It supports two input
modes: same-Crew native task context (when composed inside the Product
Planning Crew) or literal structured values (when the upstream artifacts
already completed in a separate Crew).
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.artifact_drafts import MarketAndGTMStrategyDraft
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.planning.specialist_context import (
    ProductDefinitionProjection,
    RequirementsProjection,
)
from buildwise.tasks.context_wiring import (
    PRODUCT_DEFINITION_CONTEXT_PLACEHOLDER,
    REQUIREMENTS_CONTEXT_PLACEHOLDER,
)
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    require_self_consistent_draft,
)
from buildwise.tasks.instructions import IDENTIFIER_RULES
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_market_and_gtm_task(
    *,
    agent: Agent,
    product_definition_task: Task | None = None,
    requirements_task: Task | None = None,
    product_definition: ProductDefinition | None = None,
    requirements: RequirementsSpecification | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Market and GTM task for the Market and GTM Strategist.

    Exactly one of ``(product_definition_task, requirements_task)`` or
    ``(product_definition, requirements)`` must be supplied together. Pass
    the task pair when Product Definition and Requirements execute inside
    the same Crew so CrewAI can wire native task context. Pass the
    structured value pair when both already completed in a separate Crew.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.MARKET_AND_GTM_STRATEGIST``. The agent already owns
            the web_search and web_scraper tools; this task does not
            instantiate or restrict them.
        product_definition_task: The Product Definition task, when executing
            in the same Crew.
        requirements_task: The Requirements task, when executing in the same
            Crew.
        product_definition: The completed ProductDefinition, when Product
            Definition ran in a separate Crew.
        requirements: The completed RequirementsSpecification, when
            Requirements ran in a separate Crew.
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

    same_crew_mode = product_definition_task is not None or requirements_task is not None
    structured_mode = product_definition is not None or requirements is not None

    if same_crew_mode and structured_mode:
        raise ValueError(
            "create_market_and_gtm_task accepts either "
            "(product_definition_task, requirements_task) or "
            "(product_definition, requirements), not both."
        )

    if same_crew_mode and (product_definition_task is None or requirements_task is None):
        raise ValueError(
            "create_market_and_gtm_task requires both product_definition_task "
            "and requirements_task when using same-Crew context."
        )

    if structured_mode and (product_definition is None or requirements is None):
        raise ValueError(
            "create_market_and_gtm_task requires both product_definition and "
            "requirements when using structured cross-Crew inputs."
        )

    if not same_crew_mode and not structured_mode:
        raise ValueError(
            "create_market_and_gtm_task requires either "
            "(product_definition_task, requirements_task) or "
            "(product_definition, requirements)."
        )

    context_section = (
        "Available structured context:\n"
        f"ProductDefinition: {PRODUCT_DEFINITION_CONTEXT_PLACEHOLDER}\n"
        f"RequirementsSpecification: {REQUIREMENTS_CONTEXT_PLACEHOLDER}"
        if same_crew_mode
        else (
            "Available structured context:\n"
            "ProductDefinition: "
            f"{ProductDefinitionProjection.from_artifact(product_definition).model_dump_json()}\n"  # type: ignore[arg-type]
            "RequirementsSpecification: "
            f"{RequirementsProjection.from_artifact(requirements).model_dump_json()}"  # type: ignore[arg-type]
        )
    )

    description = (
        "Objective: Evaluate the market and go-to-market strategy for the "
        "approved product.\n\n"
        f"{context_section}\n\n"
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
        "Required output: A schema-valid MarketAndGTMStrategyDraft where every claim "
        "not directly derivable from the supplied product definition and "
        "requirements is backed by an evidence entry.\n\n"
        f"{IDENTIFIER_RULES}\n"
        "Important boundaries:\n"
        "- Do not redefine ProductDefinition scope, personas, or features.\n"
        "- Do not select software architecture or technology.\n"
        "- Do not present an inference as strong or externally verified "
        "evidence; use the web_search and web_scraper tools already "
        "attached to you when they are available. If a research tool is not "
        "attached, explicitly record the missing research under evidence_gaps "
        "and do not invent external evidence.\n\n"
        "Failure or uncertainty handling: When market evidence is "
        "insufficient, record it under evidence_gaps and set decision to "
        "'requires_more_research' or 'requires_clarification' rather than "
        "fabricating market facts."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid MarketAndGTMStrategyDraft JSON object matching the "
        "compact draft model exactly, with no additional "
        "prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(MarketAndGTMStrategyDraft),
        require_self_consistent_draft(MarketAndGTMStrategyDraft, MarketAndGTMStrategy),
    )

    task_kwargs: dict[str, object] = {
        "name": "market_and_gtm_strategy",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "output_pydantic": MarketAndGTMStrategyDraft,
        "guardrails": guardrails,
        "guardrail_max_retries": guardrail_max_retries,
        # See tasks/context_wiring.py: context is always fully embedded in
        # description above, so this must be an explicit [], not left
        # unset, or CrewAI's NOT_SPECIFIED default injects raw output from
        # every other task the Crew has run so far.
        "context": [],
    }

    return Task(**task_kwargs)
