"""Chat session ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_CHAT_SESSIONS, TABLE_PATIENTS
from database.base import Base
from models.mixins import TimestampMixin


class ChatSession(TimestampMixin, Base):
    """Stores chat conversation session metadata and status."""

    __tablename__ = TABLE_CHAT_SESSIONS

    session_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_PATIENTS}.patient_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=True,
        server_default=sa.text("true"),
        nullable=False,
    )

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
