"""Database health router for MediMind AI."""

from __future__ import annotations

from fastapi import APIRouter, Request

from handlers.database_handler import DatabaseHandler
from schemas.response.database_health_response import DatabaseHealthResponse

router = APIRouter(tags=["Database"])
database_handler = DatabaseHandler()


@router.get("/database/health", response_model=DatabaseHealthResponse)
async def database_health(request: Request) -> DatabaseHealthResponse:
    """Return database connectivity information."""
    request_id = getattr(request.state, "request_id", "")
    return database_handler.get_health_response(request_id=request_id)
