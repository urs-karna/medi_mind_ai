"""Document upload request schema."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config.constants import DOCUMENT_TYPES
from exceptions.custom_exceptions import ValidationException


class DocumentUploadRequest(BaseModel):
    """Schema for validating document upload metadata."""

    model_config = ConfigDict(from_attributes=True)

    document_type: Annotated[
        str,
        Field(description="Type of medical document being uploaded"),
    ]

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        """Ensure document_type matches allowed medical document types."""
        if value not in DOCUMENT_TYPES:
            raise ValueError(f"Invalid document_type '{value}'. Allowed: {', '.join(DOCUMENT_TYPES)}")
        return value
