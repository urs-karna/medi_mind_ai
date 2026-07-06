"""Lab result repository operations."""

from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.repositories.base_repository import BaseRepository
from models.lab_result_model import LabResult


class LabResultRepository(BaseRepository[LabResult]):
    """Provides repository operations for lab result entities."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(LabResult, session, request_id)

    def list_by_document_id(self, document_id: uuid.UUID | Any) -> list[LabResult]:
        """Fetch all lab results matching a specific document_id."""
        return self._execute(
            "list_by_document_id",
            lambda: list(self._session.scalars(select(LabResult).filter_by(document_id=document_id)).all()),
        )

    def delete_by_document_id(self, document_id: uuid.UUID | Any) -> int:
        """Delete all lab results for a specific document_id inside an active transaction."""
        return self._execute(
            "delete_by_document_id",
            lambda: self._delete_by_document_id(document_id),
        )

    def _delete_by_document_id(self, document_id: uuid.UUID | Any) -> int:
        labs = list(self._session.scalars(select(LabResult).filter_by(document_id=document_id)).all())
        count = len(labs)
        for lab in labs:
            self._session.delete(lab)
        self._session.flush()
        return count
