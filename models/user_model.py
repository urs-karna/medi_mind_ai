"""User account ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.constants import TABLE_USERS
from models.base_model import BaseModel


class User(BaseModel):
    """Stores the authenticated account that future features will authorize against."""

    __tablename__ = TABLE_USERS

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    last_login: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="user", uselist=False)
