"""Patient allergy ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_PATIENT_ALLERGIES, TABLE_PATIENTS
from database.base import Base


class PatientAllergy(Base):
    """Stores patient allergy records."""

    __tablename__ = TABLE_PATIENT_ALLERGIES

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
    allergen: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    reaction: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    severity: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    recorded_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    )

    patient = relationship("Patient", back_populates="allergies")
