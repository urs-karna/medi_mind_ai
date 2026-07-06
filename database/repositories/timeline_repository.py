"""Medical timeline repository operations."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.document_model import Document
from models.medical_timeline_model import MedicalTimeline

logger = get_logger(__name__)


class TimelineRepository(BaseRepository[MedicalTimeline]):
    """Provides helper operations for recording medical timeline events."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(MedicalTimeline, session, request_id)

    def insert_event(
        self,
        patient_id: uuid.UUID | Any,
        event_type: str,
        event_date: date | None,
        summary: str,
        reference_id: uuid.UUID | None = None,
    ) -> MedicalTimeline:
        """Insert a new chronological event into a patient's medical timeline with fallback date handling."""
        if event_date is None:
            doc = self._session.get(Document, reference_id) if reference_id else None
            if doc and doc.uploaded_at:
                event_date = doc.uploaded_at.date()
                logger.warning(
                    "Missing event_date fallback to document uploaded_at",
                    patient_id=str(patient_id),
                    reference_id=str(reference_id),
                    fallback_date=str(event_date),
                    request_id=self._request_id,
                )
            else:
                event_date = datetime.now(timezone.utc).date()
                logger.warning(
                    "Missing event_date fallback to current date",
                    patient_id=str(patient_id),
                    fallback_date=str(event_date),
                    request_id=self._request_id,
                )

        event = MedicalTimeline(
            patient_id=patient_id,
            event_type=event_type,
            event_date=event_date,
            summary=summary,
            reference_id=reference_id,
        )
        return self.add(event)

    def delete_by_reference_id(self, reference_id: uuid.UUID | Any) -> int:
        """Delete timeline events for a specific reference_id inside an active transaction."""
        return self._execute(
            "delete_by_reference_id",
            lambda: self._delete_by_reference_id(reference_id),
        )

    def _delete_by_reference_id(self, reference_id: uuid.UUID | Any) -> int:
        events = list(self._session.scalars(select(MedicalTimeline).filter_by(reference_id=reference_id)).all())
        count = len(events)
        for event in events:
            self._session.delete(event)
        self._session.flush()
        return count
