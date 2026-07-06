"""Service layer handling document storage, persistence, and retrieval business logic."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.pinecone_client import delete_vectors_by_document
from app_logging.logger import get_logger
from config.constants import DOCUMENT_STATUS_DELETED, DOCUMENT_STATUS_PROCESSING, DOCUMENT_TYPES
from database.connection import get_engine
from database.repositories.document_repository import DocumentRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import NotFoundException, ValidationException
from helpers.file_storage import save_uploaded_file
from helpers.response_helper import success_response
from models.lab_result_model import LabResult
from models.medical_timeline_model import MedicalTimeline
from models.medication_model import Medication
from models.prescription_model import Prescription
from schemas.response.base_response import BaseResponse
from schemas.response.document_response import DocumentListResponse, DocumentResponse

logger = get_logger(__name__)


class DocumentService:
    """Business logic for uploading, fetching, and listing patient documents."""

    def upload_document(
        self,
        patient_id: UUID | str,
        file: UploadFile,
        document_type: str,
        request_id: str = "",
    ) -> DocumentResponse:
        """Validate, store to disk, record database entry, and return document metadata."""
        logger.info("Document upload initiated", patient_id=str(patient_id), document_type=document_type, request_id=request_id)
        if document_type not in DOCUMENT_TYPES:
            logger.warning(
                "Document upload failed: invalid document_type",
                patient_id=str(patient_id),
                document_type=document_type,
                request_id=request_id,
            )
            raise ValidationException(
                f"Invalid document_type '{document_type}'. Allowed: {', '.join(DOCUMENT_TYPES)}"
            )

        raw_file_uri = save_uploaded_file(patient_id=patient_id, file=file)

        session: Session = SessionLocal(bind=get_engine())
        try:
            repo = DocumentRepository(session=session, request_id=request_id)
            doc = repo.create(
                patient_id=patient_id,
                document_type=document_type,
                raw_file_uri=raw_file_uri,
                status=DOCUMENT_STATUS_PROCESSING,
            )
            payload = success_response(data=doc, request_id=request_id)
            logger.info(
                "Document upload completed successfully",
                patient_id=str(patient_id),
                document_id=str(doc.document_id),
                document_type=document_type,
                request_id=request_id,
            )
            return DocumentResponse.model_validate(payload)
        finally:
            session.close()

    def get_document(
        self,
        patient_id: UUID | str,
        document_id: UUID | str,
        request_id: str = "",
    ) -> DocumentResponse:
        """Fetch a single document strictly ensuring ownership by the requesting patient."""
        logger.info("Document access requested", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)
        session: Session = SessionLocal(bind=get_engine())
        try:
            repo = DocumentRepository(session=session, request_id=request_id)
            doc = repo.get_by_id(document_id=document_id, patient_id=patient_id)
            if doc is None:
                logger.warning(
                    "Document lookup failed or ownership mismatch",
                    patient_id=str(patient_id),
                    document_id=str(document_id),
                    request_id=request_id,
                )
                raise NotFoundException("Document not found")

            payload = success_response(data=doc, request_id=request_id)
            logger.info(
                "Document retrieved successfully",
                patient_id=str(patient_id),
                document_id=str(doc.document_id),
                request_id=request_id,
            )
            return DocumentResponse.model_validate(payload)
        finally:
            session.close()

    def list_documents(
        self,
        patient_id: UUID | str,
        limit: int = 20,
        offset: int = 0,
        request_id: str = "",
    ) -> DocumentListResponse:
        """List paginated documents belonging to the requesting patient."""
        logger.info("Listing patient documents", patient_id=str(patient_id), limit=limit, offset=offset, request_id=request_id)
        session: Session = SessionLocal(bind=get_engine())
        try:
            repo = DocumentRepository(session=session, request_id=request_id)
            docs = repo.list_by_patient(patient_id=patient_id, limit=limit, offset=offset)
            payload = success_response(data=docs, request_id=request_id)
            logger.info(
                "Patient documents listed successfully",
                patient_id=str(patient_id),
                count=len(docs),
                request_id=request_id,
            )
            return DocumentListResponse.model_validate(payload)
        finally:
            session.close()

    def delete_document(
        self,
        patient_id: UUID | str,
        document_id: UUID | str,
        request_id: str = "",
    ) -> BaseResponse[Any]:
        """Soft-delete a document and cascade delete its derived database rows and Pinecone vectors."""
        logger.info("Document cascade deletion initiated", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)
        session: Session = SessionLocal(bind=get_engine())
        try:
            repo = DocumentRepository(session=session, request_id=request_id)
            doc = repo.get_by_id(document_id=document_id, patient_id=patient_id)
            if not doc:
                raise NotFoundException("Document not found or access denied")

            prescriptions = session.scalars(
                select(Prescription).filter_by(document_id=doc.document_id, patient_id=doc.patient_id)
            ).all()
            presc_ids = [p.prescription_id for p in prescriptions]

            meds_deleted_count = 0
            if presc_ids:
                meds = session.scalars(
                    select(Medication).filter(Medication.prescription_id.in_(presc_ids))
                ).all()
                meds_deleted_count = len(meds)
                for med in meds:
                    session.delete(med)

            presc_deleted_count = len(prescriptions)
            for presc in prescriptions:
                session.delete(presc)

            labs = session.scalars(
                select(LabResult).filter_by(document_id=doc.document_id, patient_id=doc.patient_id)
            ).all()
            labs_deleted_count = len(labs)
            for lab in labs:
                session.delete(lab)

            ref_ids = [pid for pid in presc_ids] + [doc.document_id]
            timeline_events = session.scalars(
                select(MedicalTimeline).filter(
                    MedicalTimeline.patient_id == doc.patient_id,
                    MedicalTimeline.reference_id.in_(ref_ids)
                )
            ).all()
            timeline_deleted_count = len(timeline_events)
            for event in timeline_events:
                session.delete(event)

            doc.status = DOCUMENT_STATUS_DELETED
            session.add(doc)
            session.commit()

            logger.info(
                "Document cascade deletion DB transaction committed",
                patient_id=str(patient_id),
                document_id=str(document_id),
                prescriptions_deleted=presc_deleted_count,
                medications_deleted=meds_deleted_count,
                lab_results_deleted=labs_deleted_count,
                timeline_events_deleted=timeline_deleted_count,
                request_id=request_id,
            )
        except Exception as exc:
            session.rollback()
            raise
        finally:
            session.close()

        try:
            delete_vectors_by_document(document_id=str(document_id), patient_id=str(patient_id))
        except Exception as exc:
            logger.error("Failed to delete vectors from Pinecone after document cascade delete", error=str(exc))

        payload = success_response(message="Document and derived records deleted successfully", request_id=request_id)
        return BaseResponse[Any].model_validate(payload)
