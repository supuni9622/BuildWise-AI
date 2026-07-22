from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from buildwise.observability.context import get_request_id


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    recoverable: bool
    stage: str
    request_id: str
    session_id: str | None = None
    details: list[dict[str, Any]] | None = None


def _response(
    *,
    status_code: int,
    code: str,
    message: str,
    recoverable: bool,
    stage: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        code=code,
        message=message,
        recoverable=recoverable,
        stage=stage,
        request_id=get_request_id(),
        details=details,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    logger = structlog.get_logger(__name__)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "request_validation_failed",
            path=request.url.path,
            status="failed",
            error_code="REQUEST_VALIDATION_FAILED",
        )
        return _response(
            status_code=422,
            code="REQUEST_VALIDATION_FAILED",
            message="The request payload is invalid.",
            recoverable=True,
            stage="request_validation",
            details=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        logger.warning(
            "http_request_failed",
            path=request.url.path,
            status="failed",
            error_code="HTTP_ERROR",
            http_status=exc.status_code,
        )
        return _response(
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=str(exc.detail),
            recoverable=exc.status_code < 500,
            stage="http",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            status="failed",
            error_code="INTERNAL_ERROR",
            error_type=type(exc).__name__,
        )
        return _response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected internal error occurred.",
            recoverable=False,
            stage="internal",
        )
