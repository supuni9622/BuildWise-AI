from collections.abc import Awaitable, Callable
from time import perf_counter

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from buildwise.observability.context import new_request_id, set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        clear_contextvars()

        request_id = request.headers.get("X-Request-ID") or new_request_id()
        set_request_id(request_id)
        bind_contextvars(
            request_id=request_id,
            session_id=None,
            flow_id=None,
            trace_id=None,
            stage="http_request",
        )

        logger = structlog.get_logger(__name__)
        started_at = perf_counter()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            status="started",
        )

        response = await call_next(request)
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            http_status=response.status_code,
            status="completed",
            duration_ms=duration_ms,
        )

        clear_contextvars()
        return response
