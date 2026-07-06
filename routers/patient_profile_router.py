"""API router for patient self-declared allergies and chronic conditions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from agents.embedding_client import embed_texts
from agents.pinecone_client import delete_vector_by_id, upsert_vectors
from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from database.connection import get_engine
from database.repositories.medication_repository import MedicationRepository
from database.repositories.patient_allergy_repository import PatientAllergyRepository
from database.repositories.patient_chronic_condition_repository import PatientChronicConditionRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import AuthenticationException, NotFoundException
from helpers.drug_normalizer import normalize_drug_name
from helpers.response_helper import success_response
from models.prescription_model import Prescription
from services.chunking_service import build_medication_chunks
from schemas.request.patient_profile_request import (
    PatientAllergyCreateRequest,
    PatientChronicConditionCreateRequest,
    PatientMedicationCreateRequest,
)
from schemas.response.base_response import BaseResponse
from schemas.response.patient_profile_response import (
    PatientAllergyListResponse,
    PatientAllergyResponse,
    PatientChronicConditionListResponse,
    PatientChronicConditionResponse,
    PatientMedicationListResponse,
    PatientMedicationResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/profile", tags=["Patient Profile"])


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.post("/allergies", response_model=PatientAllergyResponse)
async def create_allergy(
    request: Request,
    body: PatientAllergyCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientAllergyResponse:
    """Create a self-declared allergy record for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientAllergyRepository(session=session, request_id=request_id)
        allergy = repo.create(
            patient_id=patient_id,
            allergen=body.allergen,
            reaction=body.reaction,
            severity=body.severity,
        )
        payload = success_response(data=allergy, request_id=request_id)
        return PatientAllergyResponse.model_validate(payload)
    finally:
        session.close()


@router.get("/allergies", response_model=PatientAllergyListResponse)
async def list_allergies(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientAllergyListResponse:
    """Retrieve all self-declared allergy records for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientAllergyRepository(session=session, request_id=request_id)
        allergies = repo.list_by_patient(patient_id=patient_id)
        payload = success_response(data=allergies, request_id=request_id)
        return PatientAllergyListResponse.model_validate(payload)
    finally:
        session.close()


@router.delete("/allergies/{id}", response_model=BaseResponse[Any])
async def delete_allergy(
    request: Request,
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> BaseResponse[Any]:
    """Delete a self-declared allergy record owned by the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientAllergyRepository(session=session, request_id=request_id)
        allergy = repo.get_by_id(record_id=id, patient_id=patient_id)
        if not allergy:
            raise NotFoundException("Allergy record not found or access denied")
        repo.delete(allergy)
        payload = success_response(message="Allergy record deleted successfully", request_id=request_id)
        return BaseResponse[Any].model_validate(payload)
    finally:
        session.close()


@router.post("/conditions", response_model=PatientChronicConditionResponse)
async def create_condition(
    request: Request,
    body: PatientChronicConditionCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientChronicConditionResponse:
    """Create a self-declared chronic condition record for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientChronicConditionRepository(session=session, request_id=request_id)
        condition = repo.create(
            patient_id=patient_id,
            condition_name=body.condition_name,
            diagnosed_date=body.diagnosed_date,
            status=body.status,
        )
        payload = success_response(data=condition, request_id=request_id)
        return PatientChronicConditionResponse.model_validate(payload)
    finally:
        session.close()


@router.get("/conditions", response_model=PatientChronicConditionListResponse)
async def list_conditions(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientChronicConditionListResponse:
    """Retrieve all self-declared chronic condition records for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientChronicConditionRepository(session=session, request_id=request_id)
        conditions = repo.list_by_patient(patient_id=patient_id)
        payload = success_response(data=conditions, request_id=request_id)
        return PatientChronicConditionListResponse.model_validate(payload)
    finally:
        session.close()


@router.delete("/conditions/{id}", response_model=BaseResponse[Any])
async def delete_condition(
    request: Request,
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> BaseResponse[Any]:
    """Delete a self-declared chronic condition record owned by the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = PatientChronicConditionRepository(session=session, request_id=request_id)
        condition = repo.get_by_id(record_id=id, patient_id=patient_id)
        if not condition:
            raise NotFoundException("Chronic condition record not found or access denied")
        repo.delete(condition)
        payload = success_response(message="Chronic condition record deleted successfully", request_id=request_id)
        return BaseResponse[Any].model_validate(payload)
    finally:
        session.close()


@router.post("/medications", response_model=PatientMedicationResponse)
async def create_medication(
    request: Request,
    body: PatientMedicationCreateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientMedicationResponse:
    """Manually add a medication record for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = MedicationRepository(session=session, request_id=request_id)
        normalized = normalize_drug_name(body.drug_name)
        med = repo.create_manual(
            patient_id=patient_id,
            drug_name_raw=body.drug_name,
            drug_name_normalized=normalized,
            dosage=body.dosage,
            frequency=body.frequency,
            start_date=body.start_date,
        )
        try:
            chunks = build_medication_chunks(
                prescription=None,
                doctor=None,
                medications=[med],
                patient_id=patient_id,
                document_id=None,
                entry_source="manual_entry",
            )
            if chunks:
                vecs = embed_texts([chunks[0].text])
                upsert_vectors([{
                    "id": chunks[0].chunk_id,
                    "values": vecs[0],
                    "metadata": chunks[0].metadata,
                }])
                logger.info("Synced manual medication to Pinecone", medication_id=str(med.medication_id))
        except Exception as exc:
            logger.error("Failed to sync manual medication to Pinecone", error=str(exc))
        payload = success_response(data=med, request_id=request_id)
        return PatientMedicationResponse.model_validate(payload)
    finally:
        session.close()


@router.get("/medications", response_model=PatientMedicationListResponse)
async def list_medications(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> PatientMedicationListResponse:
    """Retrieve all medication records (both OCR-extracted and manual) for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = MedicationRepository(session=session, request_id=request_id)
        meds = repo.list_by_patient(patient_id=patient_id)
        payload = success_response(data=meds, request_id=request_id)
        return PatientMedicationListResponse.model_validate(payload)
    finally:
        session.close()


@router.delete("/medications/{id}", response_model=BaseResponse[Any])
async def delete_medication(
    request: Request,
    id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> BaseResponse[Any]:
    """Discontinue a medication record owned by the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    session: Session = SessionLocal(bind=get_engine())
    try:
        repo = MedicationRepository(session=session, request_id=request_id)
        med = repo.get_by_id_and_patient(medication_id=id, patient_id=patient_id)
        if not med:
            raise NotFoundException("Medication record not found or access denied")
        med.status = "DISCONTINUED"
        repo.update(med)
        try:
            if med.entry_source == "manual_entry" or not med.prescription_id:
                chunk_id = f"patient_{patient_id}_manual_med_{med.medication_id}"
            else:
                presc = session.get(Prescription, med.prescription_id)
                doc_id = presc.document_id if presc else ""
                chunk_id = f"patient_{patient_id}_doc_{doc_id}_med_{med.medication_id}"
            delete_vector_by_id(chunk_id)
            logger.info("Removed discontinued medication vector from Pinecone", chunk_id=chunk_id)
        except Exception as exc:
            logger.error("Failed to remove discontinued medication from Pinecone", error=str(exc))
        payload = success_response(message="Medication marked as DISCONTINUED successfully", request_id=request_id)
        return BaseResponse[Any].model_validate(payload)
    finally:
        session.close()

