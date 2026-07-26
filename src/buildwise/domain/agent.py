"""Canonical agent contracts for BuildWise AI.

This module defines the metadata and contracts for every BuildWise agent.

These contracts are independent of CrewAI. They describe:

- what an agent is responsible for
- what it receives
- what it produces
- which tools it may use
- how failures are handled
- where outputs are handed next

The actual CrewAI Agent implementations live under:

src/buildwise/agents/
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.enums import (
    AgentFailureBehavior,
    AgentInvocationMode,
    AgentType,
    HandoffTarget,
    ModelTier,
)


class AgentCapability(BaseModel):
    """A capability that an agent possesses."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class AgentSkill(BaseModel):
    """A reusable skill or expertise area."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class AgentResponsibility(BaseModel):
    """A concrete responsibility owned by an agent."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str


class ToolPermission(BaseModel):
    """Defines whether an agent may use a tool."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    required: bool = False
    reason: str


class AgentContract(BaseModel):
    """Canonical BuildWise agent contract."""

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    agent_type: AgentType

    role: str

    mission: str

    goal: str

    description: str

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    capabilities: list[AgentCapability] = Field(default_factory=list)

    skills: list[AgentSkill] = Field(default_factory=list)

    responsibilities: list[AgentResponsibility] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Inputs / Outputs
    # ------------------------------------------------------------------

    input_model: type[BaseModel]

    output_model: type[BaseModel]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    invocation_mode: AgentInvocationMode

    model_tier: ModelTier

    failure_behavior: AgentFailureBehavior

    # ------------------------------------------------------------------
    # Tool permissions
    # ------------------------------------------------------------------

    allowed_tools: list[ToolPermission] = Field(default_factory=list)

    forbidden_tools: list[str] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    downstream_targets: list[HandoffTarget] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Optional metadata
    # ------------------------------------------------------------------

    notes: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRegistry(BaseModel):
    """Registry containing all BuildWise agent contracts."""

    model_config = ConfigDict(extra="forbid")

    agents: dict[AgentType, AgentContract] = Field(default_factory=dict)

    def register(self, contract: AgentContract) -> None:
        """Register a new agent contract."""
        self.agents[contract.agent_type] = contract

    def get(self, agent_type: AgentType) -> AgentContract:
        """Return an agent contract."""
        return self.agents[agent_type]

    def exists(self, agent_type: AgentType) -> bool:
        """Check whether an agent contract exists."""
        return agent_type in self.agents

    def all(self) -> list[AgentContract]:
        """Return every registered contract."""
        return list(self.agents.values())

    def by_model_tier(self, tier: ModelTier) -> list[AgentContract]:
        """Return agents assigned to a specific model tier."""
        return [
            contract
            for contract in self.agents.values()
            if contract.model_tier == tier
        ]

    def by_handoff_target(
        self,
        target: HandoffTarget,
    ) -> list[AgentContract]:
        """Return agents that can hand off to the given target."""
        return [
            contract
            for contract in self.agents.values()
            if target in contract.downstream_targets
        ]