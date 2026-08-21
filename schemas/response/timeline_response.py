"""Timeline read endpoints response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.response.base_response import BaseResponse


class TimelineEventResponse(BaseModel):
    """Structured medical timeline event response payload."""

    model_config = ConfigDict(from_attributes=True)

    event_id: Annotated[UUID, Field(description="Unique timeline event ID")]
    event_type: Annotated[str | None, Field(default=None, description="Type of event (e.g., doctor_visit, lab_test)")]
    event_date: Annotated[date | None, Field(default=None, description="Date event occurred")]
    summary: Annotated[str | None, Field(default=None, description="Summary description of event")]
    reference_id: Annotated[UUID | None, Field(default=None, description="Reference ID to linked entity")]
    created_at: Annotated[datetime | None, Field(default=None, description="Timestamp when event was recorded")]


class TimelineListResponse(BaseResponse[list[TimelineEventResponse]]):
    """Standardized response envelope for a list of timeline events."""
