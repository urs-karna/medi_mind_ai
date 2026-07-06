"""Central SQLAlchemy declarative base for MediMind AI."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base imported by every ORM model."""
