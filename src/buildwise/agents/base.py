from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import Field, field_validator, model_validator

from buildwise.domain.common import (
    BuildWiseModel,
    MediumText,
    ShortText,
    Slug,
)
from buildwise.domain.enums import (
    AgentFailureBehavior,
    AgentInvocationMode,
    HandoffTarget,
    ModelTier,
)


class AgentCapabilityPolicy(BuildWiseModel):
    """Controlled capabilities available to one BuildWise agent.

    CrewAI distinguishes between action capabilities and context
    capabilities:

    - tools, MCP servers, and apps allow an agent to perform actions
    - skills and knowledge provide instructions and contextual information

    This model records which capabilities BuildWise allows the later agent
    factory to attach to a native CrewAI Agent.
    """

    tool_keys: list[Slug] = Field(default_factory=list)
    mcp_server_keys: list[Slug] = Field(default_factory=list)
    app_keys: list[Slug] = Field(default_factory=list)

    skill_paths: list[str] = Field(default_factory=list)
    knowledge_paths: list[str] = Field(default_factory=list)

    @field_validator(
        "tool_keys",
        "mcp_server_keys",
        "app_keys",
    )
    @classmethod
    def ensure_unique_capability_keys(
        cls,
        value: list[Slug],
    ) -> list[Slug]:
        """Prevent duplicate action-capability references."""

        if len(value) != len(set(value)):
            raise ValueError("Agent action-capability keys must contain unique values.")

        return value

    @field_validator(
        "skill_paths",
        "knowledge_paths",
    )
    @classmethod
    def validate_context_paths(
        cls,
        value: list[str],
        info: object,
    ) -> list[str]:
        """Normalize and validate relative context-capability paths."""

        field_name = getattr(info, "field_name", "paths")
        normalized_paths: list[str] = []

        for raw_path in value:
            stripped_path = raw_path.strip()

            if not stripped_path:
                raise ValueError(f"{field_name} cannot contain empty paths.")

            path = PurePosixPath(stripped_path)

            if path.is_absolute():
                raise ValueError(f"{field_name} must contain relative project paths.")

            if ".." in path.parts:
                raise ValueError(f"{field_name} cannot contain parent-directory traversal.")

            normalized_paths.append(path.as_posix())

        if len(normalized_paths) != len(set(normalized_paths)):
            raise ValueError(f"{field_name} must contain unique paths.")

        return normalized_paths

    @property
    def has_action_capabilities(self) -> bool:
        """Return whether the agent has any action capability."""

        return bool(self.tool_keys or self.mcp_server_keys or self.app_keys)

    @property
    def has_context_capabilities(self) -> bool:
        """Return whether the agent has any context capability."""

        return bool(self.skill_paths or self.knowledge_paths)


class AgentRuntimeSettings(BuildWiseModel):
    """CrewAI runtime settings applied when building an agent."""

    verbose: bool = True
    allow_delegation: bool = False

    max_iter: int = Field(default=12, ge=1, le=50)
    max_rpm: int | None = Field(default=None, ge=1, le=10_000)

    reasoning: bool = False
    max_reasoning_attempts: int | None = Field(
        default=None,
        ge=1,
        le=10,
    )

    respect_context_window: bool = True
    use_system_prompt: bool = True

    cache: bool = True

    @model_validator(mode="after")
    def validate_reasoning_settings(self) -> AgentRuntimeSettings:
        """Keep reasoning settings internally consistent."""

        if self.reasoning and self.max_reasoning_attempts is None:
            raise ValueError("max_reasoning_attempts is required when reasoning is enabled.")

        if not self.reasoning and self.max_reasoning_attempts is not None:
            raise ValueError(
                "max_reasoning_attempts cannot be provided when reasoning is disabled."
            )

        return self


class AgentContract(BuildWiseModel):
    """Canonical BuildWise configuration for a native CrewAI Agent.

    The contract contains stable application policy and concise agent identity.

    Detailed working methodology belongs in CrewAI Skills. Reusable factual
    material belongs in CrewAI Knowledge. Task-specific instructions belong
    in the Crew task definition.

    The later agent factory converts this contract into `crewai.Agent`.
    """

    key: Slug
    display_name: ShortText

    role: ShortText
    goal: MediumText
    backstory: MediumText

    responsibilities: list[MediumText] = Field(min_length=1)
    exclusions: list[MediumText] = Field(min_length=1)

    model_tier: ModelTier
    invocation_mode: AgentInvocationMode

    capabilities: AgentCapabilityPolicy = Field(
        default_factory=AgentCapabilityPolicy,
    )
    runtime: AgentRuntimeSettings = Field(
        default_factory=AgentRuntimeSettings,
    )

    failure_behavior: AgentFailureBehavior
    handoff_targets: list[HandoffTarget] = Field(default_factory=list)

    output_model_path: str | None = None

    enabled: bool = True

    @field_validator(
        "responsibilities",
        "exclusions",
    )
    @classmethod
    def ensure_unique_text_values(
        cls,
        value: list[MediumText],
        info: object,
    ) -> list[MediumText]:
        """Prevent duplicated responsibility and exclusion statements."""

        field_name = getattr(info, "field_name", "values")

        if len(value) != len(set(value)):
            raise ValueError(f"{field_name} must contain unique values.")

        return value

    @field_validator("handoff_targets")
    @classmethod
    def ensure_unique_handoff_targets(
        cls,
        value: list[HandoffTarget],
    ) -> list[HandoffTarget]:
        """Prevent duplicate downstream handoff targets."""

        if len(value) != len(set(value)):
            raise ValueError("handoff_targets must contain unique values.")

        return value

    @field_validator("output_model_path")
    @classmethod
    def validate_output_model_path(
        cls,
        value: str | None,
    ) -> str | None:
        """Validate an optional dotted import path for structured output."""

        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError("output_model_path cannot contain only whitespace.")

        path_parts = normalized.split(".")

        if len(path_parts) < 2:
            raise ValueError("output_model_path must be a dotted Python import path.")

        if any(not part.isidentifier() for part in path_parts):
            raise ValueError("output_model_path contains an invalid Python identifier.")

        if not normalized.startswith("buildwise.domain."):
            raise ValueError("output_model_path must reference a BuildWise domain model.")

        return normalized

    @model_validator(mode="after")
    def validate_agent_contract(self) -> AgentContract:
        """Validate agent ownership and runtime policy."""

        responsibility_set = {responsibility.casefold() for responsibility in self.responsibilities}
        exclusion_set = {exclusion.casefold() for exclusion in self.exclusions}

        overlap = responsibility_set.intersection(exclusion_set)

        if overlap:
            formatted_overlap = ", ".join(sorted(overlap))
            raise ValueError(
                f"Agent responsibilities and exclusions cannot overlap: {formatted_overlap}."
            )

        if self.invocation_mode is AgentInvocationMode.REQUIRED and not self.handoff_targets:
            raise ValueError("A required agent must define at least one handoff target.")

        if (
            self.failure_behavior is AgentFailureBehavior.REQUEST_USER_INPUT
            and HandoffTarget.DISCOVERY_FLOW not in self.handoff_targets
        ):
            raise ValueError(
                "An agent that requests user input must be able to hand off to the Discovery Flow."
            )

        if self.runtime.allow_delegation and not self.handoff_targets:
            raise ValueError("An agent with delegation enabled must define handoff targets.")

        return self
