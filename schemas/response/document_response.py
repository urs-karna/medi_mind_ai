"""Document response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.response.base_response import BaseResponse


class DocumentData(BaseModel):
    """Document metadata returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    document_id: Annotated[UUID, Field(description="Unique document identifier")]
    document_type: Annotated[str | None, Field(default=None, description="Type of medical document")]
    status: Annotated[str | None, Field(default=None, description="Processing status")]
    ocr_confidence: Annotated[float | None, Field(default=None, description="AI classification confidence")]
    extraction_json: Annotated[Any | None, Field(default=None, description="Extracted structured medical JSON")]
    uploaded_at: Annotated[datetime | None, Field(default=None, description="Timestamp of document upload")]

    @field_validator("ocr_confidence", mode="before")
    @classmethod
    def cast_confidence_to_float(cls, val: Any) -> float | None:
        """Explicitly cast Decimal confidence score to float."""
        return float(val) if val is not None else None


class DocumentResponse(BaseResponse[DocumentData]):
    """Standardized response envelope for a single document."""


class DocumentListResponse(BaseResponse[list[DocumentData]]):
    """Standardized response envelope for paginated document lists."""


class ExtractionStatusData(BaseModel):
    """Extraction processing status and confidence data."""

    model_config = ConfigDict(from_attributes=True)

    document_id: Annotated[UUID, Field(description="Unique document identifier")]
    status: Annotated[str | None, Field(default=None, description="Processing status")]
    ocr_confidence: Annotated[float | None, Field(default=None, description="AI classification confidence")]
    document_type: Annotated[str | None, Field(default=None, description="Classified medical document type")]
    extraction_json: Annotated[Any | None, Field(default=None, description="Extracted structured medical JSON")]
    prescriptions_created: Annotated[int | None, Field(default=None, description="Number of prescriptions created")] = None
    medications_created: Annotated[int | None, Field(default=None, description="Number of medications created")] = None
    lab_results_created: Annotated[int | None, Field(default=None, description="Number of lab results created")] = None
    timeline_events_created: Annotated[int | None, Field(default=None, description="Number of timeline events created")] = None
    chunks_created: Annotated[int | None, Field(default=None, description="Number of vector chunks ingested into Pinecone")] = None

    @field_validator("ocr_confidence", mode="before")
    @classmethod
    def cast_confidence_to_float(cls, val: Any) -> float | None:
        """Explicitly cast Decimal confidence score to float."""
        return float(val) if val is not None else None


class ExtractionStatusResponse(BaseResponse[ExtractionStatusData]):
    """Standardized response envelope for AI extraction processing status."""
