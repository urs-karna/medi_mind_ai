"""Doctor repository operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.doctor_model import Doctor

logger = get_logger(__name__)


def _normalize_string(text: str | None) -> str:
    """Normalize string by stripping leading/trailing whitespace and lowercasing."""
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


class DoctorRepository(BaseRepository[Doctor]):
    """Provides doctor lookup and V1 deduplication operations."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(Doctor, session, request_id)

    def find_or_create(
        self,
        name: str,
        clinic: str | None = None,
        registration_no: str | None = None,
        specialty: str | None = None,
    ) -> Doctor:
        """Find existing doctor by normalized name+clinic pair or insert a new record."""
        norm_name = _normalize_string(name)
        norm_clinic = _normalize_string(clinic)

        stmt = select(Doctor)
        existing_doctors = list(self._session.scalars(stmt).all())
        for doc in existing_doctors:
            if _normalize_string(doc.name) == norm_name and _normalize_string(doc.clinic) == norm_clinic:
                logger.info(
                    "Doctor dedup hit found existing record",
                    doctor_id=str(doc.doctor_id),
                    name=name,
                    request_id=self._request_id,
                )
                return doc

        new_doctor = Doctor(
            name=name.strip() if name else "Unknown Doctor",
            clinic=clinic.strip() if clinic else None,
            registration_no=registration_no.strip() if registration_no else None,
            specialty=specialty.strip() if specialty else None,
        )
        created_doc = self.add(new_doctor)
        logger.info(
            "Created new doctor record",
            doctor_id=str(created_doc.doctor_id),
            name=name,
            request_id=self._request_id,
        )
        return created_doc
