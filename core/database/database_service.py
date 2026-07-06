"""Database health service for MediMind AI."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import text

from app_logging.logger import get_logger
from config.constants import DEFAULT_DATABASE_ERROR_MESSAGE
from database.connection import get_engine
from exceptions.custom_exceptions import DatabaseException
from helpers.datetime_helper import get_timestamp

logger = get_logger(__name__)


class DatabaseService:
    """Perform a minimal database round-trip to prove connectivity."""

    def get_health_data(self, request_id: str = "") -> dict[str, Any]:
        """Execute SELECT 1 and return timing information."""
        start_time = time.perf_counter()
        try:
            with get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))

            response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            payload = {
                "status": "healthy",
                "database": "connected",
                "timestamp": get_timestamp(),
                "response_time_ms": response_time_ms,
            }
            logger.info(
                "Database health check completed",
                operation="database_health",
                request_id=request_id,
                response_time_ms=response_time_ms,
            )
            return payload
        except Exception as exc:
            logger.error(
                "Database health check failed",
                operation="database_health",
                request_id=request_id,
                error=str(exc),
            )
            raise DatabaseException(message=DEFAULT_DATABASE_ERROR_MESSAGE)
