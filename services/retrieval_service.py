"""Service layer for RAG vector retrieval against Pinecone."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from agents import embedding_client, pinecone_client
from app_logging.logger import get_logger
from exceptions.custom_exceptions import RAGIngestionException
from schemas.retrieval.retrieval_schemas import RetrievedChunk

logger = get_logger(__name__)


class RetrievalService:
    """Provides semantic search retrieval over patient medical chunks."""

    def retrieve_relevant_chunks(self, question: str, patient_id: UUID | str, top_k: int = 5) -> list[RetrievedChunk]:
        """Embed a question and query Pinecone for top matching chunks scoped by patient_id."""
        if not patient_id:
            raise RAGIngestionException("patient_id is strictly required for retrieval")
        if not question or not question.strip():
            return []

        start_time = time.perf_counter()
        try:
            embedding = embedding_client.embed_text(question.strip())
            matches = pinecone_client.query_vectors(
                embedding=embedding,
                patient_id=str(patient_id),
                top_k=top_k,
            )

            chunks: list[RetrievedChunk] = []
            for match in matches:
                metadata: dict[str, Any] = match.get("metadata") or {}
                chunk = RetrievedChunk(
                    chunk_id=str(match.get("id", "")),
                    text=str(metadata.get("text", "")),
                    score=float(match.get("score", 0.0)),
                    chunk_type=str(metadata.get("chunk_type", "")),
                    document_id=str(metadata.get("document_id", "")),
                    reference_id=str(metadata.get("reference_id", "")),
                    event_date=metadata.get("event_date"),
                )
                chunks.append(chunk)

            sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Retrieved relevant chunks",
                patient_id=str(patient_id),
                top_k=top_k,
                result_count=len(sorted_chunks),
                latency_ms=latency_ms,
            )
            return sorted_chunks
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "Failed to retrieve relevant chunks",
                patient_id=str(patient_id),
                top_k=top_k,
                latency_ms=latency_ms,
                error=str(exc),
            )
            raise RAGIngestionException(f"Retrieval failed: {exc}") from exc
