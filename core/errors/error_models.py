"""Reusable error models for MediMind AI."""

from __future__ import annotations

from typing import Any, Annotated

from pydantic import BaseModel, Field


class ErrorModel(BaseModel):
    """Base error payload model."""

    message: Annotated[str, Field(min_length=1)]
    status_code: Annotated[int, Field(ge=400, le=599)]
    error_code: Annotated[str, Field(min_length=1)]
    details: Annotated[dict[str, Any], Field(default_factory=dict)]


class StatusBadRequest(ErrorModel):
    """400-series validation and request errors."""

    status_code: int = 400
    error_code: str = "BAD_REQUEST"


class StatusUnauthorized(ErrorModel):
    """401 authorization errors."""

    status_code: int = 401
    error_code: str = "UNAUTHORIZED"


class StatusInternalServerError(ErrorModel):
    """500-class unexpected application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"


class StatusServiceUnavailable(ErrorModel):
    """503 downstream availability errors."""

    status_code: int = 503
    error_code: str = "SERVICE_UNAVAILABLE"


class StatusNotFound(ErrorModel):
    """404 resource not found errors."""

    status_code: int = 404
    error_code: str = "NOT_FOUND"
