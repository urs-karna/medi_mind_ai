"""Shared ORM base model for MediMind AI tables."""

from __future__ import annotations

from database.base import Base
from models.mixins import TimestampMixin


class BaseModel(TimestampMixin, Base):
    """Common parent for all concrete application tables.

    Each child defines its own UUID primary-key column (``user_id``,
    ``patient_id``, …) so they match the SQL schema exactly.
    """

    __abstract__ = True
