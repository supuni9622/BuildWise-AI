"""Registry for BuildWise Crew factories.

Provides stable Crew identifiers and Crew-factory discovery. The registry
never holds Crew instances, executes a Crew, or makes routing decisions;
those responsibilities belong to the CrewAI Flow. A fresh ``crewai.Crew``
must be constructed by calling the resolved factory for every execution.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

from crewai import Crew

from buildwise.crews.ai_architecture import create_ai_architecture_crew
from buildwise.crews.discovery import create_discovery_crew
from buildwise.crews.lead_review import create_lead_review_crew
from buildwise.crews.market_and_gtm import create_market_and_gtm_crew
from buildwise.crews.product_definition import create_product_definition_crew
from buildwise.crews.qa_evaluation import create_qa_evaluation_crew
from buildwise.crews.requirements import create_requirements_crew
from buildwise.crews.security_architecture import create_security_architecture_crew
from buildwise.crews.solution_architecture import create_solution_architecture_crew


class CrewKey(StrEnum):
    """Canonical identifiers for BuildWise Crew factories."""

    DISCOVERY = "discovery"
    PRODUCT_DEFINITION = "product_definition"
    REQUIREMENTS = "requirements"
    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_EVALUATION = "qa_evaluation"
    LEAD_REVIEW = "lead_review"


CrewFactory = Callable[..., Crew]


class CrewRegistryError(RuntimeError):
    """Base exception raised by the BuildWise Crew registry."""


class CrewFactoryNotFoundError(KeyError, CrewRegistryError):
    """Raised when a Crew factory cannot be found."""


class DuplicateCrewFactoryError(ValueError, CrewRegistryError):
    """Raised when the registry receives a duplicate Crew factory."""


class CrewRegistry:
    """Validated registry mapping stable Crew keys to Crew factories."""

    def __init__(self, factories: dict[CrewKey, CrewFactory]) -> None:
        self._factories: dict[CrewKey, CrewFactory] = {}

        for key, factory in factories.items():
            self.register(key, factory)

    def register(
        self,
        key: CrewKey,
        factory: CrewFactory,
        *,
        replace: bool = False,
    ) -> None:
        """Register one Crew factory under a stable key.

        Args:
            key: Canonical Crew identifier.
            factory: Callable that returns a native ``crewai.Crew``.
            replace: Whether an existing factory for this key may be
                replaced.

        Raises:
            DuplicateCrewFactoryError: If a factory is already registered
                for ``key`` and ``replace`` is ``False``.
        """

        if key in self._factories and not replace:
            raise DuplicateCrewFactoryError(
                f"A Crew factory is already registered for '{key.value}'."
            )

        self._factories[key] = factory

    def resolve(self, key: CrewKey | str) -> CrewFactory:
        """Return the Crew factory registered for one key.

        Raises:
            CrewFactoryNotFoundError: If no factory is registered for
                ``key``.
        """

        normalized_key = self._normalize_key(key)
        factory = self._factories.get(normalized_key)

        if factory is None:
            raise CrewFactoryNotFoundError(
                f"No Crew factory is registered for '{normalized_key.value}'."
            )

        return factory

    def contains(self, key: CrewKey | str) -> bool:
        """Return whether a Crew factory is registered for one key."""

        try:
            normalized_key = CrewKey(key)
        except ValueError:
            return False

        return normalized_key in self._factories

    def list(self) -> tuple[CrewKey, ...]:
        """Return every registered Crew key."""

        return tuple(self._factories)

    @staticmethod
    def _normalize_key(key: CrewKey | str) -> CrewKey:
        """Normalize a Crew identifier or raise a registry error."""

        try:
            return CrewKey(key)
        except ValueError as exc:
            supported = ", ".join(item.value for item in CrewKey)
            raise CrewFactoryNotFoundError(
                f"Unknown Crew key '{key}'. Supported keys: {supported}."
            ) from exc


DEFAULT_CREW_FACTORIES: dict[CrewKey, CrewFactory] = {
    CrewKey.DISCOVERY: create_discovery_crew,
    CrewKey.PRODUCT_DEFINITION: create_product_definition_crew,
    CrewKey.REQUIREMENTS: create_requirements_crew,
    CrewKey.MARKET_AND_GTM: create_market_and_gtm_crew,
    CrewKey.SOLUTION_ARCHITECTURE: create_solution_architecture_crew,
    CrewKey.AI_ARCHITECTURE: create_ai_architecture_crew,
    CrewKey.SECURITY_ARCHITECTURE: create_security_architecture_crew,
    CrewKey.QA_EVALUATION: create_qa_evaluation_crew,
    CrewKey.LEAD_REVIEW: create_lead_review_crew,
}


CREW_REGISTRY = CrewRegistry(DEFAULT_CREW_FACTORIES)
