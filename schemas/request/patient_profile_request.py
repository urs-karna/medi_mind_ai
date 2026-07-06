"""Patient profile management request schemas."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientAllergyCreateRequest(BaseModel):
    """Schema for creating a patient allergy record."""

    model_config = ConfigDict(from_attributes=True)

    allergen: Annotated[str, Field(min_length=1, description="Name of the allergen")]
    reaction: Annotated[str | None, Field(default=None, description="Observed allergic reaction")]
    severity: Annotated[str | None, Field(default=None, description="Severity: mild, moderate, or severe")]

    @field_validator("severity", mode="before")
    @classmethod
    def _validate_severity(cls, val: Any) -> str | None:
        if val is None or str(val).strip() == "":
            return None
        cleaned = str(val).strip().lower()
        if cleaned not in ("mild", "moderate", "severe"):
            raise ValueError("Severity must be one of: mild, moderate, severe")
        return cleaned


class PatientChronicConditionCreateRequest(BaseModel):
    """Schema for creating a patient chronic condition record."""

    model_config = ConfigDict(from_attributes=True)

    condition_name: Annotated[str, Field(min_length=1, description="Name of the chronic condition")]
    diagnosed_date: Annotated[date | None, Field(default=None, description="Date of diagnosis (YYYY-MM-DD)")]
    status: Annotated[str | None, Field(default="active", description="Status: active or resolved")]

    @field_validator("status", mode="before")
    @classmethod
    def _validate_status(cls, val: Any) -> str | None:
        if val is None or str(val).strip() == "":
            return "active"
        cleaned = str(val).strip().lower()
        if cleaned not in ("active", "resolved"):
            raise ValueError("Status must be either active or resolved")
        return cleaned


class PatientMedicationCreateRequest(BaseModel):
    """Schema for manually creating a patient medication record."""

    model_config = ConfigDict(from_attributes=True)

    drug_name: Annotated[str, Field(min_length=1, description="Name of the medication")]
    dosage: Annotated[str | None, Field(default=None, description="Dosage (e.g. 500mg)")]
    frequency: Annotated[str | None, Field(default=None, description="Frequency (e.g. Twice daily)")]
    start_date: Annotated[date | None, Field(default=None, description="Start date (YYYY-MM-DD)")]

