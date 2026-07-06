"""Pydantic schemas for LangChain structured vision output extraction."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentClassificationSchema(BaseModel):
    """Schema forcing structured document category classification and confidence scoring."""

    model_config = ConfigDict(from_attributes=True)

    document_type: Literal[
        "prescription_printed",
        "prescription_handwritten",
        "lab_report",
        "drug_package",
        "medical_bill",
        "discharge_summary",
        "insurance_document",
        "medical_record",
    ] = Field(description="Exact classified medical document category")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Certainty score of classification between 0.0 and 1.0",
    )


class DoctorInfoSchema(BaseModel):
    """Extracted doctor details from a prescription document."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, description="Full name of the prescribing doctor")
    registration_no: str | None = Field(default=None, description="Medical registration or license number of the doctor")
    clinic: str | None = Field(default=None, description="Name of the hospital or clinic")
    specialty: str | None = Field(default=None, description="Medical specialty of the doctor, e.g. Cardiology")


class PatientInfoSchema(BaseModel):
    """Extracted patient details from a medical document."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, description="Full name of the patient")
    gender: str | None = Field(default=None, description="Gender of the patient, e.g. Male or Female")
    age: int | None = Field(
        default=None,
        description="Patient age as a plain integer, e.g. 25 — not '25 yrs' or '25 years old'",
    )


class MedicineItemSchema(BaseModel):
    """Extracted medicine line item details from a prescription."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, description="Brand or generic name of the medicine")
    dosage: str | None = Field(default=None, description="Dosage amount per intake, e.g. 500mg")
    frequency: str | None = Field(default=None, description="Intake frequency, e.g. Twice daily or TID")
    duration: str | None = Field(default=None, description="Duration of treatment, e.g. 5 days or 1 week")
    instructions: str | None = Field(default=None, description="Special intake instructions, e.g. After meals")


class PrescriptionExtractionSchema(BaseModel):
    """Structured extraction schema for printed or handwritten prescriptions."""

    model_config = ConfigDict(from_attributes=True)

    doctor: DoctorInfoSchema = Field(description="Prescribing doctor information")
    patient: PatientInfoSchema = Field(description="Patient demographic information")
    medicines: list[MedicineItemSchema] = Field(default_factory=list, description="List of prescribed medications")
    diagnosis: list[str] = Field(default_factory=list, description="List of diagnosed conditions or symptoms mentioned")
    follow_up_date: date | None = Field(
        default=None,
        description="Follow-up date formatted strictly as YYYY-MM-DD (e.g. 2026-07-10) if present, otherwise null",
    )


class LabTestItemSchema(BaseModel):
    """Extracted individual test measurement from a laboratory report."""

    model_config = ConfigDict(from_attributes=True)

    test_name: str | None = Field(default=None, description="Name of the laboratory test conducted, e.g. Hemoglobin")
    value: float | None = Field(default=None, description="Numeric result value of the test measurement as a plain float")
    unit: str | None = Field(default=None, description="Measurement unit, e.g. g/dL or mg/dL")
    reference_range: str | None = Field(default=None, description="Normal reference range string, e.g. 13.5 - 17.5")
    flag: str | None = Field(default=None, description="Abnormality flag indicator, e.g. Normal, High, or Low")
    test_date: date | None = Field(
        default=None,
        description="Date the test was conducted formatted strictly as YYYY-MM-DD if present, otherwise null",
    )


class LabReportExtractionSchema(BaseModel):
    """Structured extraction schema for laboratory test reports."""

    model_config = ConfigDict(from_attributes=True)

    tests: list[LabTestItemSchema] = Field(default_factory=list, description="List of laboratory test measurements")


class GenericExtractionSchema(BaseModel):
    """Structured extraction schema for general medical documents, bills, and summaries."""

    model_config = ConfigDict(from_attributes=True)

    summary: str | None = Field(default=None, description="Concise summary of the medical document contents")
    key_dates: list[str] = Field(default_factory=list, description="List of important dates found in the document")
    entities_detected: list[str] = Field(default_factory=list, description="Key medical entities, facilities, or procedures detected")
    notes: str | None = Field(default=None, description="Any additional observations or comments regarding the document")
