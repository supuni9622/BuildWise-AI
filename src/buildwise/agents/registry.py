"""Registry for BuildWise agent contracts.

This module exposes the canonical set of BuildWise agent contracts.

The registry stores framework-independent AgentContract objects. The agent
factory will later translate these contracts into native ``crewai.Agent``
instances by resolving:

- model tiers
- CrewAI Skills
- official CrewAI tools
- MCP servers
- apps
- knowledge sources
- runtime settings
"""

from __future__ import annotations

from collections.abc import Iterable

from buildwise.agents.ai_architect import AI_ARCHITECT_CONTRACT
from buildwise.agents.base import AgentContract
from buildwise.agents.business_analyst import BUSINESS_ANALYST_CONTRACT
from buildwise.agents.lead_reviewer import LEAD_REVIEWER_CONTRACT
from buildwise.agents.market_and_gtm_strategist import (
    MARKET_AND_GTM_STRATEGIST_CONTRACT,
)
from buildwise.agents.product_discovery_analyst import (
    PRODUCT_DISCOVERY_ANALYST_CONTRACT,
)
from buildwise.agents.product_manager import PRODUCT_MANAGER_CONTRACT
from buildwise.agents.qa_evaluation_architect import (
    QA_EVALUATION_ARCHITECT_CONTRACT,
)
from buildwise.agents.security_architect import SECURITY_ARCHITECT_CONTRACT
from buildwise.agents.solution_architect import SOLUTION_ARCHITECT_CONTRACT
from buildwise.domain.enums import (
    AgentInvocationMode,
    AgentType,
    HandoffTarget,
    ModelTier,
)


class AgentContractRegistryError(RuntimeError):
    """Base exception raised by the BuildWise agent contract registry."""


class AgentContractNotFoundError(
    KeyError,
    AgentContractRegistryError,
):
    """Raised when an agent contract cannot be found."""


class DuplicateAgentContractError(
    ValueError,
    AgentContractRegistryError,
):
    """Raised when the registry receives duplicate agent contracts."""


class DisabledAgentContractError(
    AgentContractRegistryError,
):
    """Raised when a disabled contract is requested as an active contract."""


