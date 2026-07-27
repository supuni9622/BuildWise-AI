"""Official CrewAI tools used by BuildWise.

BuildWise reuses CrewAI's native tool ecosystem and places a deterministic
sanitizing proxy around resolved tools.

The ToolRegistry provides:

- lazy tool construction
- centralized configuration
- stable BuildWise tool identifiers
- dependency injection for the Agent Factory
- mandatory output sanitization before agent use

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
