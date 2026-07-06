"""Medication specific repository operations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config.constants import MEDICATION_STATUS_ACTIVE
from database.repositories.base_repository import BaseRepository
from models.medication_model import Medication


class MedicationRepository(BaseRepository[Medication]):
    """Provides indexed exact-match queries and active medication filtering."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(Medication, session, request_id)

    def get_active_by_patient_id(self, patient_id: uuid.UUID | Any) -> list[Medication]:
        """Fetch all currently active medications for a patient."""
        return self._execute(
            "get_active_by_patient_id",
            lambda: list(
                self._session.scalars(
                    select(Medication).filter_by(
                        patient_id=patient_id,
                        status=MEDICATION_STATUS_ACTIVE,
                    )
                ).all()
            ),
            patient_id=patient_id,
        )

    def get_by_drug_name_normalized(
        self, patient_id: uuid.UUID | Any, drug_name_normalized: str
    ) -> list[Medication]:
        """Fetch patient medications matching an exact normalized drug name."""
        return self._execute(
            "get_by_drug_name_normalized",
            lambda: list(
                self._session.scalars(
                    select(Medication).filter_by(
                        patient_id=patient_id,
                        drug_name_normalized=drug_name_normalized,
                    )
                ).all()
            ),
            patient_id=patient_id,
        )

    def delete_by_prescription_id(self, prescription_id: uuid.UUID | Any) -> int:
        """Delete all medications for a specific prescription inside an active transaction."""
        return self._execute(
            "delete_by_prescription_id",
            lambda: self._delete_by_prescription_id(prescription_id),
        )

    def _delete_by_prescription_id(self, prescription_id: uuid.UUID | Any) -> int:
        meds = list(self._session.scalars(select(Medication).filter_by(prescription_id=prescription_id)).all())
        count = len(meds)
        for med in meds:
            self._session.delete(med)
        self._session.flush()
        return count

    def create_manual(
        self,
        patient_id: uuid.UUID | Any,
        drug_name_raw: str,
        drug_name_normalized: str | None,
        dosage: str | None = None,
        frequency: str | None = None,
        start_date: Any | None = None,
    ) -> Medication:
        """Create and persist a new manually entered medication record."""
        med_obj = Medication(
            patient_id=patient_id,
            drug_name_raw=drug_name_raw,
            drug_name_normalized=drug_name_normalized,
            dosage=dosage,
            frequency=frequency,
            start_date=start_date,
            status=MEDICATION_STATUS_ACTIVE,
            prescription_id=None,
            extraction_confidence=None,
            entry_source="manual_entry",
        )
        return self.create(med_obj)

    def get_by_id_and_patient(self, medication_id: Any, patient_id: Any) -> Medication | None:
        """Fetch a medication by ID, enforcing patient ownership isolation."""
        return self._execute(
            "get_by_id_and_patient",
            lambda: self._session.scalars(
                select(Medication).filter_by(medication_id=medication_id, patient_id=patient_id)
            ).first(),
            patient_id=patient_id,
        )

    def list_by_patient(self, patient_id: Any) -> list[Medication]:
        """Fetch all medications for a patient ordered by start_date descending."""
        return self._execute(
            "list_by_patient",
            lambda: list(
                self._session.scalars(
                    select(Medication)
                    .filter_by(patient_id=patient_id)
                    .order_by(Medication.start_date.desc().nulls_last())
                ).all()
            ),
            patient_id=patient_id,
        )

