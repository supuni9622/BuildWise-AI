"""Deterministic and model-assisted validation."""

from typing import Any

__all__ = ["validate_final_output", "validate_output"]


def __getattr__(name: str) -> Any:
    """Keep package exports lazy to avoid the Flow/state import cycle."""

    if name == "validate_final_output":
        from buildwise.validation.final_output_validator import validate_final_output

        return validate_final_output
    if name == "validate_output":
        from buildwise.validation.output_validator import validate_output

        return validate_output
    raise AttributeError(name)
