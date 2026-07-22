from pydantic import BaseModel, ConfigDict, Field


class UsageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str | None = None
    model: str | None = None
    agent_name: str | None = None
    task_name: str | None = None
    tool_name: str | None = None

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    agent_execution_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    execution_duration_ms: int = Field(default=0, ge=0)


class UsageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[UsageRecord] = Field(default_factory=list)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    agent_execution_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    execution_duration_ms: int = Field(default=0, ge=0)
