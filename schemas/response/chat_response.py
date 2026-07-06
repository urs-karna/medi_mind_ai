"""Chat response schemas and envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.response.base_response import BaseResponse


class CitationSchema(BaseModel):
    """Represents a source document chunk cited in an assistant response."""

    model_config = ConfigDict(from_attributes=True)

    document_id: Annotated[UUID | str | None, Field(default=None, description="Source document ID")]
    chunk_type: Annotated[str | None, Field(default=None, description="Type of chunk cited (medication, lab_result, etc.)")]
    score: Annotated[float | None, Field(default=None, description="Similarity score of the retrieved chunk")]


class ChatMessageResult(BaseModel):
    """Payload data returned after sending a chat message and receiving an LLM response."""

    model_config = ConfigDict(from_attributes=True)

    session_id: Annotated[UUID, Field(description="Chat session ID")]
    message_id: Annotated[UUID, Field(description="Assistant message ID")]
    answer: Annotated[str, Field(description="Grounded assistant text response")]
    citations: Annotated[list[CitationSchema], Field(default_factory=list, description="Citations supporting the answer")]
    created_at: Annotated[datetime | None, Field(default=None, description="Timestamp of response creation")]


class ChatMessageResponse(BaseResponse[ChatMessageResult]):
    """Standardized response envelope for a chat message result."""


class ChatSessionData(BaseModel):
    """Chat session metadata payload."""

    model_config = ConfigDict(from_attributes=True)

    session_id: Annotated[UUID, Field(description="Session ID")]
    patient_id: Annotated[UUID, Field(description="Patient ID")]
    title: Annotated[str | None, Field(default=None, description="Session title")]
    summary: Annotated[str | None, Field(default=None, description="Session summary")]
    is_active: Annotated[bool, Field(default=True, description="Whether session is active")]
    created_at: Annotated[datetime | None, Field(default=None, description="Session creation timestamp")]
    updated_at: Annotated[datetime | None, Field(default=None, description="Session last updated timestamp")]


class ChatSessionResponse(BaseResponse[ChatSessionData]):
    """Standardized response envelope for a single chat session."""


class ChatSessionListResponse(BaseResponse[list[ChatSessionData]]):
    """Standardized response envelope for paginated chat session lists."""


class ChatMessageItem(BaseModel):
    """Individual message item within a chat session history."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    message_id: Annotated[UUID, Field(description="Message ID")]
    session_id: Annotated[UUID, Field(description="Session ID")]
    role: Annotated[str, Field(description="Role of sender (user, assistant, system)")]
    content: Annotated[str, Field(description="Message text content")]
    citations: Annotated[list[CitationSchema] | None, Field(default=None, description="Citations supporting the message")]
    metadata: Annotated[
        dict[str, Any] | None,
        Field(default=None, validation_alias="message_metadata", serialization_alias="metadata", description="Message metadata"),
    ]
    created_at: Annotated[datetime | None, Field(default=None, description="Creation timestamp")]


class ChatHistoryResponse(BaseResponse[list[ChatMessageItem]]):
    """Standardized response envelope for session chat history."""
