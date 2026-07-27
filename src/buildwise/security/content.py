"""Shared deterministic detection and redaction for untrusted text."""

import re
from dataclasses import dataclass

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "instruction_override",
        re.compile(
            r"\b(?:ignore|disregard|override)\s+(?:all\s+)?"
            r"(?:previous|prior|above|system|developer)\s+instructions?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "prompt_exfiltration",
        re.compile(
            r"\b(?:reveal|show|print|return|repeat)\s+(?:the\s+)?"
            r"(?:system|developer)\s+(?:prompt|message|instructions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role_impersonation",
        re.compile(r"</?(?:system|developer|assistant)\b[^>]*>", re.IGNORECASE),
    ),
    (
        "jailbreak_attempt",
        re.compile(r"\b(?:jailbreak|developer\s+mode)\b", re.IGNORECASE),
    ),
)

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)


@dataclass(frozen=True)
class ContentScan:
    injection_patterns: tuple[str, ...]
    secret_patterns: tuple[str, ...]

    @property
    def unsafe(self) -> bool:
        return bool(self.injection_patterns or self.secret_patterns)


def scan_content(text: str) -> ContentScan:
    """Return pattern names only, never the matched sensitive content."""

    injections = tuple(name for name, pattern in _INJECTION_PATTERNS if pattern.search(text))
    secrets = tuple(name for name, pattern in _SECRET_PATTERNS if pattern.search(text))
    return ContentScan(injection_patterns=injections, secret_patterns=secrets)


def redact_secrets(text: str) -> tuple[str, int]:
    """Replace known secret formats and return the number of replacements."""

    redacted = text
    count = 0
    for _, pattern in _SECRET_PATTERNS:
        redacted, replacements = pattern.subn("[REDACTED_SECRET]", redacted)
        count += replacements
    return redacted, count
