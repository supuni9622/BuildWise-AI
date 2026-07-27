"""Factory for constructing native CrewAI agents from BuildWise contracts.

The contract layer is the stable BuildWise source of truth for agent policy.
This factory translates those contracts into native ``crewai.Agent`` objects.

The factory intentionally delegates runtime capabilities to CrewAI:

- ``crewai.Agent`` provides the native agent runtime
- CrewAI Skills provide reusable working methodology
- official CrewAI tools provide actions
- CrewAI Tasks define task-specific instructions and structured outputs
- CrewAI Crews execute focused reasoning units
- CrewAI Flows orchestrate state, routing, and execution order

Structured output models are not attached here. They belong to the CrewAI Task
through ``output_pydantic``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

import structlog
from crewai import LLM, Agent
from crewai.tools import BaseTool

from buildwise.agents.base import AgentContract
from buildwise.agents.registry import (
    AGENT_CONTRACT_REGISTRY,
    AgentContractRegistry,
)
from buildwise.config.settings import Settings, get_settings
from buildwise.domain.enums import AgentFailureBehavior, AgentType, ModelTier
from buildwise.tools.registry import (
    TOOL_REGISTRY,
    ToolConfigurationError,
    ToolRegistry,
)

logger = structlog.get_logger(__name__)


class AgentFactoryError(RuntimeError):
    """Base error raised while constructing a native CrewAI agent."""


class AgentProviderConfigurationError(AgentFactoryError):
    """Raised when the configured LLM provider is not ready."""


class AgentSkillNotFoundError(AgentFactoryError):
    """Raised when a contract references a missing CrewAI Skill."""


class UnsupportedAgentCapabilityError(AgentFactoryError):
    """Raised when a capability has no configured runtime resolver."""


class KnowledgeResolver(Protocol):
    """Protocol for resolving BuildWise knowledge references.

    CrewAI Knowledge sources are runtime objects rather than arbitrary path
    strings. A dedicated resolver can be injected after the Knowledge layer is
    implemented.
    """

    def __call__(
        self,
        paths: Iterable[str],
    ) -> list[Any]:
        """Resolve knowledge paths into CrewAI knowledge-source objects."""


class MCPResolver(Protocol):
    """Protocol for resolving BuildWise MCP server references."""

    def __call__(
        self,
        keys: Iterable[str],
    ) -> list[Any]:
        """Resolve registered MCP keys into CrewAI-compatible values."""


class AppResolver(Protocol):
    """Protocol for resolving CrewAI application-integration references."""

    def __call__(
        self,
        keys: Iterable[str],
    ) -> list[Any]:
        """Resolve registered app keys into CrewAI-compatible values."""


LLMFactory = Callable[[str, Settings], LLM]


class AgentFactory:
    """Construct native CrewAI agents from validated BuildWise contracts.

    The factory resolves:

    - ``ModelTier`` into a configured CrewAI ``LLM``
    - tool keys through the BuildWise official-tool registry
    - relative skill paths into validated project paths
    - optional Knowledge, MCP, and App references through injected resolvers
    - contract runtime settings into native CrewAI Agent settings

    The factory does not:

    - define CrewAI Tasks
    - attach ``output_pydantic``
    - create Crews
    - orchestrate Flows
    - reimplement CrewAI tools, Skills, Knowledge, MCPs, or Apps
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        contract_registry: AgentContractRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        project_root: Path | None = None,
        llm_factory: LLMFactory | None = None,
        knowledge_resolver: KnowledgeResolver | None = None,
        mcp_resolver: MCPResolver | None = None,
        app_resolver: AppResolver | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._contract_registry = contract_registry or AGENT_CONTRACT_REGISTRY
        self._tool_registry = tool_registry or TOOL_REGISTRY

        self._project_root = (
            project_root.resolve() if project_root is not None else self._default_project_root()
        )

        self._llm_factory = llm_factory or self._build_default_llm

        self._knowledge_resolver = knowledge_resolver
        self._mcp_resolver = mcp_resolver
        self._app_resolver = app_resolver

    @property
    def project_root(self) -> Path:
        """Return the project root used to resolve CrewAI Skill paths."""

        return self._project_root

    def create(
        self,
        agent_type: AgentType | str,
    ) -> Agent:
        """Build one native CrewAI Agent from its registered contract.

        Args:
            agent_type: Canonical BuildWise agent identifier.

        Returns:
            Fully configured native ``crewai.Agent``.

        Raises:
            AgentProviderConfigurationError: If the model provider is not
                configured.
            AgentSkillNotFoundError: If a declared Skill path is unavailable.
            UnsupportedAgentCapabilityError: If a contract requests Knowledge,
                MCPs, or Apps without an appropriate resolver.
        """

        contract = self._contract_registry.get(agent_type)

        return self.create_from_contract(contract)

    def create_from_contract(
        self,
        contract: AgentContract,
    ) -> Agent:
        """Build a native CrewAI Agent from one validated contract."""

        self._validate_provider_configuration()

        model_name = self.resolve_model_name(contract.model_tier)
        llm = self._llm_factory(model_name, self._settings)

        tools = self._resolve_tools(contract)
        skills = self._resolve_skills(contract)
        knowledge_sources = self._resolve_knowledge(contract)
        mcps = self._resolve_mcps(contract)
        apps = self._resolve_apps(contract)

        runtime = contract.runtime
        reasoning_enabled = (
            runtime.reasoning and self._settings.crewai_reasoning_enabled
        )

        agent_kwargs: dict[str, Any] = {
            "role": contract.role,
            "goal": contract.goal,
            "backstory": contract.backstory,
            "llm": llm,
            "tools": tools,
            "skills": skills,
            "verbose": (runtime.verbose and self._settings.crewai_verbose),
            "allow_delegation": runtime.allow_delegation,
            "max_iter": min(
                runtime.max_iter,
                self._settings.max_agent_iterations,
            ),
            "max_rpm": runtime.max_rpm,
            "reasoning": reasoning_enabled,
            "respect_context_window": (runtime.respect_context_window),
            "use_system_prompt": runtime.use_system_prompt,
            "cache": runtime.cache,
            "max_execution_time": (self._settings.max_execution_seconds),
        }

        if reasoning_enabled:
            agent_kwargs["max_reasoning_attempts"] = (
                runtime.max_reasoning_attempts
            )

        if knowledge_sources:
            agent_kwargs["knowledge_sources"] = knowledge_sources

        if mcps:
            agent_kwargs["mcps"] = mcps

        if apps:
            agent_kwargs["apps"] = apps

        return Agent(**agent_kwargs)

    def create_many(
        self,
        agent_types: Iterable[AgentType | str],
    ) -> list[Agent]:
        """Create native CrewAI agents in the supplied order.

        Duplicate identifiers are ignored while preserving the order of their
        first occurrence.
        """

        normalized_types: list[AgentType] = []
        seen: set[AgentType] = set()

        for agent_type in agent_types:
            normalized_type = AgentType(agent_type)

            if normalized_type in seen:
                continue

            seen.add(normalized_type)
            normalized_types.append(normalized_type)

        return [self.create(agent_type) for agent_type in normalized_types]

    def create_required_agents(self) -> list[Agent]:
        """Create every enabled, always-required BuildWise agent."""

        return [
            self.create_from_contract(contract) for contract in self._contract_registry.required()
        ]

    def resolve_model_name(
        self,
        model_tier: ModelTier | str,
    ) -> str:
        """Resolve a BuildWise model tier into its configured model name."""

        normalized_tier = ModelTier(model_tier)

        model_by_tier: dict[ModelTier, str] = {
            ModelTier.FAST: self._settings.fast_model,
            ModelTier.PRIMARY: self._settings.primary_agent_model,
            ModelTier.ARCHITECT: self._settings.architect_model,
            ModelTier.LEAD_REVIEWER: (self._settings.lead_reviewer_model),
        }

        model_name = model_by_tier[normalized_tier].strip()

        if not model_name:
            raise AgentProviderConfigurationError(
                f"No model is configured for tier '{normalized_tier.value}'."
            )

        return model_name

    def _resolve_tools(
        self,
        contract: AgentContract,
    ) -> list[BaseTool]:
        """Resolve official CrewAI tools requested by an agent contract."""

        tools: list[BaseTool] = []
        for key in contract.capabilities.tool_keys:
            try:
                tools.append(self._tool_registry.resolve(key))
            except ToolConfigurationError as error:
                if (
                    contract.failure_behavior
                    is not AgentFailureBehavior.CONTINUE_WITH_LIMITATION
                ):
                    raise
                logger.warning(
                    "optional_agent_tool_unavailable",
                    agent=contract.key,
                    tool=str(key),
                    reason=str(error),
                )
        return tools

    def _resolve_skills(
        self,
        contract: AgentContract,
    ) -> list[str]:
        """Resolve and validate CrewAI Skill package paths.

        CrewAI expects a Skill package directory containing ``SKILL.md``.
        Contracts store project-relative package paths such as
        ``skills/ai_architect``.
        """

        resolved_paths: list[str] = []

        for relative_path in contract.capabilities.skill_paths:
            skill_directory = (self._project_root / relative_path).resolve()

            self._ensure_within_project_root(
                path=skill_directory,
                contract=contract,
            )

            skill_file = skill_directory / "SKILL.md"

            if not skill_directory.is_dir():
                raise AgentSkillNotFoundError(
                    f"Agent '{contract.key}' references missing Skill directory '{relative_path}'."
                )

            if not skill_file.is_file():
                raise AgentSkillNotFoundError(
                    f"Agent '{contract.key}' Skill directory "
                    f"'{relative_path}' does not contain SKILL.md."
                )

            resolved_paths.append(str(skill_directory))

        return resolved_paths

    def _resolve_knowledge(
        self,
        contract: AgentContract,
    ) -> list[Any]:
        """Resolve optional CrewAI Knowledge sources."""

        paths = contract.capabilities.knowledge_paths

        if not paths:
            return []

        if self._knowledge_resolver is None:
            raise UnsupportedAgentCapabilityError(
                f"Agent '{contract.key}' requests Knowledge sources "
                f"{list(paths)}, but no KnowledgeResolver was supplied to "
                "AgentFactory. Implement the BuildWise Knowledge layer or "
                "remove these knowledge_paths from the contract."
            )

        return self._knowledge_resolver(paths)

    def _resolve_mcps(
        self,
        contract: AgentContract,
    ) -> list[Any]:
        """Resolve optional CrewAI MCP server references."""

        keys = contract.capabilities.mcp_server_keys

        if not keys:
            return []

        if self._mcp_resolver is None:
            raise UnsupportedAgentCapabilityError(
                f"Agent '{contract.key}' requests MCP servers "
                f"{list(keys)}, but no MCPResolver was supplied to "
                "AgentFactory."
            )

        return self._mcp_resolver(keys)

    def _resolve_apps(
        self,
        contract: AgentContract,
    ) -> list[Any]:
        """Resolve optional CrewAI App integration references."""

        keys = contract.capabilities.app_keys

        if not keys:
            return []

        if self._app_resolver is None:
            raise UnsupportedAgentCapabilityError(
                f"Agent '{contract.key}' requests CrewAI Apps "
                f"{list(keys)}, but no AppResolver was supplied to "
                "AgentFactory."
            )

        return self._app_resolver(keys)

    def _validate_provider_configuration(self) -> None:
        """Ensure the configured model provider has its required credentials."""

        if self._settings.provider_configuration_ready:
            return

        raise AgentProviderConfigurationError(
            "The configured BuildWise models require OpenAI, but OPENAI_API_KEY is not configured."
        )

    def _build_default_llm(
        self,
        model_name: str,
        settings: Settings,
    ) -> LLM:
        """Create CrewAI's native LLM wrapper.

        CrewAI remains responsible for provider execution, retries, request
        formatting, and model interaction.
        """

        llm_kwargs: dict[str, Any] = {
            "model": model_name,
            "timeout": settings.llm_request_timeout_seconds,
            "max_retries": settings.llm_max_retries,
        }

        if model_name.startswith("openai/"):
            if settings.openai_api_key is None:
                raise AgentProviderConfigurationError(
                    f"OPENAI_API_KEY is required for model '{model_name}'."
                )

            llm_kwargs["api_key"] = settings.openai_api_key.get_secret_value()

        return LLM(**llm_kwargs)

    def _ensure_within_project_root(
        self,
        *,
        path: Path,
        contract: AgentContract,
    ) -> None:
        """Prevent resolved Skill paths from escaping the project root."""

        try:
            path.relative_to(self._project_root)
        except ValueError as exc:
            raise AgentSkillNotFoundError(
                f"Agent '{contract.key}' Skill path '{path}' resolves "
                "outside the BuildWise project root."
            ) from exc

    @staticmethod
    def _default_project_root() -> Path:
        """Resolve the buildwise package root from this module location.

        Agent contract ``skill_paths`` are relative to ``src/buildwise``
        (for example ``skills/business_analyst``), which is where the Skill
        packages actually live.
        """

        return Path(__file__).resolve().parents[1]


AGENT_FACTORY = AgentFactory()
