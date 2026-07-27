import pytest

from buildwise.agents.factory import AgentFactory
from buildwise.agents.market_and_gtm_strategist import (
    MARKET_AND_GTM_STRATEGIST_CONTRACT,
)
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentFailureBehavior
from buildwise.tools.registry import ToolConfigurationError, ToolRegistry


class _UnavailableToolRegistry(ToolRegistry):
    def resolve(self, key: str) -> None:
        raise ToolConfigurationError(f"{key} is not configured.")


def test_optional_tool_failure_is_omitted_for_continuation_agent() -> None:
    factory = AgentFactory(
        settings=Settings(app_env="test"),
        tool_registry=_UnavailableToolRegistry(),
    )

    assert factory._resolve_tools(MARKET_AND_GTM_STRATEGIST_CONTRACT) == []


def test_optional_tool_failure_remains_fatal_for_strict_agent() -> None:
    factory = AgentFactory(
        settings=Settings(app_env="test"),
        tool_registry=_UnavailableToolRegistry(),
    )
    contract = MARKET_AND_GTM_STRATEGIST_CONTRACT.model_copy(
        update={"failure_behavior": AgentFailureBehavior.FAIL_SESSION}
    )

    with pytest.raises(ToolConfigurationError, match="not configured"):
        factory._resolve_tools(contract)
