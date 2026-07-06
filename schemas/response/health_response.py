"""Health response schema."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from schemas.response.base_response import BaseResponse


class HealthData(BaseModel):
    """Health check payload."""

    environment: Annotated[str, Field(description="Current application environment")]
    version: Annotated[str, Field(description="Application version")]
    timestamp: Annotated[str, Field(description="Current UTC timestamp")]


class HealthResponse(BaseResponse[HealthData]):
    """Standardized health endpoint response."""
