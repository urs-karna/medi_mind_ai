"""Patient chronic condition ORM model."""

from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_PATIENT_CHRONIC_CONDITIONS, TABLE_PATIENTS
from database.base import Base


class PatientChronicCondition(Base):
    """Stores patient chronic condition records."""

    __tablename__ = TABLE_PATIENT_CHRONIC_CONDITIONS

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
    condition_name: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    diagnosed_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    status: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
