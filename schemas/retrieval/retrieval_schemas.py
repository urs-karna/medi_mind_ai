"""Pydantic schemas for RAG vector retrieval results."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetrievedChunk(BaseModel):
    """Represents a scored vector match returned from Pinecone retrieval."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(description="Unique identifier of the matching vector chunk")
    text: str = Field(description="Exact sentence text embedded for this chunk")
    score: float = Field(description="Cosine similarity score of the match")
    chunk_type: str = Field(description="Entity type such as medication or lab_result")
    document_id: str = Field(description="UUID of the source document")
    reference_id: str = Field(description="UUID of the source database record")
    event_date: date | None = Field(default=None, description="Date associated with the medical event")

    @field_validator("event_date", mode="before")
    @classmethod
    def _parse_event_date(cls, val: Any) -> date | None:
        """Parse string or date objects into date or None if empty."""
        if val is None or val == "":
            return None
        if isinstance(val, date):
            return val
        try:
            return datetime.strptime(str(val), "%Y-%m-%d").date()
        except Exception:
            return None


class RetrievalResponse(BaseModel):
    """API response payload containing retrieved medical context chunks."""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(description="The plain-English question searched")
    results: list[RetrievedChunk] = Field(description="List of matching retrieved chunks sorted by score descending")
    result_count: int = Field(description="Total number of retrieved chunks returned")
