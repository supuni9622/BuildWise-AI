"""Official CrewAI tool registry.

Resolves the small set of stable tool keys referenced by
``AgentContract.tool_keys`` into native CrewAI/``crewai_tools`` tool
instances. Crews and Tasks never instantiate tools directly — only the
``AgentFactory`` calls into this registry, per the Tools layer PRDs.
"""

from __future__ import annotations

from collections.abc import Callable

from crewai.tools.base_tool import BaseTool
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

_TOOL_FACTORIES: dict[str, Callable[[], BaseTool]] = {
    "web_search": SerperDevTool,
    "web_scraper": ScrapeWebsiteTool,
}


def resolve_tools(tool_keys: tuple[str, ...]) -> list[BaseTool]:
    """Resolve stable tool keys into freshly constructed native tool instances.

    A new tool instance is created per call rather than shared/cached, so
    Agents never accidentally share mutable tool state across Crews.
    """

    tools: list[BaseTool] = []
    for key in tool_keys:
        factory = _TOOL_FACTORIES.get(key)
        if factory is None:
            raise ValueError(
                f"Unknown tool key {key!r}. Supported tool keys: {sorted(_TOOL_FACTORIES)}"
            )
        tools.append(factory())
    return tools


def supported_tool_keys() -> set[str]:
    return set(_TOOL_FACTORIES)
