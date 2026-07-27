"""Small process-local API limiter for the unauthenticated MVP."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock
from time import monotonic

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from buildwise.domain.exceptions import RateLimitExceeded
from buildwise.observability.context import get_request_id


class InMemoryRateLimiter:
    """Fixed-window-equivalent sliding limiter scoped by client and operation."""

    def __init__(self, *, requests: int, window_seconds: int) -> None:
        self._requests = requests
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def require_capacity(self, key: str) -> None:
        now = monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self._requests:
                raise RateLimitExceeded(
                    "Too many consultation requests. Please retry later."
                )
            events.append(now)


class ConsultationRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: object,
        *,
        requests: int,
        window_seconds: int,
    ) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._limiter = InMemoryRateLimiter(
            requests=requests,
            window_seconds=window_seconds,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "POST" and "/consultations" in request.url.path:
            client = request.client.host if request.client else "unknown"
            operation = (
                "clarification"
                if request.url.path.endswith("/clarifications")
                else "start"
            )
            try:
                self._limiter.require_capacity(f"{client}:{operation}")
            except RateLimitExceeded as error:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": "CAPACITY_LIMIT_EXCEEDED",
                        "message": str(error),
                        "recoverable": True,
                        "stage": "rate_limit",
                        "request_id": get_request_id(),
                        "session_id": None,
                        "details": None,
                    },
                )
        return await call_next(request)
