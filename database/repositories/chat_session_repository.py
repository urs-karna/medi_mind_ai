"""Chat session repository operations scoped to patient ownership."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.chat_session_model import ChatSession

logger = get_logger(__name__)


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Provides chat session CRUD operations with strict patient ownership isolation."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(ChatSession, session, request_id)

    def create(self, patient_id: UUID | Any, title: str | None = None) -> ChatSession:
        """Create and persist a new chat conversation session for a patient."""
        session_obj = ChatSession(patient_id=patient_id, title=title)
        res = super().create(session_obj)
        logger.info("Created chat session", session_id=str(res.session_id), patient_id=str(patient_id))
        return res

    def get_by_id(self, session_id: Any, patient_id: Any | None = None) -> ChatSession | None:
        """Fetch a chat session by ID, enforcing patient ownership isolation."""
        return self._execute(
            "get_by_id",
            lambda: self._session.scalars(
                select(ChatSession).filter_by(session_id=session_id, patient_id=patient_id)
                if patient_id is not None
                else select(ChatSession).filter_by(session_id=session_id)
            ).first(),
            patient_id=patient_id,
        )

    def list_by_patient(
        self,
        patient_id: Any,
        limit: int = 20,
        offset: int = 0,
        is_active: bool | None = True,
    ) -> list[ChatSession]:
        """Fetch paginated chat sessions for a patient ordered by most recent activity."""
        def _query():
            stmt = select(ChatSession).filter_by(patient_id=patient_id)
            if is_active is not None:
                stmt = stmt.filter_by(is_active=is_active)
            stmt = stmt.order_by(ChatSession.updated_at.desc()).limit(limit).offset(offset)
            return list(self._session.scalars(stmt).all())

        return self._execute("list_by_patient", _query, patient_id=patient_id)

    def touch_updated_at(self, session_id: Any) -> None:
        """Update the updated_at timestamp of a chat session to current time when new activity occurs."""
        def _touch():
            stmt = (
                update(ChatSession)
                .where(ChatSession.session_id == session_id)
                .values(updated_at=sa.func.now())
            )
            self._session.execute(stmt)
            self._session.commit()

        import sqlalchemy as sa
        self._execute("touch_updated_at", _touch)
        logger.info("Touched chat session updated_at", session_id=str(session_id))