class AgentContractRegistry:
    """Validated registry containing BuildWise agent contracts.

    The registry is intentionally independent of CrewAI runtime construction.
    It enables the rest of the application to discover agent policy without
    importing individual contract modules.

    Native ``crewai.Agent`` instances are created later by ``AgentFactory``.
    """

    def __init__(
        self,
        contracts: Iterable[AgentContract],
    ) -> None:
        self._contracts: dict[AgentType, AgentContract] = {}

        for contract in contracts:
            self.register(contract)

    def register(
        self,
        contract: AgentContract,
        *,
        replace: bool = False,
    ) -> None:
        """Register an agent contract.

        Args:
            contract: Contract to add.
            replace: Whether an existing contract with the same agent type may
                be replaced.

        Raises:
            DuplicateAgentContractError: If the contract already exists and
                replacement was not explicitly enabled.
        """

        agent_type = self._agent_type_from_contract(contract)

        if agent_type in self._contracts and not replace:
            raise DuplicateAgentContractError(
                "An agent contract is already registered for "
                f"'{agent_type.value}'."
            )

        self._contracts[agent_type] = contract

    def get(
        self,
        agent_type: AgentType | str,
        *,
        require_enabled: bool = True,
    ) -> AgentContract:
        """Return one registered contract.

        Args:
            agent_type: Canonical agent identifier.
            require_enabled: Whether disabled contracts should raise an error.

        Raises:
            AgentContractNotFoundError: If the agent is unknown.
            DisabledAgentContractError: If the contract is disabled and an
                active contract was requested.
        """

        normalized_type = self._normalize_agent_type(agent_type)

        try:
            contract = self._contracts[normalized_type]
        except KeyError as exc:
            supported = ", ".join(
                item.value for item in self.agent_types()
            )

            raise AgentContractNotFoundError(
                f"No agent contract is registered for "
                f"'{normalized_type.value}'. Supported agents: {supported}."
            ) from exc

        if require_enabled and not contract.enabled:
            raise DisabledAgentContractError(
                f"Agent contract '{normalized_type.value}' is disabled."
            )

        return contract

    def contains(
        self,
        agent_type: AgentType | str,
    ) -> bool:
        """Return whether an agent contract is registered."""

        try:
            normalized_type = AgentType(agent_type)
        except ValueError:
            return False

        return normalized_type in self._contracts

    def is_enabled(
        self,
        agent_type: AgentType | str,
    ) -> bool:
        """Return whether a registered agent contract is enabled."""

        if not self.contains(agent_type):
            return False

        return self.get(
            agent_type,
            require_enabled=False,
        ).enabled

    def all(
        self,
        *,
        enabled_only: bool = True,
    ) -> tuple[AgentContract, ...]:
        """Return all contracts in canonical registry order."""

        contracts = tuple(self._contracts.values())

        if not enabled_only:
            return contracts

        return tuple(
            contract
            for contract in contracts
            if contract.enabled
        )

    def agent_types(
        self,
        *,
        enabled_only: bool = False,
    ) -> tuple[AgentType, ...]:
        """Return registered agent identifiers."""

        if not enabled_only:
            return tuple(self._contracts)

        return tuple(
            agent_type
            for agent_type, contract in self._contracts.items()
            if contract.enabled
        )

    def required(self) -> tuple[AgentContract, ...]:
        """Return all enabled, always-required agent contracts."""

        return tuple(
            contract
            for contract in self._contracts.values()
            if contract.enabled
            and contract.invocation_mode is AgentInvocationMode.REQUIRED
        )

    def conditional(self) -> tuple[AgentContract, ...]:
        """Return all enabled, conditionally selected agent contracts."""

        return tuple(
            contract
            for contract in self._contracts.values()
            if contract.enabled
            and contract.invocation_mode
            is AgentInvocationMode.CONDITIONAL
        )

    def by_model_tier(
        self,
        model_tier: ModelTier | str,
        *,
        enabled_only: bool = True,
    ) -> tuple[AgentContract, ...]:
        """Return contracts assigned to a model-routing tier."""

        normalized_tier = ModelTier(model_tier)

        return tuple(
            contract
            for contract in self._contracts.values()
            if contract.model_tier is normalized_tier
            and (contract.enabled or not enabled_only)
        )

    def by_handoff_target(
        self,
        handoff_target: HandoffTarget | str,
        *,
        enabled_only: bool = True,
    ) -> tuple[AgentContract, ...]:
        """Return contracts allowed to hand off to a target."""

        normalized_target = HandoffTarget(handoff_target)

        return tuple(
            contract
            for contract in self._contracts.values()
            if normalized_target in contract.handoff_targets
            and (contract.enabled or not enabled_only)
        )

    def with_tools(
        self,
        *,
        enabled_only: bool = True,
    ) -> tuple[AgentContract, ...]:
        """Return contracts that request one or more CrewAI tools."""

        return tuple(
            contract
            for contract in self._contracts.values()
            if contract.capabilities.tool_keys
            and (contract.enabled or not enabled_only)
        )

    def with_skills(
        self,
        *,
        enabled_only: bool = True,
    ) -> tuple[AgentContract, ...]:
        """Return contracts that declare CrewAI Skills."""

        return tuple(
            contract
            for contract in self._contracts.values()
            if contract.capabilities.skill_paths
            and (contract.enabled or not enabled_only)
        )

    def validate(self) -> None:
        """Validate registry-wide agent invariants.

        Individual contract validation is handled by Pydantic. This method
        validates relationships that can only be checked across contracts.

        Raises:
            AgentContractRegistryError: If a registry-wide invariant fails.
        """

        self._validate_complete_agent_set()
        self._validate_unique_contract_keys()
        self._validate_handoff_targets()
        self._validate_required_agent_set()

    def _validate_complete_agent_set(self) -> None:
        """Require every canonical BuildWise agent to be registered."""

        expected = set(AgentType)
        registered = set(self._contracts)

        missing = expected.difference(registered)

        if not missing:
            return

        formatted = ", ".join(
            sorted(agent_type.value for agent_type in missing)
        )

        raise AgentContractRegistryError(
            f"Missing canonical agent contracts: {formatted}."
        )

    def _validate_unique_contract_keys(self) -> None:
        """Ensure contract keys remain globally unique."""

        keys = [
            contract.key
            for contract in self._contracts.values()
        ]

        if len(keys) != len(set(keys)):
            raise AgentContractRegistryError(
                "Agent contract keys must be globally unique."
            )

    def _validate_handoff_targets(self) -> None:
        """Validate handoffs that point to known agent roles."""

        agent_target_map: dict[HandoffTarget, AgentType] = {
            HandoffTarget.MARKET_AND_GTM_SPECIALIST: (
                AgentType.MARKET_AND_GTM_STRATEGIST
            ),
            HandoffTarget.SOLUTION_ARCHITECT: (
                AgentType.SOLUTION_ARCHITECT
            ),
            HandoffTarget.AI_ARCHITECT: AgentType.AI_ARCHITECT,
            HandoffTarget.SECURITY_ARCHITECT: (
                AgentType.SECURITY_ARCHITECT
            ),
            HandoffTarget.QA_AND_EVALUATION_ARCHITECT: (
                AgentType.QA_AND_EVALUATION_ARCHITECT
            ),
            HandoffTarget.LEAD_REVIEWER: AgentType.LEAD_REVIEWER,
        }

        for contract in self._contracts.values():
            for target in contract.handoff_targets:
                target_agent_type = agent_target_map.get(target)

                if target_agent_type is None:
                    continue

                target_contract = self._contracts.get(
                    target_agent_type
                )

                if target_contract is None:
                    raise AgentContractRegistryError(
                        f"Agent '{contract.key}' hands off to "
                        f"'{target.value}', but the corresponding agent "
                        "contract is not registered."
                    )

                if not target_contract.enabled:
                    raise AgentContractRegistryError(
                        f"Agent '{contract.key}' hands off to disabled "
                        f"agent '{target_agent_type.value}'."
                    )

    def _validate_required_agent_set(self) -> None:
        """Require the core BuildWise agents to remain enabled and required."""

        required_agent_types = {
            AgentType.PRODUCT_DISCOVERY_ANALYST,
            AgentType.PRODUCT_MANAGER,
            AgentType.BUSINESS_ANALYST,
            AgentType.LEAD_REVIEWER,
        }

        for agent_type in required_agent_types:
            contract = self._contracts.get(agent_type)

            if contract is None:
                raise AgentContractRegistryError(
                    f"Required agent '{agent_type.value}' is not registered."
                )

            if not contract.enabled:
                raise AgentContractRegistryError(
                    f"Required agent '{agent_type.value}' cannot be disabled."
                )

            if (
                contract.invocation_mode
                is not AgentInvocationMode.REQUIRED
            ):
                raise AgentContractRegistryError(
                    f"Core agent '{agent_type.value}' must use "
                    "AgentInvocationMode.REQUIRED."
                )

    @staticmethod
    def _normalize_agent_type(
        agent_type: AgentType | str,
    ) -> AgentType:
        """Normalize an agent identifier or raise a registry error."""

        try:
            return AgentType(agent_type)
        except ValueError as exc:
            supported = ", ".join(
                item.value for item in AgentType
            )

            raise AgentContractNotFoundError(
                f"Unknown agent type '{agent_type}'. "
                f"Supported agents: {supported}."
            ) from exc

    @staticmethod
    def _agent_type_from_contract(
        contract: AgentContract,
    ) -> AgentType:
        """Resolve the canonical agent type from a contract key."""

        try:
            return AgentType(contract.key)
        except ValueError as exc:
            raise AgentContractRegistryError(
                f"Agent contract key '{contract.key}' does not match a "
                "canonical AgentType."
            ) from exc


DEFAULT_AGENT_CONTRACTS: tuple[AgentContract, ...] = (
    PRODUCT_DISCOVERY_ANALYST_CONTRACT,
    PRODUCT_MANAGER_CONTRACT,
    BUSINESS_ANALYST_CONTRACT,
    MARKET_AND_GTM_STRATEGIST_CONTRACT,
    SOLUTION_ARCHITECT_CONTRACT,
    AI_ARCHITECT_CONTRACT,
    SECURITY_ARCHITECT_CONTRACT,
    QA_EVALUATION_ARCHITECT_CONTRACT,
    LEAD_REVIEWER_CONTRACT,
)


AGENT_CONTRACT_REGISTRY = AgentContractRegistry(
    contracts=DEFAULT_AGENT_CONTRACTS,
)

AGENT_CONTRACT_REGISTRY.validate()