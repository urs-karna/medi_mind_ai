"""Google Gemini embedding client wrapper for RAG ingestion."""

from __future__ import annotations

import time
from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app_logging.logger import get_logger
from config.constants import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
)
from config.settings import get_settings
from exceptions.custom_exceptions import RAGIngestionException

logger = get_logger(__name__)

_embedding_model_instance: GoogleGenerativeAIEmbeddings | None = None


def _get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """Return cached GoogleGenerativeAIEmbeddings instance."""
    global _embedding_model_instance
    if _embedding_model_instance is not None:
        return _embedding_model_instance

    settings = get_settings()
    if not settings.google_api_key:
        raise RAGIngestionException("GOOGLE_API_KEY is not configured in settings")

    try:
        _embedding_model_instance = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=settings.google_api_key,
            output_dimensionality=EMBEDDING_DIMENSION,
        )
        return _embedding_model_instance
    except Exception as exc:
        logger.error("Failed to initialize GoogleGenerativeAIEmbeddings", error=str(exc))
        raise RAGIngestionException(f"Embedding model initialization failed: {exc}") from exc


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    if not text:
        return []

    start_time = time.perf_counter()
    try:
        model = _get_embedding_model()
        vector = model.embed_query(text)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info("Generated single text embedding", latency_ms=latency_ms)
        return vector
    except Exception as exc:
        logger.error("Failed to generate single text embedding", error=str(exc))
        raise RAGIngestionException(f"Embedding generation failed: {exc}") from exc


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for multiple text strings in batches."""
    if not texts:
        return []

    start_time = time.perf_counter()
    model = _get_embedding_model()
    batch_size = EMBEDDING_BATCH_SIZE
    total_texts = len(texts)
    batch_count = 0
    all_embeddings: list[list[float]] = []

    try:
        for i in range(0, total_texts, batch_size):
            batch = texts[i : i + batch_size]
            batch_vectors = model.embed_documents(batch)
            all_embeddings.extend(batch_vectors)
            batch_count += 1

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Generated batch embeddings",
            total_texts=total_texts,
            batch_count=batch_count,
            latency_ms=latency_ms,
        )
        return all_embeddings
    except Exception as exc:
        logger.error("Failed to generate batch embeddings", error=str(exc), total_texts=total_texts)
        raise RAGIngestionException(f"Batch embedding generation failed: {exc}") from exc
