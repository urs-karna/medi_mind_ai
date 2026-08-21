"""Records read endpoints response schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.response.base_response import BaseResponse


class MedicationSummary(BaseModel):
    """Summary representation of a prescribed medication."""

    model_config = ConfigDict(from_attributes=True)

    medication_id: Annotated[UUID, Field(description="Unique medication ID")]
    drug_name_normalized: Annotated[str | None, Field(default=None, description="Normalized drug name")]
    dosage: Annotated[str | None, Field(default=None, description="Dosage instructions")]
    frequency: Annotated[str | None, Field(default=None, description="Dosing frequency")]
    duration: Annotated[str | None, Field(default=None, description="Treatment duration")]
    instructions: Annotated[str | None, Field(default=None, description="Additional administration instructions")]
    status: Annotated[str | None, Field(default=None, description="Current medication status")]


class PrescriptionRecordResponse(BaseModel):
    """Structured prescription record response payload."""

    model_config = ConfigDict(from_attributes=True)

    prescription_id: Annotated[UUID, Field(description="Unique prescription ID")]
    prescribed_date: Annotated[date | None, Field(default=None, description="Date prescription was issued")]
    doctor_name: Annotated[str | None, Field(default=None, description="Name of prescribing doctor")]
    diagnosis: Annotated[list[str] | None, Field(default_factory=list, description="List of diagnoses")]
    medications: Annotated[list[MedicationSummary], Field(default_factory=list, description="List of prescribed medications")]
    document_id: Annotated[UUID | None, Field(default=None, description="Source document ID")]


class PrescriptionListResponse(BaseResponse[list[PrescriptionRecordResponse]]):
    """Standardized response envelope for a list of prescription records."""


class LabResultRecordResponse(BaseModel):
    """Structured laboratory test result response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[UUID, Field(description="Unique lab result ID")]
    test_name: Annotated[str | None, Field(default=None, description="Name of laboratory test")]
    value: Annotated[Decimal | None, Field(default=None, description="Measured test value")]
    unit: Annotated[str | None, Field(default=None, description="Unit of measurement")]
    reference_range: Annotated[str | None, Field(default=None, description="Standard reference range")]
    flag: Annotated[str | None, Field(default=None, description="Abnormality flag (e.g., Normal, High, Low)")]
    test_date: Annotated[date | None, Field(default=None, description="Date test was performed")]
    document_id: Annotated[UUID | None, Field(default=None, description="Source document ID")]


class LabResultListResponse(BaseResponse[list[LabResultRecordResponse]]):
    """Standardized response envelope for a list of laboratory test results."""
