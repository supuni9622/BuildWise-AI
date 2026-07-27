"""Application-safe control-flow exceptions."""


class RateLimitExceeded(RuntimeError):
    """Raised when an API caller exceeds its request allowance."""


class ActiveSessionLimitExceeded(RuntimeError):
    """Raised when this process cannot safely start more Flow executions."""
