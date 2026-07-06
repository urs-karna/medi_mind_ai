"""Document repository operations with patient privacy enforcement."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.repositories.base_repository import BaseRepository
from models.document_model import Document


class DocumentRepository(BaseRepository[Document]):
    """Provides document CRUD operations scoped strictly to patient ownership."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(Document, session, request_id)

    def create(
        self,
        patient_id: UUID | Any = None,
        document_type: str = "",
        raw_file_uri: str = "",
        status: str = "",
        instance: Document | None = None,
    ) -> Document:
        """Create and persist a new medical document record."""
        doc = instance or Document(
            patient_id=patient_id,
            document_type=document_type,
            raw_file_uri=raw_file_uri,
            status=status,
        )
        return super().create(doc)

    def get_by_id(self, document_id: Any, patient_id: Any | None = None) -> Document | None:
        """Fetch a document by ID, enforcing patient ownership if patient_id is provided."""
        return self._execute(
            "get_by_id",
            lambda: self._session.scalars(
                select(Document).filter_by(document_id=document_id, patient_id=patient_id)
                if patient_id is not None
                else select(Document).filter_by(document_id=document_id)
            ).first(),
            patient_id=patient_id,
        )

    def list_by_patient(self, patient_id: Any, limit: int = 20, offset: int = 0) -> list[Document]:
        """Fetch paginated documents belonging to a specific patient ordered by upload time."""
        return self._execute(
            "list_by_patient",
            lambda: list(
                self._session.scalars(
                    select(Document)
                    .filter_by(patient_id=patient_id)
                    .order_by(Document.uploaded_at.desc())
                    .limit(limit)
                    .offset(offset)
                ).all()
            ),
            patient_id=patient_id,
        )
