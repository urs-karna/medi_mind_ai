"""Middleware for extracting and storing token context (user_id, patient_id)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Request

from app_logging.logger import get_logger

logger = get_logger(__name__)


def assign_token_context(
    request: Request,
    user_id: UUID | str | None,
    patient_id: UUID | str | None,
) -> None:
    """Store the authenticated user's identifiers on the request state.

    Call this after JWT validation to make the IDs available to all
    downstream handlers and dependencies for the current request.
    """
    request.state.user_id = str(user_id) if user_id else None
    request.state.patient_id = str(patient_id) if patient_id else None
    logger.debug(
        "Token context assigned",
        user_id=request.state.user_id,
        patient_id=request.state.patient_id,
    )


def get_token_context(request: Request) -> dict[str, Any]:
    """Return the authenticated identifiers from the request state.

    Returns a dict with ``user_id`` and ``patient_id`` (both may be ``None``
    if the request is unauthenticated).
    """
    return {
        "user_id": getattr(request.state, "user_id", None),
        "patient_id": getattr(request.state, "patient_id", None),
    }
