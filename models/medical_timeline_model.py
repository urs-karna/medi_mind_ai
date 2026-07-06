"""Medical timeline event ORM model."""

from __future__ import annotations

import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_MEDICAL_TIMELINE, TABLE_PATIENTS
from models.base_model import BaseModel


class MedicalTimeline(BaseModel):
    """Stores chronological medical timeline events for a patient."""

    __tablename__ = TABLE_MEDICAL_TIMELINE
    __table_args__ = (
        sa.Index("idx_timeline_patient_date", "patient_id", sa.text("event_date DESC")),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
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
    event_type: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    event_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid(as_uuid=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
