"""Orchestration handler for document endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import UploadFile

from app_logging.logger import get_logger
from config.constants import DOCUMENT_STATUS_READY
from schemas.response.base_response import BaseResponse
from schemas.response.document_response import DocumentListResponse, DocumentResponse, ExtractionStatusResponse
from services.document_service import DocumentService
from services.extraction_persistence_service import ExtractionPersistenceService
from services.extraction_service import ExtractionService
from services.rag_ingestion_service import RAGIngestionService

logger = get_logger(__name__)


class DocumentHandler:
    """Orchestrate calls to DocumentService and return API response models."""

    def __init__(
        self,
        service: DocumentService | None = None,
        extraction_service: ExtractionService | None = None,
        persistence_service: ExtractionPersistenceService | None = None,
        rag_ingestion_service: RAGIngestionService | None = None,
    ) -> None:
        self._service = service or DocumentService()
        self._extraction_service = extraction_service or ExtractionService()
        self._persistence_service = persistence_service or ExtractionPersistenceService()
        self._rag_ingestion_service = rag_ingestion_service or RAGIngestionService()

    def upload_document(
        self,
        patient_id: UUID | str,
        file: UploadFile,
        document_type: str,
        request_id: str = "",
    ) -> DocumentResponse:
        """Handle document upload orchestration."""
        logger.info("Handling document upload", patient_id=str(patient_id), request_id=request_id)
        return self._service.upload_document(
            patient_id=patient_id,
            file=file,
            document_type=document_type,
            request_id=request_id,
        )

    def get_document(
        self,
        patient_id: UUID | str,
        document_id: UUID | str,
        request_id: str = "",
    ) -> DocumentResponse:
        """Handle single document retrieval orchestration."""
        logger.info("Handling document get", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)
        return self._service.get_document(
            patient_id=patient_id,
            document_id=document_id,
            request_id=request_id,
        )

    def list_documents(
        self,
        patient_id: UUID | str,
        limit: int = 20,
        offset: int = 0,
        request_id: str = "",
    ) -> DocumentListResponse:
        """Handle document listing orchestration."""
        logger.info("Handling document list", patient_id=str(patient_id), request_id=request_id)
        return self._service.list_documents(
            patient_id=patient_id,
            limit=limit,
            offset=offset,
            request_id=request_id,
        )

    def process_document(
        self,
        patient_id: UUID | str,
        document_id: UUID | str,
        request_id: str = "",
    ) -> ExtractionStatusResponse:
        """Handle AI OCR, structured extraction, clinical table persistence, and RAG vector ingestion."""
        logger.info("Handling document processing", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)
        res = self._extraction_service.process_document(
            document_id=document_id,
            patient_id=patient_id,
            request_id=request_id,
        )
        if res.data and res.data.status == DOCUMENT_STATUS_READY:
            counts = self._persistence_service.persist_extraction(
                document_id=document_id,
                patient_id=patient_id,
                request_id=request_id,
            )
            res.data.prescriptions_created = counts.get("prescriptions_created", 0)
            res.data.medications_created = counts.get("medications_created", 0)
            res.data.lab_results_created = counts.get("lab_results_created", 0)
            res.data.timeline_events_created = counts.get("timeline_events_created", 0)

            rag_res = self._rag_ingestion_service.ingest_document(
                document_id=document_id,
                patient_id=patient_id,
                request_id=request_id,
            )
            res.data.chunks_created = rag_res.get("chunks_created", 0)
        return res

    def delete_document(
        self,
        patient_id: UUID | str,
        document_id: UUID | str,
        request_id: str = "",
    ) -> BaseResponse[Any]:
        """Handle document cascade deletion orchestration."""
        logger.info("Handling document delete", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)
        return self._service.delete_document(
            patient_id=patient_id,
            document_id=document_id,
            request_id=request_id,
        )
