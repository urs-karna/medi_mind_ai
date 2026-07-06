"""Chat retrieval audit trail ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_CHAT_MESSAGES, TABLE_CHAT_RETRIEVALS
from database.base import Base
from models.mixins import TimestampMixin


class ChatRetrieval(TimestampMixin, Base):
    """Stores vector retrieval audit records grounding assistant chat responses."""

    __tablename__ = TABLE_CHAT_RETRIEVALS

    retrieval_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_CHAT_MESSAGES}.message_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid(as_uuid=True), nullable=True)
    chunk_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    retrieved_text: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    message = relationship("ChatMessage", back_populates="retrievals")
