"""Service layer for persisting AI extracted JSON data into structured clinical tables."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from config.constants import (
    DOCUMENT_STATUS_READY,
    DOCUMENT_TYPE_LAB_REPORT,
    DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN,
    DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
    MEDICATION_STATUS_ACTIVE,
)
from database.connection import get_engine
from database.repositories.doctor_repository import DoctorRepository
from database.repositories.document_repository import DocumentRepository
from database.repositories.lab_result_repository import LabResultRepository
from database.repositories.medication_repository import MedicationRepository
from database.repositories.patient_repository import PatientRepository
from database.repositories.prescription_repository import PrescriptionRepository
from database.repositories.timeline_repository import TimelineRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import AIExtractionException, DatabaseException, NotFoundException
from helpers.drug_normalizer import normalize_drug_name
from models.lab_result_model import LabResult
from models.medication_model import Medication
from models.prescription_model import Prescription

logger = get_logger(__name__)


def _parse_date_string(val: Any) -> date | None:
    """Parse ISO YYYY-MM-DD date string into date object."""
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except Exception:
        return None


def _check_patient_mismatch(ext_name: str | None, profile_name: str | None, patient_id: str, request_id: str) -> None:
    """Log warning if extracted patient name does not loosely match profile name."""
    if not ext_name or not profile_name:
        return
    ext_words = {w.lower() for w in ext_name.split() if len(w) >= 3}
    profile_words = {w.lower() for w in profile_name.split() if len(w) >= 3}
    if not ext_words.intersection(profile_words):
        logger.warning(
            "possible_patient_mismatch",
            extracted_name=ext_name,
            profile_name=profile_name,
            patient_id=patient_id,
            request_id=request_id,
        )


class ExtractionPersistenceService:
    """Persists validated extraction JSON into doctors, prescriptions, medications, and lab results."""

    def persist_extraction(self, document_id: UUID | str, patient_id: UUID | str, request_id: str = "") -> dict[str, int]:
        """Write structured extraction data to database tables inside a transactional block."""
        counts = {
            "prescriptions_created": 0,
            "medications_created": 0,
            "lab_results_created": 0,
            "timeline_events_created": 0,
        }

        session: Session = SessionLocal(bind=get_engine())
        try:
            with session.begin():
                doc_repo = DocumentRepository(session=session, request_id=request_id)
                doc = doc_repo.get_by_id(document_id=document_id, patient_id=patient_id)
                if doc is None:
                    raise NotFoundException("Document not found")
                if doc.status != DOCUMENT_STATUS_READY:
                    raise AIExtractionException(f"Cannot persist document with status {doc.status}; must be READY")

                ext_data = doc.extraction_json or {}
                doc_type = doc.document_type or ""

                if doc_type in (DOCUMENT_TYPE_PRESCRIPTION_PRINTED, DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN):
                    doctor_repo = DoctorRepository(session=session, request_id=request_id)
                    patient_repo = PatientRepository(session=session, request_id=request_id)
                    presc_repo = PrescriptionRepository(session=session, request_id=request_id)
                    med_repo = MedicationRepository(session=session, request_id=request_id)
                    timeline_repo = TimelineRepository(session=session, request_id=request_id)

                    doc_info = ext_data.get("doctor") or {}
                    doctor = doctor_repo.find_or_create(
                        name=doc_info.get("name") or "Unknown Doctor",
                        clinic=doc_info.get("clinic"),
                        registration_no=doc_info.get("registration_no"),
                        specialty=doc_info.get("specialty"),
                    )

                    patient_profile = patient_repo.get_by_id(patient_id=patient_id)
                    pat_info = ext_data.get("patient") or {}
                    _check_patient_mismatch(
                        ext_name=pat_info.get("name"),
                        profile_name=patient_profile.user.full_name if patient_profile and patient_profile.user else None,
                        patient_id=str(patient_id),
                        request_id=request_id,
                    )

                    presc_date = _parse_date_string(ext_data.get("prescribed_date"))
                    if not presc_date:
                        presc_date = doc.uploaded_at.date() if doc.uploaded_at else datetime.now().date()
                        logger.warning("Missing prescribed_date fallback used", patient_id=str(patient_id), document_id=str(document_id), request_id=request_id)

                    existing_presc = presc_repo.get_by_document_id(document_id=doc.document_id)
                    if existing_presc is not None:
                        logger.info(
                            "reprocessing_existing_prescription",
                            document_id=str(document_id),
                            prescription_id=str(existing_presc.prescription_id),
                            request_id=request_id,
                        )
                        med_repo.delete_by_prescription_id(prescription_id=existing_presc.prescription_id)
                        timeline_repo.delete_by_reference_id(reference_id=existing_presc.prescription_id)

                        existing_presc.doctor_id = doctor.doctor_id
                        existing_presc.prescribed_date = presc_date
                        existing_presc.diagnosis = ext_data.get("diagnosis") or []
                        existing_presc.follow_up_date = _parse_date_string(ext_data.get("follow_up_date"))
                        created_presc = presc_repo.update_in_tx(existing_presc)
                    else:
                        new_presc = Prescription(
                            patient_id=doc.patient_id,
                            doctor_id=doctor.doctor_id,
                            document_id=doc.document_id,
                            prescribed_date=presc_date,
                            diagnosis=ext_data.get("diagnosis") or [],
                            follow_up_date=_parse_date_string(ext_data.get("follow_up_date")),
                        )
                        created_presc = presc_repo.add(new_presc)
                        counts["prescriptions_created"] += 1
                        logger.info(
                            "creating_new_prescription",
                            document_id=str(document_id),
                            prescription_id=str(created_presc.prescription_id),
                            request_id=request_id,
                        )

                    medicines = ext_data.get("medicines") or []
                    for med_item in medicines:
                        raw_name = med_item.get("name")
                        norm_name = normalize_drug_name(raw_name)
                        new_med = Medication(
                            patient_id=doc.patient_id,
                            prescription_id=created_presc.prescription_id,
                            drug_name_raw=raw_name,
                            drug_name_normalized=norm_name,
                            dosage=med_item.get("dosage"),
                            frequency=med_item.get("frequency"),
                            duration=med_item.get("duration"),
                            instructions=med_item.get("instructions"),
                            status=MEDICATION_STATUS_ACTIVE,
                            # V1 simplification: per-medicine confidence isn't available yet, so use document-level score
                            extraction_confidence=doc.ocr_confidence,
                        )
                        created_med = med_repo.add(new_med)
                        counts["medications_created"] += 1
                        logger.info("Inserted medication record", patient_id=str(patient_id), table="medications", row_id=str(created_med.medication_id), request_id=request_id)

                    timeline_repo.insert_event(
                        patient_id=doc.patient_id,
                        event_type="prescription",
                        event_date=presc_date,
                        summary=f"Prescription from {doctor.name or 'Unknown'}",
                        reference_id=created_presc.prescription_id,
                    )
                    counts["timeline_events_created"] += 1

                elif doc_type == DOCUMENT_TYPE_LAB_REPORT:
                    lab_repo = LabResultRepository(session=session, request_id=request_id)
                    timeline_repo = TimelineRepository(session=session, request_id=request_id)

                    existing_labs = lab_repo.list_by_document_id(document_id=doc.document_id)
                    if existing_labs:
                        logger.info("reprocessing_existing_lab_report", document_id=str(document_id), request_id=request_id)
                        lab_repo.delete_by_document_id(document_id=doc.document_id)
                        timeline_repo.delete_by_reference_id(reference_id=doc.document_id)
                    else:
                        logger.info("creating_new_lab_report", document_id=str(document_id), request_id=request_id)

                    tests = ext_data.get("tests") or []
                    for test_item in tests:
                        val_raw = test_item.get("value")
                        val_num = None
                        if val_raw is not None:
                            try:
                                val_num = Decimal(str(val_raw))
                            except Exception:
                                val_num = None

                        test_date = _parse_date_string(test_item.get("test_date"))
                        new_lab = LabResult(
                            patient_id=doc.patient_id,
                            document_id=doc.document_id,
                            test_name=test_item.get("test_name"),
                            value=val_num,
                            unit=test_item.get("unit"),
                            reference_range=test_item.get("reference_range"),
                            flag=test_item.get("flag"),
                            test_date=test_date,
                        )
                        created_lab = lab_repo.add(new_lab)
                        counts["lab_results_created"] += 1
                        logger.info("Inserted lab result record", patient_id=str(patient_id), table="lab_results", row_id=str(created_lab.id), request_id=request_id)

                    timeline_repo.insert_event(
                        patient_id=doc.patient_id,
                        event_type="lab_report",
                        event_date=doc.uploaded_at.date() if doc.uploaded_at else None,
                        summary="Lab report uploaded",
                        reference_id=doc.document_id,
                    )
                    counts["timeline_events_created"] += 1

                else:
                    logger.info("Document type has no structured table persistence path yet", document_id=str(document_id), document_type=doc_type, request_id=request_id)

        except Exception as exc:
            logger.error("Failed to persist extraction data to database tables", document_id=str(document_id), error=str(exc), request_id=request_id)
            if isinstance(exc, (AIExtractionException, NotFoundException, DatabaseException)):
                raise
            raise DatabaseException(f"Database error during extraction persistence: {exc}") from exc
        finally:
            session.close()

        return counts
