from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buildwise.api.rate_limiter import ConsultationRateLimitMiddleware
from buildwise.api.router import api_router
from buildwise.config.logging import configure_logging
from buildwise.config.settings import get_settings
from buildwise.domain.errors import register_exception_handlers
from buildwise.observability.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger = structlog.get_logger(__name__)

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        app_env=settings.app_env,
        app_version=settings.app_version,
    )
    yield
    logger.info("application_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        ConsultationRateLimitMiddleware,
        requests=settings.api_rate_limit_requests,
        window_seconds=settings.api_rate_limit_window_seconds,
    )
    register_exception_handlers(application)
    application.include_router(api_router)

    return application


app = create_app()
