"""Document ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_DOCUMENTS, TABLE_PATIENTS
from database.base import Base


class Document(Base):
    """Stores uploaded medical document metadata and extraction results."""

    __tablename__ = TABLE_DOCUMENTS

    document_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_PATIENTS}.patient_id", ondelete="CASCADE"),
        nullable=True,
    )
    document_type: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    raw_file_uri: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    extraction_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ocr_confidence: Mapped[Decimal | None] = mapped_column(sa.Numeric, nullable=True)
    status: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    )
