"""CrewAI Flows."""

from typing import Any

__all__ = ["BlueprintBuilder", "BuildWiseConsultingFlow"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from buildwise.flows.consulting_flow import (
            BlueprintBuilder,
            BuildWiseConsultingFlow,
        )

        return {
            "BlueprintBuilder": BlueprintBuilder,
            "BuildWiseConsultingFlow": BuildWiseConsultingFlow,
        }[name]
    raise AttributeError(name)
