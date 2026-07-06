"""Orchestration handler for RAG vector retrieval endpoints."""

from __future__ import annotations

from uuid import UUID

from app_logging.logger import get_logger
from schemas.retrieval.retrieval_schemas import RetrievalResponse, RetrievedChunk
from services.retrieval_service import RetrievalService

logger = get_logger(__name__)


class RetrievalHandler:
    """Orchestrate calls to RetrievalService and return API response models."""

    def __init__(self, service: RetrievalService | None = None) -> None:
        self._service = service or RetrievalService()

    def search(
        self,
        question: str,
        patient_id: UUID | str,
        top_k: int = 5,
        request_id: str = "",
    ) -> RetrievalResponse:
        """Handle RAG retrieval search orchestration."""
        logger.info("Handling retrieval search", patient_id=str(patient_id), top_k=top_k, request_id=request_id)
        chunks: list[RetrievedChunk] = self._service.retrieve_relevant_chunks(
            question=question,
            patient_id=patient_id,
            top_k=top_k,
        )
        return RetrievalResponse(
            query=question,
            results=chunks,
            result_count=len(chunks),
        )
