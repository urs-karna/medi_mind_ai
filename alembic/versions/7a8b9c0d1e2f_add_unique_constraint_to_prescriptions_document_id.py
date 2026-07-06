"""add unique constraint to prescriptions document_id

Revision ID: 7a8b9c0d1e2f
Revises: 268503f1f64a
Create Date: 2026-07-04 15:30:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "7a8b9c0d1e2f"
down_revision = "268503f1f64a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_prescriptions_document_id", "prescriptions", ["document_id"])


def downgrade() -> None:
    op.drop_constraint("uq_prescriptions_document_id", "prescriptions", type_="unique")
