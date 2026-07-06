"""Entity-based chunking service converting database rows into embedding inputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app_logging.logger import get_logger
from config.constants import METADATA_SCHEMA_VERSION

logger = get_logger(__name__)


class ChunkInput(BaseModel):
    """Structured input representing a database entity chunk for vector embedding."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(description="Unique identifier for the vector chunk")
    text: str = Field(description="Formatted sentence text describing the database entity")
    metadata: dict[str, Any] = Field(description="Primitive metadata dictionary for Pinecone filtering")


def _format_medication_text(med: Any, presc: Any, doc_obj: Any) -> str:
    """Deterministic sentence builder for a medication entity without printing literal None."""
    drug = getattr(med, "drug_name_normalized", None) or getattr(med, "drug_name_raw", None) or "Unknown medication"
    dosage = getattr(med, "dosage", None)
    freq = getattr(med, "frequency", None)
    duration = getattr(med, "duration", None)
    instructions = getattr(med, "instructions", None)

    parts = [str(drug)]
    if dosage:
        parts.append(str(dosage))
    if freq:
        parts.append(str(freq))

    main_clause = ", ".join(parts)
    duration_str = f"for {duration}" if duration else "for as needed"
    main_clause = f"{main_clause}, {duration_str}."

    inst_clause = f" Instructions: {instructions}." if instructions else ""

    doc_name = getattr(doc_obj, "name", None) if doc_obj else None
    presc_date = getattr(presc, "prescribed_date", None) if presc else None
    diag = getattr(presc, "diagnosis", None) if presc else None

    prescribed_by_parts: list[str] = []
    if doc_name or presc_date or (diag and isinstance(diag, list) and len(diag) > 0):
        if doc_name:
            prescribed_by_parts.append(f"Prescribed by {doc_name}")
        else:
            prescribed_by_parts.append("Prescribed")

        if presc_date:
            date_str = presc_date.isoformat() if hasattr(presc_date, "isoformat") else str(presc_date)
            prescribed_by_parts.append(f"on {date_str}")

        if diag and isinstance(diag, list) and len(diag) > 0:
            diag_str = ", ".join(str(d) for d in diag if d)
            if diag_str:
                prescribed_by_parts.append(f"for {diag_str}")

    prescribed_clause = " ".join(prescribed_by_parts)
    if prescribed_clause:
        prescribed_clause = f" {prescribed_clause}."

    return f"{main_clause}{inst_clause}{prescribed_clause}".strip()


def _format_lab_result_text(lab: Any) -> str:
    """Deterministic sentence builder for a lab result entity without printing literal None."""
    test_name = getattr(lab, "test_name", None) or "Unknown test"
    val = getattr(lab, "value", None)
    unit = getattr(lab, "unit", None)
    ref = getattr(lab, "reference_range", None)
    flag = getattr(lab, "flag", None)
    t_date = getattr(lab, "test_date", None)

    val_str = f"{val}" if val is not None else ""
    if unit:
        val_str = f"{val_str} {unit}".strip()

    details: list[str] = []
    if ref:
        details.append(f"reference range: {ref}")
    if flag:
        details.append(f"flag: {flag}")

    details_clause = f" ({', '.join(details)})" if details else ""

    date_str = ""
    if t_date:
        fmt_date = t_date.isoformat() if hasattr(t_date, "isoformat") else str(t_date)
        date_str = f" on {fmt_date}"

    if val_str:
        return f"{test_name}: {val_str}{details_clause}{date_str}."
    return f"{test_name}{details_clause}{date_str}."


def build_medication_chunks(
    prescription: Any,
    doctor: Any,
    medications: list[Any],
    patient_id: Any,
    document_id: Any = None,
    entry_source: str | None = None,
) -> list[ChunkInput]:
    """Build entity chunks for each medication record from a prescription or manual entry."""
    chunks: list[ChunkInput] = []
    presc_date = getattr(prescription, "prescribed_date", None) if prescription else None
    event_date_str = ""
    if presc_date:
        event_date_str = presc_date.isoformat() if hasattr(presc_date, "isoformat") else str(presc_date)

    for med in medications:
        med_id = getattr(med, "medication_id", None)
        if not med_id:
            continue
        med_source = entry_source or getattr(med, "entry_source", None) or ("manual_entry" if document_id is None else "ocr_extraction")
        if med_source == "manual_entry" or document_id is None:
            chunk_id = f"patient_{patient_id}_manual_med_{med_id}"
            doc_id_val = ""
            doc_type_val = "manual_entry"
            source_val = "manual_entry"
        else:
            chunk_id = f"patient_{patient_id}_doc_{document_id}_med_{med_id}"
            doc_id_val = str(document_id)
            doc_type_val = "prescription"
            source_val = "structured_extraction"

        text = _format_medication_text(med, prescription, doctor)
        metadata = {
            "patient_id": str(patient_id),
            "document_id": doc_id_val,
            "document_type": doc_type_val,
            "chunk_type": "medication",
            "reference_id": str(med_id),
            "event_date": event_date_str,
            "version": METADATA_SCHEMA_VERSION,
            "source": source_val,
            "entry_source": med_source,
            "text": text,
        }
        chunks.append(ChunkInput(chunk_id=chunk_id, text=text, metadata=metadata))

    logger.info(
        "Built medication entity chunks",
        document_id=str(document_id) if document_id else "manual",
        patient_id=str(patient_id),
        chunk_count=len(chunks),
    )
    return chunks


def build_lab_result_chunks(
    lab_results: list[Any],
    document: Any,
    patient_id: Any,
    document_id: Any,
) -> list[ChunkInput]:
    """Build entity chunks for each lab test measurement record."""
    chunks: list[ChunkInput] = []

    for lab in lab_results:
        lab_id = getattr(lab, "id", None) or getattr(lab, "lab_result_id", None)
        if not lab_id:
            continue
        chunk_id = f"patient_{patient_id}_doc_{document_id}_lab_{lab_id}"
        text = _format_lab_result_text(lab)
        t_date = getattr(lab, "test_date", None)
        event_date_str = ""
        if t_date:
            event_date_str = t_date.isoformat() if hasattr(t_date, "isoformat") else str(t_date)

        metadata = {
            "patient_id": str(patient_id),
            "document_id": str(document_id),
            "document_type": "lab_report",
            "chunk_type": "lab_result",
            "reference_id": str(lab_id),
            "event_date": event_date_str,
            "version": METADATA_SCHEMA_VERSION,
            "source": "structured_extraction",
            "text": text,
        }
        chunks.append(ChunkInput(chunk_id=chunk_id, text=text, metadata=metadata))

    logger.info(
        "Built lab result entity chunks",
        document_id=str(document_id),
        patient_id=str(patient_id),
        chunk_count=len(chunks),
    )
    return chunks
