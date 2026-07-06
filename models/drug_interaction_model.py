"""Drug interaction ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from config.constants import TABLE_DRUG_INTERACTIONS
from database.base import Base


class DrugInteraction(Base):
    """Stores known pairwise drug-drug interaction reference data."""

    __tablename__ = TABLE_DRUG_INTERACTIONS

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )
    drug_a_normalized: Mapped[str] = mapped_column(sa.Text, nullable=False)
    drug_b_normalized: Mapped[str] = mapped_column(sa.Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )
