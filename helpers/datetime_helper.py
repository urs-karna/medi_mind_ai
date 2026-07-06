"""Datetime helper utilities for MediMind AI."""

from __future__ import annotations

from datetime import datetime, timezone

from app_logging.logger import get_logger

logger = get_logger(__name__)


def get_current_utc_time() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    current_time = datetime.now(timezone.utc)
    logger.debug("Current UTC time generated")
    return current_time


def get_timestamp() -> str:
    """Return the current UTC timestamp as an ISO 8601 string."""
    timestamp = get_current_utc_time().isoformat()
    logger.debug("UTC timestamp generated")
    return timestamp
