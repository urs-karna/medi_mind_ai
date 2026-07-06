"""Pinecone vector database client wrapper for RAG ingestion and retrieval."""

from __future__ import annotations

from typing import Any

from pinecone import Pinecone, ServerlessSpec

from app_logging.logger import get_logger
from config.constants import (
    EMBEDDING_DIMENSION,
    PINECONE_UPSERT_BATCH_SIZE,
)
from config.settings import get_settings
from exceptions.custom_exceptions import RAGIngestionException

logger = get_logger(__name__)

_index_handle: Any | None = None


def ensure_index_exists() -> None:
    """Check if Pinecone index exists and create it if missing at app startup."""
    settings = get_settings()
    if not settings.pinecone_api_key:
        logger.warning("PINECONE_API_KEY not configured; skipping index creation")
        return

    try:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        index_name = settings.pinecone_index_name
        existing = pc.list_indexes()
        existing_names = [idx["name"] if isinstance(idx, dict) else getattr(idx, "name", str(idx)) for idx in existing]

        if index_name not in existing_names:
            logger.info("Creating new Pinecone index", index_name=index_name, dimension=EMBEDDING_DIMENSION)
            pc.create_index(
                name=index_name,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info("Pinecone index created successfully", index_name=index_name)
        else:
            logger.info("Found existing Pinecone index", index_name=index_name)
    except Exception as exc:
        logger.error("Failed during ensure_index_exists", error=str(exc))
        raise RAGIngestionException(f"Pinecone index check/create failed: {exc}") from exc


def get_pinecone_index() -> Any:
    """Return handle to existing Pinecone index without checking existence."""
    global _index_handle
    if _index_handle is not None:
        return _index_handle

    settings = get_settings()
    if not settings.pinecone_api_key:
        raise RAGIngestionException("PINECONE_API_KEY is not configured in settings")

    try:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        _index_handle = pc.Index(settings.pinecone_index_name)
        return _index_handle
    except Exception as exc:
        logger.error("Failed to get Pinecone index handle", error=str(exc))
        raise RAGIngestionException(f"Failed to get Pinecone index: {exc}") from exc


def upsert_vectors(vectors: list[dict[str, Any]]) -> None:
    """Upsert vector dictionaries into Pinecone in batches."""
    if not vectors:
        return

    index = get_pinecone_index()
    batch_size = PINECONE_UPSERT_BATCH_SIZE
    total_vectors = len(vectors)
    batch_count = 0

    try:
        for i in range(0, total_vectors, batch_size):
            batch = vectors[i : i + batch_size]
            index.upsert(vectors=batch)
            batch_count += 1
        logger.info(
            "Upserted vectors to Pinecone",
            total_vectors=total_vectors,
            batch_count=batch_count,
        )
    except Exception as exc:
        logger.error("Failed to upsert vectors to Pinecone", error=str(exc), total_vectors=total_vectors)
        raise RAGIngestionException(f"Vector upsert failed: {exc}") from exc


def delete_vectors_by_document(document_id: str, patient_id: str) -> None:
    """Delete all vectors for a document and patient to ensure re-ingestion idempotency."""
    if not patient_id:
        raise RAGIngestionException("patient_id is strictly required for deleting vectors")
    if not document_id:
        return

    index = get_pinecone_index()
    target_filter = {"document_id": str(document_id), "patient_id": str(patient_id)}

    try:
        index.delete(filter=target_filter)
        logger.info(
            "Deleted vectors via metadata filter",
            document_id=str(document_id),
            patient_id=str(patient_id),
            path="metadata_filter",
        )
    except Exception as exc:
        logger.info(
            "Metadata filter delete unsupported or failed, falling back to query-and-delete",
            document_id=str(document_id),
            patient_id=str(patient_id),
            error=str(exc),
            path="query_fallback",
        )
        try:
            # Fallback: query matching IDs using a zero vector
            zero_vector = [0.0] * EMBEDDING_DIMENSION
            query_res = index.query(
                vector=zero_vector,
                top_k=1000,
                filter=target_filter,
                include_metadata=False,
            )
            matches = getattr(query_res, "matches", []) or query_res.get("matches", [])
            ids_to_delete = [
                m["id"] if isinstance(m, dict) else getattr(m, "id", str(m)) for m in matches
            ]
            if ids_to_delete:
                index.delete(ids=ids_to_delete)
            logger.info(
                "Deleted vectors via query-and-delete fallback",
                document_id=str(document_id),
                patient_id=str(patient_id),
                removed_count=len(ids_to_delete),
                path="query_fallback",
            )
        except Exception as fallback_exc:
            logger.error(
                "Failed to delete vectors during query fallback",
                document_id=str(document_id),
                patient_id=str(patient_id),
                error=str(fallback_exc),
            )
            raise RAGIngestionException(f"Vector deletion failed: {fallback_exc}") from fallback_exc


def delete_vector_by_id(chunk_id: str) -> None:
    """Delete a single vector from Pinecone by its chunk ID."""
    if not chunk_id:
        return

    index = get_pinecone_index()
    try:
        index.delete(ids=[str(chunk_id)])
        logger.info("Deleted single vector from Pinecone", chunk_id=str(chunk_id))
    except Exception as exc:
        logger.error("Failed to delete single vector from Pinecone", chunk_id=str(chunk_id), error=str(exc))
        raise RAGIngestionException(f"Single vector deletion failed: {exc}") from exc


def query_vectors(
    embedding: list[float],
    patient_id: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query Pinecone for similar vectors strictly scoped by patient_id filter."""
    if not patient_id:
        raise RAGIngestionException("patient_id is strictly required for vector queries")

    index = get_pinecone_index()
    query_filter = dict(filters or {})
    query_filter["patient_id"] = str(patient_id)

    try:
        res = index.query(
            vector=embedding,
            top_k=top_k,
            filter=query_filter,
            include_metadata=True,
        )
        matches = getattr(res, "matches", []) or res.get("matches", [])
        results: list[dict[str, Any]] = []
        for match in matches:
            if isinstance(match, dict):
                results.append(match)
            else:
                results.append({
                    "id": getattr(match, "id", ""),
                    "score": getattr(match, "score", 0.0),
                    "metadata": getattr(match, "metadata", {}),
                })
        return results
    except Exception as exc:
        logger.error("Failed to query vectors from Pinecone", patient_id=str(patient_id), error=str(exc))
        raise RAGIngestionException(f"Vector query failed: {exc}") from exc
