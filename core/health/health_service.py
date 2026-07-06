"""Health domain business logic."""

from __future__ import annotations

from typing import Any

from config.settings import get_settings
from helpers.datetime_helper import get_timestamp
from app_logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class HealthService:
    """Return platform health state using only pure business data."""

    def get_health_data(self) -> dict[str, Any]:
        """Build the health payload for the API."""
        payload = {
            "environment": settings.environment,
            "version": settings.app_version,
            "timestamp": get_timestamp(),
        }
        logger.info("Health payload generated")
        return payload
