from pydantic import SecretStr

from buildwise.agents.factory import AgentFactory
from buildwise.agents.market_and_gtm_strategist import (
    MARKET_AND_GTM_STRATEGIST_CONTRACT,
)
from buildwise.agents.product_discovery_analyst import (
    PRODUCT_DISCOVERY_ANALYST_CONTRACT,
)
from buildwise.config.settings import Settings


def _factory() -> AgentFactory:
    return AgentFactory(
        settings=Settings(
            openai_api_key=SecretStr("sk-test-not-a-real-key"),
            max_agent_iterations=4,
            crewai_tracing_enabled=False,
        )
    )


def test_toolless_structured_agent_uses_one_iteration() -> None:
    agent = _factory().create_from_contract(PRODUCT_DISCOVERY_ANALYST_CONTRACT)

    assert agent.max_iter == 1


def test_action_capable_agent_keeps_bounded_iteration_budget() -> None:
    agent = _factory().create_from_contract(MARKET_AND_GTM_STRATEGIST_CONTRACT)

    assert agent.max_iter == 4
