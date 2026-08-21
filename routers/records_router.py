"""API router for patient medical records listing endpoints (prescriptions and lab results)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from database.connection import get_engine
from database.session import SessionLocal
from exceptions.custom_exceptions import AuthenticationException
from helpers.response_helper import success_response
from models.doctor_model import Doctor
from models.lab_result_model import LabResult
from models.prescription_model import Prescription
from schemas.response.records_response import (
    LabResultListResponse,
    LabResultRecordResponse,
    MedicationSummary,
    PrescriptionListResponse,
    PrescriptionRecordResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/records", tags=["Records"])


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.get("/prescriptions", response_model=PrescriptionListResponse)
async def list_prescriptions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PrescriptionListResponse:
    """Retrieve a paginated list of prescription records for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        all_rows = session.execute(
            select(Prescription, Doctor)
            .outerjoin(Doctor, Prescription.doctor_id == Doctor.doctor_id)
            .options(selectinload(Prescription.medications))
            .filter(Prescription.patient_id == patient_id)
            .order_by(Prescription.prescribed_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()

        results = [
            PrescriptionRecordResponse(
                prescription_id=rx.prescription_id,
                prescribed_date=rx.prescribed_date,
                doctor_name=doc.name if doc else None,
                diagnosis=rx.diagnosis or [],
                medications=[
                    MedicationSummary.model_validate(med)
                    for med in (rx.medications or [])
                ],
                document_id=rx.document_id,
            )
            for rx, doc in all_rows
        ]

        logger.info(
            "Fetched prescription records",
            patient_id=patient_id,
            result_count=len(results),
        )
        payload = success_response(data=results, request_id=request_id)
        return PrescriptionListResponse.model_validate(payload)
    finally:
        session.close()


@router.get("/lab-results", response_model=LabResultListResponse)
async def list_lab_results(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> LabResultListResponse:
    """Retrieve a paginated list of laboratory test results for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        all_lab_rows = session.scalars(
            select(LabResult)
            .filter(LabResult.patient_id == patient_id)
            .order_by(LabResult.test_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()

        results = [LabResultRecordResponse.model_validate(row) for row in all_lab_rows]

        logger.info(
            "Fetched lab result records",
            patient_id=patient_id,
            result_count=len(results),
        )
        payload = success_response(data=results, request_id=request_id)
        return LabResultListResponse.model_validate(payload)
    finally:
        session.close()
