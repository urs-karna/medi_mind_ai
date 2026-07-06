"""Chat message repository operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from config.constants import MessageRole
from database.repositories.base_repository import BaseRepository
from models.chat_message_model import ChatMessage

logger = get_logger(__name__)


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Provides chat message CRUD operations."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(ChatMessage, session, request_id)

    def create(
        self,
        session_id: UUID | Any,
        role: MessageRole | str,
        content: str,
        citations: Any = None,
        metadata: Any = None,
    ) -> ChatMessage:
        """Create and persist a new message in a chat session."""
        role_val = MessageRole(role).value
        msg = ChatMessage(
            session_id=session_id,
            role=role_val,
            content=content,
            citations=citations,
            message_metadata=metadata,
        )
        res = super().create(msg)
        logger.info(
            "Created chat message",
            session_id=str(session_id),
            message_id=str(res.message_id),
            role=role_val,
        )
        return res

    def list_by_session(self, session_id: Any, limit: int = 50) -> list[ChatMessage]:
        """Fetch conversation messages for a session ordered oldest-first up to limit."""
        return self._execute(
            "list_by_session",
            lambda: list(
                self._session.scalars(
                    select(ChatMessage)
                    .filter_by(session_id=session_id)
                    .order_by(ChatMessage.created_at.asc())
                    .limit(limit)
                ).all()
            ),
        )
