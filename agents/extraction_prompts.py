"""Prompt engineering templates for medical document OCR and classification."""

from __future__ import annotations

from config.constants import (
    DOCUMENT_TYPE_DISCHARGE_SUMMARY,
    DOCUMENT_TYPE_DRUG_PACKAGE,
    DOCUMENT_TYPE_INSURANCE_DOCUMENT,
    DOCUMENT_TYPE_LAB_REPORT,
    DOCUMENT_TYPE_MEDICAL_BILL,
    DOCUMENT_TYPE_MEDICAL_RECORD,
    DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN,
    DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
    DOCUMENT_TYPES,
)


def get_classification_prompt() -> str:
    """Return prompt instructing Gemini to classify the document type."""
    allowed = ", ".join(DOCUMENT_TYPES)
    return f"""You are a healthcare document classification expert. Analyze this medical document image and classify it into exactly one of the following allowed categories:
{allowed}

Return valid JSON only, no markdown fences, no explanation text.
Format your output strictly as:
{{"document_type": "<exact_category_string>", "confidence": 0.95}}

If the document is partially obscured, estimate the best fitting category and reflect your certainty in the confidence score (between 0.0 and 1.0)."""


def get_extraction_prompt(document_type: str) -> str:
    """Return structured JSON extraction prompt tailored to the document type."""
    common_footer = (
        "Extract accurately from the document image. "
        "If a field is unreadable or missing, leave it null/empty — do not guess."
    )

    if document_type in (DOCUMENT_TYPE_PRESCRIPTION_PRINTED, DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN):
        schema = """{
  "doctor": {
    "name": null,
    "registration_no": null,
    "clinic": null,
    "specialty": null
  },
  "patient": {
    "name": null,
    "gender": null,
    "age": null
  },
  "medicines": [
    {
      "name": null,
      "dosage": null,
      "frequency": null,
      "duration": null,
      "instructions": null
    }
  ],
  "diagnosis": [],
  "follow_up_date": null
}"""
    elif document_type == DOCUMENT_TYPE_LAB_REPORT:
        schema = """{
  "tests": [
    {
      "test_name": null,
      "value": null,
      "unit": null,
      "reference_range": null,
      "flag": null,
      "test_date": null
    }
  ]
}"""
    else:
        schema = """{
  "summary": null,
  "key_dates": [],
  "entities_detected": [],
  "notes": null
}"""

    return f"""Extract all structured medical data from this {document_type} document strictly matching the following JSON schema structure:
{schema}

{common_footer}"""
