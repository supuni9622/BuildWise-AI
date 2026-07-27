from fastapi import APIRouter

from buildwise.api.v1.consultations import router as consultations_router
from buildwise.config.settings import get_settings
from buildwise.domain.api import ApiRootResponse

router = APIRouter()
settings = get_settings()
router.include_router(consultations_router)


@router.get("", response_model=ApiRootResponse, tags=["API"])
async def api_root() -> ApiRootResponse:
    return ApiRootResponse(
        name=settings.app_name,
        version=settings.app_version,
        api_version="v1",
        status="available",
    )
