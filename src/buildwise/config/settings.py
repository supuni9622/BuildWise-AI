from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BuildWise AI"
    app_env: Literal["local", "test", "docker", "staging", "production"] = "local"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    database_url: str = "sqlite:///./data/buildwise.db"

    report_storage_backend: Literal["filesystem", "s3"] = "filesystem"
    report_storage_path: Path = Path("data/reports")
    store_blueprint_json: bool = False
    s3_report_bucket: str | None = None
    aws_region: str | None = None
    s3_endpoint_url: str | None = None

    openai_api_key: SecretStr | None = None
    primary_agent_model: str = "openai/gpt-5-mini"
    architect_model: str = "openai/gpt-5.2"
    lead_reviewer_model: str = "openai/gpt-5.2"
    fast_model: str = "openai/gpt-5-mini"

    crewai_tracing_enabled: bool = True
    crewai_verbose: bool = True
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_request_timeout_seconds: int = Field(default=90, ge=10, le=300)
    max_agent_iterations: int = Field(default=12, ge=1, le=50)
    max_execution_seconds: int = Field(default=900, ge=60, le=3600)

    max_session_tokens: int = Field(default=120_000, ge=1_000)
    max_estimated_cost_usd: float = Field(default=10.0, ge=0.0)
    max_agent_executions: int = Field(default=20, ge=1)
    max_tool_calls: int = Field(default=30, ge=0)
    max_retries_per_operation: int = Field(default=2, ge=0, le=5)
    api_rate_limit_requests: int = Field(default=30, ge=1, le=10_000)
    api_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)
    max_active_consultations: int = Field(default=10, ge=1, le=1_000)

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        return normalized.rstrip("/")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {sorted(allowed)}")
        return normalized

    @property
    def provider_configuration_ready(self) -> bool:
        model_values = (
            self.primary_agent_model,
            self.architect_model,
            self.lead_reviewer_model,
            self.fast_model,
        )
        uses_openai = any(model.startswith("openai/") for model in model_values)
        return not uses_openai or self.openai_api_key is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
