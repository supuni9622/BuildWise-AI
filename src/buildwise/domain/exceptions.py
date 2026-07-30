"""Application-safe control-flow exceptions."""


class RateLimitExceeded(RuntimeError):
    """Raised when an API caller exceeds its request allowance."""


class ActiveSessionLimitExceeded(RuntimeError):
    """Raised when this process cannot safely start more Flow executions."""


class CrewExecutionError(RuntimeError):
    """Raised when a Crew fails after CrewAI's own internal retries are exhausted.

    Wraps whatever CrewAI (or a guardrail) raised out of ``Crew.kickoff()`` —
    most commonly a task exhausting its bounded guardrail-retry budget. The
    original exception is preserved as ``__cause__`` for server-side logs,
    but this type's own message is deliberately generic: unlike a guardrail
    validation error (which only ever describes the consultation's own
    generated content), an arbitrary underlying exception could carry
    provider/internal detail this application does not persist or expose.

    ``stage`` identifies which Flow stage's Crew failed, which is safe to
    surface and is enough context to know whether resubmitting the same
    consultation is worth trying.
    """

    def __init__(self, *, stage: str) -> None:
        self.stage = stage
        super().__init__(f"Crew execution failed at stage '{stage}'.")
