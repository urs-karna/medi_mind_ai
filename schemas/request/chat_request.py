"""Chat request schemas."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Schema for sending a question in a chat session."""

    model_config = ConfigDict(from_attributes=True)

    session_id: Annotated[UUID | None, Field(default=None, description="Optional chat session ID; None creates a new session")]
    question: Annotated[str, Field(min_length=1, description="Patient medical question")]
