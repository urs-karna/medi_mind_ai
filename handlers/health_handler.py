"""Health request orchestration handler."""

from __future__ import annotations

from core.health.health_service import HealthService
from config.constants import HEALTH_ENDPOINT_MESSAGE
from helpers.response_helper import success_response
from app_logging.logger import get_logger
from schemas.response.health_response import HealthResponse

logger = get_logger(__name__)


class HealthHandler:
    """Orchestrate health service output into response models."""

    def __init__(self, service: HealthService | None = None) -> None:
        self._service = service or HealthService()

    def get_health_response(self, request_id: str = "") -> HealthResponse:
        """Return a validated health response model."""
        logger.info("Health response requested")
        data = self._service.get_health_data()
        payload = success_response(
            message=HEALTH_ENDPOINT_MESSAGE,
            data=data,
            request_id=request_id,
        )
        return HealthResponse.model_validate(payload)
