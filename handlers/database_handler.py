"""Database health orchestration handler."""

from __future__ import annotations

from app_logging.logger import get_logger
from config.constants import DEFAULT_SUCCESS_MESSAGE
from core.database.database_service import DatabaseService
from helpers.response_helper import success_response
from schemas.response.database_health_response import DatabaseHealthResponse

logger = get_logger(__name__)


class DatabaseHandler:
    """Convert database service results into API response models."""

    def __init__(self, service: DatabaseService | None = None) -> None:
        self._service = service or DatabaseService()

    def get_health_response(self, request_id: str = "") -> DatabaseHealthResponse:
        """Return the database health response model."""
        logger.info("Database health requested", request_id=request_id)
        data = self._service.get_health_data(request_id=request_id)
        payload = success_response(message=DEFAULT_SUCCESS_MESSAGE, data=data, request_id=request_id)
        return DatabaseHealthResponse.model_validate(payload)
