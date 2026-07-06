"""Patient chronic condition repository operations scoped to patient ownership."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.patient_chronic_condition_model import PatientChronicCondition

logger = get_logger(__name__)


class PatientChronicConditionRepository(BaseRepository[PatientChronicCondition]):
    """Provides CRUD operations for patient chronic condition records with ownership isolation."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(PatientChronicCondition, session, request_id)

    def create(
        self,
        patient_id: UUID | Any,
        condition_name: str,
        diagnosed_date: date | None = None,
        status: str | None = None,
    ) -> PatientChronicCondition:
        """Create and persist a new chronic condition record for a patient."""
        condition_obj = PatientChronicCondition(
            patient_id=patient_id,
            condition_name=condition_name,
            diagnosed_date=diagnosed_date,
            status=status,
        )
        res = super().create(condition_obj)
        logger.info(
            "Created patient chronic condition",
            patient_id=str(patient_id),
            table="patient_chronic_conditions",
            id=str(res.id),
            condition_name=condition_name,
        )
        return res

    def get_by_id(self, record_id: Any, patient_id: Any | None = None) -> PatientChronicCondition | None:
        """Fetch a chronic condition record by ID, enforcing patient ownership isolation."""
        return self._execute(
            "get_by_id",
            lambda: self._session.scalars(
                select(PatientChronicCondition).filter_by(id=record_id, patient_id=patient_id)
                if patient_id is not None
                else select(PatientChronicCondition).filter_by(id=record_id)
            ).first(),
            patient_id=patient_id,
        )

    def list_by_patient(self, patient_id: Any) -> list[PatientChronicCondition]:
        """Fetch all chronic condition records for a patient."""
        return self._execute(
            "list_by_patient",
            lambda: list(
                self._session.scalars(
                    select(PatientChronicCondition)
                    .filter_by(patient_id=patient_id)
                    .order_by(PatientChronicCondition.id.desc())
                ).all()
            ),
            patient_id=patient_id,
        )

    def delete(self, instance: PatientChronicCondition) -> None:
        """Delete a chronic condition record and log structured identifier deletion."""
        logger.info(
            "Deleted patient chronic condition",
            patient_id=str(instance.patient_id),
            table="patient_chronic_conditions",
            id=str(instance.id),
            condition_name=instance.condition_name,
        )
        super().delete(instance)
