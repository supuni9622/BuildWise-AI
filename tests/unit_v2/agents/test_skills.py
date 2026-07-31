"""Unit tests verifying every specialist Agent gets exactly its own Skill and
tools stay Market & GTM-only. No live LLM calls — Agent/Skill construction
never calls a model.
"""

from __future__ import annotations

import os

import pytest

from buildwisev2.agents import AgentFactory, AgentType

os.environ.setdefault("OPENAI_API_KEY", "sk-test")


@pytest.fixture
def agent_factory() -> AgentFactory:
    return AgentFactory()


@pytest.mark.parametrize("agent_type", list(AgentType))
def test_every_agent_loads_exactly_its_own_skill(
    agent_factory: AgentFactory,
    agent_type: AgentType,
) -> None:
    agent = agent_factory.create(agent_type)

    skill_names = [skill.name for skill in (agent.skills or [])]

    assert skill_names == [agent_type.value.replace("_", "-")]


def test_only_market_and_gtm_strategist_has_tools(agent_factory: AgentFactory) -> None:
    for agent_type in AgentType:
        agent = agent_factory.create(agent_type)
        if agent_type == AgentType.MARKET_AND_GTM_STRATEGIST:
            assert {tool.name for tool in (agent.tools or [])} == {
                "Search the internet with Serper",
                "Read website content",
            }
        else:
            assert not agent.tools
