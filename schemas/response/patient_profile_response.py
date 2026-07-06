"""Patient profile management response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.response.base_response import BaseResponse


class PatientAllergyData(BaseModel):
    """Patient allergy record metadata payload."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[UUID, Field(description="Unique allergy record ID")]
    patient_id: Annotated[UUID, Field(description="Patient ID")]
    allergen: Annotated[str | None, Field(default=None, description="Allergen name")]
    reaction: Annotated[str | None, Field(default=None, description="Allergic reaction")]
    severity: Annotated[str | None, Field(default=None, description="Severity of allergy")]
    recorded_at: Annotated[datetime | None, Field(default=None, description="Recording timestamp")]


class PatientAllergyResponse(BaseResponse[PatientAllergyData]):
    """Standardized response envelope for a single patient allergy record."""


class PatientAllergyListResponse(BaseResponse[list[PatientAllergyData]]):
    """Standardized response envelope for a list of patient allergy records."""


class PatientChronicConditionData(BaseModel):
    """Patient chronic condition record metadata payload."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[UUID, Field(description="Unique condition record ID")]
    patient_id: Annotated[UUID, Field(description="Patient ID")]
    condition_name: Annotated[str | None, Field(default=None, description="Condition name")]
    diagnosed_date: Annotated[date | None, Field(default=None, description="Diagnosis date")]
    status: Annotated[str | None, Field(default=None, description="Condition status")]


class PatientChronicConditionResponse(BaseResponse[PatientChronicConditionData]):
    """Standardized response envelope for a single patient chronic condition record."""


class PatientChronicConditionListResponse(BaseResponse[list[PatientChronicConditionData]]):
    """Standardized response envelope for a list of patient chronic condition records."""


class PatientMedicationData(BaseModel):
    """Patient medication record metadata payload."""

    model_config = ConfigDict(from_attributes=True)

    medication_id: Annotated[UUID, Field(description="Unique medication record ID")]
    patient_id: Annotated[UUID | None, Field(default=None, description="Patient ID")]
    drug_name_raw: Annotated[str | None, Field(default=None, description="Raw drug name")]
    drug_name_normalized: Annotated[str | None, Field(default=None, description="Normalized drug name")]
    dosage: Annotated[str | None, Field(default=None, description="Dosage")]
    frequency: Annotated[str | None, Field(default=None, description="Frequency")]
    start_date: Annotated[date | None, Field(default=None, description="Start date")]
    status: Annotated[str | None, Field(default=None, description="Medication status")]
    entry_source: Annotated[str | None, Field(default=None, description="Entry source (ocr_extraction / manual_entry)")]


class PatientMedicationResponse(BaseResponse[PatientMedicationData]):
    """Standardized response envelope for a single patient medication record."""


class PatientMedicationListResponse(BaseResponse[list[PatientMedicationData]]):
    """Standardized response envelope for a list of patient medication records."""

