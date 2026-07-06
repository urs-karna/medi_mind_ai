"""Lab result ORM model."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_DOCUMENTS, TABLE_LAB_RESULTS, TABLE_PATIENTS
from database.base import Base


class LabResult(Base):
    """Stores laboratory test measurements and flags."""

    __tablename__ = TABLE_LAB_RESULTS

    id: Mapped[uuid.UUID] = mapped_column(
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
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_DOCUMENTS}.document_id", ondelete="SET NULL"),
        nullable=True,
    )
    test_name: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    value: Mapped[Decimal | None] = mapped_column(sa.Numeric, nullable=True)
    unit: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    reference_range: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    flag: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    test_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
