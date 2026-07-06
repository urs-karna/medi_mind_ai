"""Custom application exceptions for MediMind AI."""

from __future__ import annotations

from typing import Any

from core.errors.error_models import (
    ErrorModel,
    StatusBadRequest,
    StatusInternalServerError,
    StatusNotFound,
    StatusUnauthorized,
)


class BaseAppException(Exception):
    """Base class for application-specific exceptions."""

    def __init__(self, error: ErrorModel) -> None:
        super().__init__(error.message)
        self.error = error
        self.message = error.message
        self.status_code = error.status_code
        self.error_code = error.error_code
        self.details = error.details


class ValidationException(BaseAppException):
    """Raised when business validation fails."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusBadRequest(message=message, details=details or {}))


class AuthenticationException(BaseAppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusUnauthorized(message=message, details=details or {}))


class DatabaseException(BaseAppException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusInternalServerError(message=message, details=details or {}))


class NotFoundException(BaseAppException):
    """Raised when a requested resource does not exist or is inaccessible."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusNotFound(message=message, details=details or {}))


class DocumentProcessingException(BaseAppException):
    """Raised when document file storage or processing fails."""

    def __init__(self, message: str = "Document processing failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusInternalServerError(message=message, details=details or {}))


class AIExtractionException(BaseAppException):
    """Raised when AI vision classification or structured extraction fails."""

    def __init__(self, message: str = "AI extraction failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusInternalServerError(message=message, details=details or {}))


class RAGIngestionException(BaseAppException):
    """Raised when RAG embedding, chunking, or Pinecone vector database operations fail."""

    def __init__(self, message: str = "RAG ingestion failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusInternalServerError(message=message, details=details or {}))


class ChatGenerationException(BaseAppException):
    """Raised when chat LLM response generation fails."""

    def __init__(self, message: str = "Chat generation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(StatusInternalServerError(message=message, details=details or {}))

