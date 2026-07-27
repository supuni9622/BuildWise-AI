"""Structured execution policies for BuildWise's allowlisted tools."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ToolSideEffect(StrEnum):
    READ_ONLY = "read_only"


class ToolPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    maximum_retries: int = Field(default=1, ge=0, le=3)
    maximum_input_characters: int = Field(default=20_000, ge=100)
    require_https_urls: bool = True
    allowed_domains: tuple[str, ...] = ()
    side_effect: ToolSideEffect = ToolSideEffect.READ_ONLY
    log_inputs: bool = False


DEFAULT_TOOL_POLICIES: dict[str, ToolPolicy] = {
    "web_search": ToolPolicy(key="web_search", timeout_seconds=30),
    "web_scraper": ToolPolicy(key="web_scraper", timeout_seconds=30),
    "github_search": ToolPolicy(key="github_search", timeout_seconds=45),
}
