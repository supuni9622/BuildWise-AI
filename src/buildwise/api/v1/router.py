from fastapi import APIRouter

from buildwise.config.settings import get_settings
from buildwise.domain.api import ApiRootResponse

router = APIRouter()
settings = get_settings()


@router.get("", response_model=ApiRootResponse, tags=["API"])
async def api_root() -> ApiRootResponse:
    return ApiRootResponse(
        name=settings.app_name,
        version=settings.app_version,
        api_version="v1",
        status="available",
    )
