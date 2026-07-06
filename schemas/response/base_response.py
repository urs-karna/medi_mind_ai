"""Reusable API response schema for MediMind AI."""

from __future__ import annotations

from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    model_config = ConfigDict(from_attributes=True)

    success: Annotated[bool, Field(description="Indicates whether the operation succeeded")]
    message: Annotated[str, Field(description="Human-readable response message")]
    data: Annotated[T | None, Field(default=None, description="Payload returned by the endpoint")]
    request_id: Annotated[str, Field(default="", description="Request identifier for tracing")]
