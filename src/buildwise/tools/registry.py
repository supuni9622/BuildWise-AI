from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from enum import StrEnum

from crewai.tools import BaseTool
from crewai_tools import (
    GithubSearchTool,
    ScrapeWebsiteTool,
    SerperDevTool,
)


class ToolKey(StrEnum):
    """Canonical identifiers for CrewAI tools enabled in BuildWise."""

    WEB_SEARCH = "web_search"
    WEB_SCRAPER = "web_scraper"
    GITHUB_SEARCH = "github_search"


class ToolConfigurationError(RuntimeError):
    """Raised when an official CrewAI tool cannot be configured safely."""


ToolFactory = Callable[[], BaseTool]


class ToolRegistry:
    """Lazy registry for official CrewAI tools used by BuildWise.

    This registry does not reimplement any CrewAI tool.

    It provides:

    - stable BuildWise tool identifiers
    - lazy tool construction
    - environment validation
    - duplicate prevention
    - controlled tool resolution for the agent factory

    Tools are instantiated only when an agent contract requests them.
    """

    def __init__(self) -> None:
        self._factories: dict[ToolKey, ToolFactory] = {
            ToolKey.WEB_SEARCH: self._build_web_search,
            ToolKey.WEB_SCRAPER: self._build_web_scraper,
            ToolKey.GITHUB_SEARCH: self._build_github_search,
        }

    @property
    def available_keys(self) -> tuple[ToolKey, ...]:
        """Return all registered tool identifiers."""

        return tuple(self._factories)

    def contains(self, key: ToolKey | str) -> bool:
        """Return whether a tool identifier is registered."""

        try:
            normalized_key = ToolKey(key)
        except ValueError:
            return False

        return normalized_key in self._factories

    def resolve(self, key: ToolKey | str) -> BaseTool:
        """Instantiate and return one official CrewAI tool."""

        try:
            normalized_key = ToolKey(key)
        except ValueError as exc:
            supported = ", ".join(registered_key.value for registered_key in self.available_keys)
            raise KeyError(
                f"Unknown BuildWise tool key '{key}'. Supported tools: {supported}."
            ) from exc

        factory = self._factories.get(normalized_key)

        if factory is None:
            raise KeyError(f"No tool factory is registered for '{normalized_key.value}'.")

        return factory()

    def resolve_many(
        self,
        keys: Iterable[ToolKey | str],
    ) -> list[BaseTool]:
        """Instantiate a unique ordered collection of CrewAI tools."""

        normalized_keys: list[ToolKey] = []
        seen: set[ToolKey] = set()

        for key in keys:
            try:
                normalized_key = ToolKey(key)
            except ValueError as exc:
                raise KeyError(f"Unknown BuildWise tool key '{key}'.") from exc

            if normalized_key in seen:
                continue

            seen.add(normalized_key)
            normalized_keys.append(normalized_key)

        return [self.resolve(normalized_key) for normalized_key in normalized_keys]

    @staticmethod
    def _build_web_search() -> BaseTool:
        """Create CrewAI's official Serper web-search tool."""

        if not os.getenv("SERPER_API_KEY"):
            raise ToolConfigurationError("SERPER_API_KEY is required to use the 'web_search' tool.")

        return SerperDevTool()

    @staticmethod
    def _build_web_scraper() -> BaseTool:
        """Create CrewAI's official website-scraping tool."""

        return ScrapeWebsiteTool()

    @staticmethod
    def _build_github_search() -> BaseTool:
        """Create CrewAI's official semantic GitHub-search tool."""

        github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

        if not github_token:
            raise ToolConfigurationError(
                "GITHUB_TOKEN or GH_TOKEN is required to use the 'github_search' tool."
            )

        return GithubSearchTool(
            gh_token=github_token,
            content_types=[
                "code",
                "repo",
                "pr",
                "issue",
            ],
        )


TOOL_REGISTRY = ToolRegistry()
