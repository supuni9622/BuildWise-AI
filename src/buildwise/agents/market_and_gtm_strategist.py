from __future__ import annotations

from buildwise.agents.base import (
    AgentCapabilityPolicy,
    AgentContract,
    AgentRuntimeSettings,
)
from buildwise.domain.enums import (
    AgentFailureBehavior,
    AgentInvocationMode,
    AgentType,
    HandoffTarget,
    ModelTier,
)


def build_market_and_gtm_strategist_contract() -> AgentContract:
    """Build the canonical contract for the Market & GTM Strategist.

    The Market & GTM Strategist converts a validated ProductDefinition into
    a MarketAndGTMStrategy covering market segments, competitors,
    opportunities, positioning, pricing, channels, and launch experiments.

    Detailed market research methodology belongs in the associated CrewAI
    Skill. Task-specific instructions and structured-output enforcement
    belong in the Specialist Crew task definitions.
    """

    return AgentContract(
        key=AgentType.MARKET_AND_GTM_STRATEGIST.value,
        display_name="Market & GTM Strategist",
        role="Market & Go-To-Market Strategist",
        goal=(
            "Produce a market analysis covering competitors, positioning, "
            "target customers, pricing direction, launch strategy, and "
            "growth recommendations."
        ),
        backstory=(
            "You are an experienced product marketing strategist with "
            "expertise in SaaS, AI products, startup validation, product "
            "positioning, market sizing, and commercialization."
        ),
        responsibilities=[
            "Analyze the target market for the proposed product.",
            "Identify customer segments.",
            "Estimate market opportunity.",
            "Identify competitors and their positioning.",
            "Recommend a positioning strategy.",
            "Recommend a pricing approach.",
            "Recommend customer acquisition channels.",
            "Create an MVP launch strategy.",
            "Highlight commercial and market risks.",
        ],
        exclusions=[
            "Do not design technical or solution architecture.",
            "Do not produce implementation plans.",
            "Do not recommend infrastructure or technology choices.",
            "Do not modify product requirements.",
            "Do not estimate engineering effort.",
        ],
        model_tier=ModelTier.PRIMARY,
        invocation_mode=AgentInvocationMode.CONDITIONAL,
        capabilities=AgentCapabilityPolicy(
            tool_keys=[
                "web_search",
                "web_scraper",
            ],
            mcp_server_keys=[],
            app_keys=[],
            skill_paths=[
                "skills/market_and_gtm_strategist",
            ],
            knowledge_paths=[],
        ),
        runtime=AgentRuntimeSettings(
            verbose=True,
            allow_delegation=False,
            max_iter=12,
            max_rpm=None,
            reasoning=True,
            max_reasoning_attempts=3,
            respect_context_window=True,
            use_system_prompt=True,
            cache=True,
        ),
        failure_behavior=AgentFailureBehavior.CONTINUE_WITH_LIMITATION,
        handoff_targets=[
            HandoffTarget.LEAD_REVIEWER,
        ],
        output_model_path="buildwise.domain.market_and_gtm.MarketAndGTMStrategy",
        enabled=True,
    )


MARKET_AND_GTM_STRATEGIST_CONTRACT = build_market_and_gtm_strategist_contract()
