"""Medication ORM model."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_MEDICATIONS, TABLE_PATIENTS, TABLE_PRESCRIPTIONS
from database.base import Base


class Medication(Base):
    """Stores prescribed or reported medication records."""

    __tablename__ = TABLE_MEDICATIONS

    medication_id: Mapped[uuid.UUID] = mapped_column(
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
    prescription_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_PRESCRIPTIONS}.prescription_id", ondelete="CASCADE"),
        nullable=True,
    )
    drug_name_raw: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    drug_name_normalized: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    drug_class: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    dosage: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    route: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    frequency: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    duration: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    status: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    side_effects_reported: Mapped[list[str] | None] = mapped_column(ARRAY(sa.String), nullable=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(sa.Numeric, nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    entry_source: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        default="ocr_extraction",
        server_default=sa.text("'ocr_extraction'"),
    )

    prescription = relationship("Prescription", back_populates="medications")
