"""add instructions column to medications

Revision ID: 268503f1f64a
Revises: 5889661e2715
Create Date: 2026-07-04 11:09:16.681346
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '268503f1f64a'
down_revision = '5889661e2715'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('medications', sa.Column('instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('medications', 'instructions')
