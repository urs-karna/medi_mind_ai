"""Retrieval search request schema."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievalSearchRequest(BaseModel):
    """Schema for validating RAG retrieval search request body."""

    model_config = ConfigDict(from_attributes=True)

    question: str = Field(description="The plain-English medical question to search for")
    top_k: int | None = Field(default=5, ge=1, le=50, description="Number of top matching chunks to return")
