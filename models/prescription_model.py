"""Prescription ORM model."""

from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_DOCTORS, TABLE_DOCUMENTS, TABLE_PATIENTS, TABLE_PRESCRIPTIONS
from database.base import Base


class Prescription(Base):
    """Stores prescription records."""

    __tablename__ = TABLE_PRESCRIPTIONS

    prescription_id: Mapped[uuid.UUID] = mapped_column(
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
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_DOCTORS}.doctor_id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_DOCUMENTS}.document_id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    prescribed_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    diagnosis: Mapped[list[str] | None] = mapped_column(ARRAY(sa.String), nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)

    medications = relationship("Medication", back_populates="prescription", cascade="all, delete-orphan")
