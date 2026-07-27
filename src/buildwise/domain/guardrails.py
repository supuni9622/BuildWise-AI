"""Domain models and errors for deterministic content guardrails."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InputGuardrailResult(BaseModel):
    """Safe, non-verbatim result of screening user-controlled input."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    risk_level: Literal["low", "high"]
    detected_patterns: list[str] = Field(default_factory=list)
    redaction_count: int = 0
    rejection_reason: str | None = None


class SanitizedToolOutput(BaseModel):
    """Sanitized representation of untrusted external tool output."""

    model_config = ConfigDict(extra="forbid")

    safe_content: str
    injection_detected: bool = False
    discarded_sections: int = 0
    redaction_count: int = 0
    truncated: bool = False


class InputGuardrailViolation(ValueError):
    """Raised when direct user input must not enter model context."""

    def __init__(self, result: InputGuardrailResult) -> None:
        self.result = result
        super().__init__(
            result.rejection_reason
            or "The submitted content was rejected by the input guardrail."
        )
