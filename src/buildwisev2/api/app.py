"""FastAPI application exposing the BuildWise v2 Consulting Flow.

Matches the REST contract the existing ``web/`` frontend already expects
(``web/app/page.tsx``): ``POST /api/v1/consultations``,
``GET /api/v1/consultations/{id}``,
``POST /api/v1/consultations/{id}/clarifications``,
``GET /api/v1/consultations/{id}/result``.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from buildwisev2.api import service
from buildwisev2.api.schemas import (
    BlueprintResultResponse,
    ClarificationSubmission,
    ConsultationResponse,
    IntakeRequest,
)
from buildwisev2.config.settings import get_settings

router = APIRouter(prefix="/api/v1")


@router.post("/consultations", response_model=ConsultationResponse)
def create_consultation(request: IntakeRequest) -> ConsultationResponse:
    return service.start_consultation(request)


@router.get("/consultations/{consultation_id}", response_model=ConsultationResponse)
def read_consultation(consultation_id: str) -> ConsultationResponse:
    result = service.get_consultation(consultation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    return result


@router.post(
    "/consultations/{consultation_id}/clarifications",
    response_model=ConsultationResponse,
)
def answer_clarifications(
    consultation_id: str,
    submission: ClarificationSubmission,
) -> ConsultationResponse:
    result = service.submit_clarifications(consultation_id, submission)
    if result is None:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    return result


@router.get(
    "/consultations/{consultation_id}/result",
    response_model=BlueprintResultResponse,
)
def read_result(consultation_id: str) -> BlueprintResultResponse:
    result = service.get_result(consultation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Blueprint not ready.")
    return BlueprintResultResponse(result=result)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="BuildWise v2 API")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)
    return application


app = create_app()
