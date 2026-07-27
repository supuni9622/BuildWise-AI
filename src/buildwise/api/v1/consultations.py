"""Consultation start, clarification, status, and result endpoints."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from buildwise.api.v1.consultation_service import ConsultationService
from buildwise.domain.api import (
    ConsultationResponse,
    ConsultationResultResponse,
    StartConsultationRequest,
    SubmitClarificationsRequest,
)
from buildwise.persistence.database import get_engine
from buildwise.persistence.flow_store import BuildWiseFlowStore

router = APIRouter(prefix="/consultations", tags=["Consultations"])


@lru_cache
def get_consultation_service() -> ConsultationService:
    """Return the process-wide consultation service."""

    return ConsultationService(flow_store=BuildWiseFlowStore(get_engine()))


ConsultationServiceDependency = Annotated[
    ConsultationService,
    Depends(get_consultation_service),
]


@router.post(
    "",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_consultation(
    request: StartConsultationRequest,
    service: ConsultationServiceDependency,
) -> ConsultationResponse:
    return await run_in_threadpool(service.start, request)


@router.post(
    "/{consultation_id}/clarifications",
    response_model=ConsultationResponse,
)
async def submit_clarifications(
    consultation_id: str,
    request: SubmitClarificationsRequest,
    service: ConsultationServiceDependency,
) -> ConsultationResponse:
    try:
        return await run_in_threadpool(
            service.submit_clarifications,
            consultation_id,
            request,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: str,
    service: ConsultationServiceDependency,
) -> ConsultationResponse:
    try:
        return await run_in_threadpool(service.get, consultation_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{consultation_id}/result", response_model=ConsultationResultResponse)
async def get_consultation_result(
    consultation_id: str,
    service: ConsultationServiceDependency,
) -> ConsultationResultResponse:
    try:
        return await run_in_threadpool(service.get_result, consultation_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
