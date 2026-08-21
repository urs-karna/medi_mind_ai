"""API router for patient medical timeline listing endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from database.connection import get_engine
from database.session import SessionLocal
from exceptions.custom_exceptions import AuthenticationException
from helpers.response_helper import success_response
from models.medical_timeline_model import MedicalTimeline
from schemas.response.timeline_response import TimelineEventResponse, TimelineListResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/timeline", tags=["Timeline"])


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.get("", response_model=TimelineListResponse)
async def list_timeline_events(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TimelineListResponse:
    """Retrieve a paginated list of chronological medical timeline events for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        all_event_rows = session.scalars(
            select(MedicalTimeline)
            .filter(MedicalTimeline.patient_id == patient_id)
            .order_by(MedicalTimeline.event_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()

        results = [TimelineEventResponse.model_validate(row) for row in all_event_rows]

        logger.info(
            "Fetched timeline events",
            patient_id=patient_id,
            result_count=len(results),
        )
        payload = success_response(data=results, request_id=request_id)
        return TimelineListResponse.model_validate(payload)
    finally:
        session.close()
