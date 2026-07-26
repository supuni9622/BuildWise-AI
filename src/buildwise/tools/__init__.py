"""Official CrewAI tools used by BuildWise.

BuildWise intentionally reuses CrewAI's native tool ecosystem instead of
implementing custom wrappers.

The ToolRegistry provides:

- lazy tool construction
- centralized configuration
- stable BuildWise tool identifiers
- dependency injection for the Agent Factory

Agents should obtain tools through the registry rather than instantiating
CrewAI tools directly.
"""

from buildwise.tools.registry import (
    TOOL_REGISTRY,
    ToolConfigurationError,
    ToolKey,
    ToolRegistry,
)

__all__ = [
    "TOOL_REGISTRY",
    "ToolConfigurationError",
    "ToolKey",
    "ToolRegistry",
]
