"""Unit tests for the ToolRegistry. No live network calls — only construction."""

from __future__ import annotations

import pytest

from buildwisev2.tools.registry import resolve_tools, supported_tool_keys


def test_resolve_tools_returns_fresh_instances_each_call() -> None:
    first = resolve_tools(("web_search", "web_scraper"))
    second = resolve_tools(("web_search",))

    assert len(first) == 2
    assert len(second) == 1
    assert first[0] is not second[0]


def test_resolve_tools_empty_tuple_returns_empty_list() -> None:
    assert resolve_tools(()) == []


def test_resolve_tools_unknown_key_raises() -> None:
    with pytest.raises(ValueError, match="Unknown tool key"):
        resolve_tools(("not_a_real_tool",))


def test_supported_tool_keys_contains_web_search_and_scraper() -> None:
    keys = supported_tool_keys()
    assert "web_search" in keys
    assert "web_scraper" in keys
