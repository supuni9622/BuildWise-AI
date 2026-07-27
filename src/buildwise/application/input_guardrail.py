"""Input boundary for user-controlled consultation content."""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from buildwise.domain.guardrails import InputGuardrailResult, InputGuardrailViolation
from buildwise.security import scan_content


class InputGuardrailProcessor:
    """Reject prompt-injection attempts and secrets before persistence/model use."""

    def __init__(self, *, maximum_characters: int = 50_000) -> None:
        self._maximum_characters = maximum_characters

    def inspect(self, payload: Any) -> InputGuardrailResult:
        text = "\n".join(self._iter_strings(payload))
        if len(text) > self._maximum_characters:
            return InputGuardrailResult(
                allowed=False,
                risk_level="high",
                detected_patterns=["input_size_limit"],
                rejection_reason="The submitted content exceeds the guardrail size limit.",
            )

        scan = scan_content(text)
        detected = sorted({*scan.injection_patterns, *scan.secret_patterns})
        if detected:
            reason = (
                "The submitted content contains unsafe instructions or sensitive "
                "credential material and cannot be processed."
            )
            return InputGuardrailResult(
                allowed=False,
                risk_level="high",
                detected_patterns=detected,
                redaction_count=len(scan.secret_patterns),
                rejection_reason=reason,
            )

        return InputGuardrailResult(allowed=True, risk_level="low")

    def require_allowed(self, payload: Any) -> InputGuardrailResult:
        result = self.inspect(payload)
        if not result.allowed:
            raise InputGuardrailViolation(result)
        return result

    def _iter_strings(self, value: Any) -> Sequence[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, BaseModel):
            return self._iter_strings(value.model_dump(mode="python"))
        if isinstance(value, Mapping):
            return [
                item
                for child in value.values()
                for item in self._iter_strings(child)
            ]
        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
            return [item for child in value for item in self._iter_strings(child)]
        return []
