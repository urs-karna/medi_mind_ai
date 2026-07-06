"""Patient repository operations."""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from database.repositories.base_repository import BaseRepository
from models.patient_model import Patient


class PatientRepository(BaseRepository[Patient]):
    """Provides repository operations for patient entities."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(Patient, session, request_id)

    def get_by_id(self, record_id: Any = None, patient_id: Any = None) -> Patient | None:
        """Fetch a single patient profile by patient_id or record_id."""
        target_id = patient_id if patient_id is not None else record_id
        return self._execute(
            "get_by_id",
            lambda: self._session.get(Patient, target_id),
            patient_id=target_id,
        )
 