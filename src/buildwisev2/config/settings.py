"""Application settings for BuildWise v2.

Tasks and Crews never choose models or retry counts directly — they read
resolved values from ``Settings``, per the Tasks/Crews architecture PRDs
("Tasks never choose models", "Model Selection ... Agent Factory resolves
the actual LLM").
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from buildwisev2.domain.common import FlowRuntimeLimits


class ModelTier(StrEnum):
    """Coarse model tiers referenced by Agent contracts.

    ``FAST`` — discovery-style extraction work.
    ``STANDARD`` — most specialist reasoning (Product, BA, Market, QA).
    ``ADVANCED`` — architecture-heavy specialists (Solution/AI/Security).
    ``LEAD_REVIEW`` — the cross-artifact final reviewer.
    """

    FAST = "fast"
    STANDARD = "standard"
    ADVANCED = "advanced"
    LEAD_REVIEW = "lead_review"


class Settings(BaseSettings):
    """Reads only ``BUILDWISEV2_``-prefixed process environment variables.

    Deliberately does not load the shared repo-root ``.env`` file: it is
    v1 ``buildwise``'s configuration surface with unrelated/conflicting
    unprefixed names (e.g. ``CORS_ALLOWED_ORIGINS``) that pydantic-settings'
    dotenv source does not filter by ``env_prefix`` the same way it filters
    OS environment variables. Provider credentials (``OPENAI_API_KEY``,
    ``ANTHROPIC_API_KEY``, ...) are read directly by CrewAI/LiteLLM from the
    process environment regardless, so exporting them (or keeping them in
    the root ``.env`` your shell already loads) is unaffected by this.
    """

    model_config = SettingsConfigDict(
        env_prefix="BUILDWISEV2_",
        extra="ignore",
    )

    # --- model resolution -------------------------------------------------
    fast_model: str = "openai/gpt-5-mini"
    standard_model: str = "openai/gpt-5-mini"
    advanced_model: str = "openai/gpt-5.2"
    lead_review_model: str = "openai/gpt-5.2"

    # --- CrewAI runtime -----------------------------------------------------
    crewai_verbose: bool = False
    crew_cache: bool = True
    crew_memory: bool = False
    agent_max_iterations: int = 15

    # --- retries --------------------------------------------------------
    max_retries_per_operation: int = 2

    # --- runtime limits ---------------------------------------------------
    runtime_limits: FlowRuntimeLimits = FlowRuntimeLimits()

    # --- API layer ----------------------------------------------------------
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # --- persistence ----------------------------------------------------
    flow_persistence_db_path: str = "data/buildwisev2_flows.db"

    def resolve_model(self, tier: ModelTier) -> str:
        return {
            ModelTier.FAST: self.fast_model,
            ModelTier.STANDARD: self.standard_model,
            ModelTier.ADVANCED: self.advanced_model,
            ModelTier.LEAD_REVIEW: self.lead_review_model,
        }[tier]


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached Settings instance."""

    return Settings()
