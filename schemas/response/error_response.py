"""Error response schema."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

from schemas.response.base_response import BaseResponse


class ErrorDetails(BaseModel):
    """Optional error payload details."""

    details: Annotated[dict[str, Any], Field(default_factory=dict)]


class ErrorResponse(BaseResponse[Any]):
    """Standardized error response envelope."""

    error_code: Annotated[str | None, Field(default=None, description="Machine-readable error code")]
    status_code: Annotated[int | None, Field(default=None, description="HTTP status code")]
