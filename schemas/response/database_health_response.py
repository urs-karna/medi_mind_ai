"""Database health response schema."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from schemas.response.base_response import BaseResponse


class DatabaseHealthData(BaseModel):
    """Database connectivity payload."""

    status: Annotated[str, Field(description="Database health status")]
    database: Annotated[str, Field(description="Database name or connection label")]
    timestamp: Annotated[str, Field(description="Current UTC timestamp")]
    response_time_ms: Annotated[float, Field(description="Round-trip database latency in milliseconds")]


class DatabaseHealthResponse(BaseResponse[DatabaseHealthData]):
    """Standard response envelope for the database health endpoint."""
