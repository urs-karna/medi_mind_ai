"""Chat message ORM model."""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_CHAT_MESSAGES, TABLE_CHAT_SESSIONS
from database.base import Base
from models.mixins import TimestampMixin


class ChatMessage(TimestampMixin, Base):
    """Stores individual messages within a chat conversation session."""

    __tablename__ = TABLE_CHAT_MESSAGES

    message_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_CHAT_SESSIONS}.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    citations: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB, nullable=True)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    session = relationship("ChatSession", back_populates="messages")
    retrievals = relationship("ChatRetrieval", back_populates="message", cascade="all, delete-orphan")
