"""Prescription repository operations."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.repositories.base_repository import BaseRepository
from models.prescription_model import Prescription


class PrescriptionRepository(BaseRepository[Prescription]):
    """Provides repository operations for prescription entities."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(Prescription, session, request_id)

    def get_by_document_id(self, document_id: Any) -> Prescription | None:
        """Fetch a single prescription row matching a specific document_id."""
        return self._execute(
            "get_by_document_id",
            lambda: self._session.scalars(select(Prescription).filter_by(document_id=document_id)).first(),
        )
