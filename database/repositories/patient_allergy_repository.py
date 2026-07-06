"""Patient allergy repository operations scoped to patient ownership."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.patient_allergy_model import PatientAllergy

logger = get_logger(__name__)


class PatientAllergyRepository(BaseRepository[PatientAllergy]):
    """Provides CRUD operations for patient allergy records with ownership isolation."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(PatientAllergy, session, request_id)

    def create(
        self,
        patient_id: UUID | Any,
        allergen: str,
        reaction: str | None = None,
        severity: str | None = None,
    ) -> PatientAllergy:
        """Create and persist a new allergy record for a patient."""
        allergy_obj = PatientAllergy(
            patient_id=patient_id,
            allergen=allergen,
            reaction=reaction,
            severity=severity,
        )
        res = super().create(allergy_obj)
        logger.info(
            "Created patient allergy",
            patient_id=str(patient_id),
            table="patient_allergies",
            id=str(res.id),
            allergen=allergen,
        )
        return res

    def get_by_id(self, record_id: Any, patient_id: Any | None = None) -> PatientAllergy | None:
        """Fetch an allergy record by ID, enforcing patient ownership isolation."""
        return self._execute(
            "get_by_id",
            lambda: self._session.scalars(
                select(PatientAllergy).filter_by(id=record_id, patient_id=patient_id)
                if patient_id is not None
                else select(PatientAllergy).filter_by(id=record_id)
            ).first(),
            patient_id=patient_id,
        )

    def list_by_patient(self, patient_id: Any) -> list[PatientAllergy]:
        """Fetch all allergy records for a patient ordered by recording time descending."""
        return self._execute(
            "list_by_patient",
            lambda: list(
                self._session.scalars(
                    select(PatientAllergy)
                    .filter_by(patient_id=patient_id)
                    .order_by(PatientAllergy.recorded_at.desc())
                ).all()
            ),
            patient_id=patient_id,
        )

    def delete(self, instance: PatientAllergy) -> None:
        """Delete an allergy record and log structured identifier deletion."""
        logger.info(
            "Deleted patient allergy",
            patient_id=str(instance.patient_id),
            table="patient_allergies",
            id=str(instance.id),
            allergen=instance.allergen,
        )
        super().delete(instance)
