"""Doctor ORM model."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_DOCTORS
from database.base import Base


class Doctor(Base):
    """Stores doctor information."""

    __tablename__ = TABLE_DOCTORS

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    registration_no: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    specialty: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    clinic: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
