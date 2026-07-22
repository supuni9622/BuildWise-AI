from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from buildwise.api.v1.router import router as v1_router
from buildwise.config.settings import get_settings
from buildwise.domain.health import HealthResponse
from buildwise.persistence.database import check_database_connection

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/ready", response_model=HealthResponse, tags=["Operations"])
async def ready() -> HealthResponse:
    database_ready = await run_in_threadpool(check_database_connection)
    provider_ready = settings.provider_configuration_ready
    ready_status = database_ready and provider_ready

    return HealthResponse(
        status="ready" if ready_status else "not_ready",
        service=settings.app_name,
        version=settings.app_version,
        checks={
            "database": database_ready,
            "llm_provider_configuration": provider_ready,
        },
    )


api_router = APIRouter()
api_router.include_router(router)
api_router.include_router(v1_router, prefix=settings.api_v1_prefix)
