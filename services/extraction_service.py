"""Service layer handling AI multimodal vision classification and medical extraction."""

from __future__ import annotations

import time
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from agents.langchain_client import classify_document, extract_document_data
from app_logging.logger import get_logger
from config.constants import (
    DOCUMENT_STATUS_NEEDS_REVIEW,
    DOCUMENT_STATUS_READY,
    EXTRACTION_CONFIDENCE_THRESHOLD,
)
from database.connection import get_engine
from database.repositories.document_repository import DocumentRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import AIExtractionException, NotFoundException
from helpers.file_storage import get_mime_type, read_file
from helpers.response_helper import success_response
from schemas.response.document_response import ExtractionStatusResponse

logger = get_logger(__name__)


class ExtractionService:
    """Orchestrate multimodal document OCR, classification, and structured extraction."""

    def process_document(
        self,
        document_id: UUID | str,
        patient_id: UUID | str,
        request_id: str = "",
    ) -> ExtractionStatusResponse:
        """Process an uploaded document via LangChain structured vision output and save extraction."""
        logger.info("Starting AI extraction pipeline", document_id=str(document_id), patient_id=str(patient_id), request_id=request_id)

        session: Session = SessionLocal(bind=get_engine())
        try:
            repo = DocumentRepository(session=session, request_id=request_id)
            doc = repo.get_by_id(document_id=document_id, patient_id=patient_id)
            if doc is None:
                logger.warning("Extraction aborted: document not found or ownership mismatch", document_id=str(document_id), patient_id=str(patient_id))
                raise NotFoundException("Document not found")

            if not doc.raw_file_uri:
                raise AIExtractionException("Document has no stored file URI")

            # Stage 1: Read file bytes
            stage_start = time.perf_counter()
            image_bytes = read_file(doc.raw_file_uri)
            mime_type = get_mime_type(doc.raw_file_uri)
            logger.info(
                "Read document file for extraction",
                document_id=str(document_id),
                stage="read_file",
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
            )

            # Stage 2: Classify document type
            stage_start = time.perf_counter()
            class_res = classify_document(
                image_bytes=image_bytes,
                mime_type=mime_type,
                document_id=str(document_id),
                request_id=request_id,
            )
            classified_type = class_res.document_type
            confidence_val = float(class_res.confidence)

            logger.info(
                "Document classification complete",
                document_id=str(document_id),
                stage="classification",
                classified_type=classified_type,
                confidence=confidence_val,
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
            )

            # Stage 3: Extract structured medical data
            stage_start = time.perf_counter()
            extract_res = extract_document_data(
                image_bytes=image_bytes,
                mime_type=mime_type,
                document_type=classified_type,
                document_id=str(document_id),
                request_id=request_id,
            )
            extracted_json = extract_res.model_dump(mode="json")
            logger.info(
                "Structured medical extraction complete",
                document_id=str(document_id),
                stage="extraction",
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
            )

            # Stage 4: Update document record
            doc.document_type = classified_type
            doc.extraction_json = extracted_json
            doc.ocr_confidence = Decimal(str(confidence_val))
            doc.status = DOCUMENT_STATUS_READY if confidence_val >= EXTRACTION_CONFIDENCE_THRESHOLD else DOCUMENT_STATUS_NEEDS_REVIEW
            repo.update(doc)

            logger.info(
                "Document processing pipeline finished",
                document_id=str(document_id),
                final_status=doc.status,
                ocr_confidence=confidence_val,
                request_id=request_id,
            )
            payload = success_response(data=doc, request_id=request_id)
            return ExtractionStatusResponse.model_validate(payload)
        finally:
            session.close()
