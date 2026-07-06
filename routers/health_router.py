"""Health check router for MediMind AI."""

from __future__ import annotations

from fastapi import APIRouter, Request

from handlers.health_handler import HealthHandler
from app_logging.logger import get_logger
from schemas.response.health_response import HealthResponse

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)
health_handler = HealthHandler()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Return API health information."""
    request_id = getattr(request.state, "request_id", "")
    logger.info("Health check requested")
    return health_handler.get_health_response(request_id=request_id)
