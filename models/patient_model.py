"""Patient profile ORM model."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_PATIENTS, TABLE_USERS
from models.base_model import BaseModel


class Patient(BaseModel):
    """Stores the person-specific profile tied one-to-one to a user account."""

    __tablename__ = TABLE_PATIENTS

    patient_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(f"{TABLE_USERS}.user_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    dob: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric, nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric, nullable=True)

    user = relationship("User", back_populates="patient")
    allergies = relationship("PatientAllergy", back_populates="patient", cascade="all, delete-orphan")
