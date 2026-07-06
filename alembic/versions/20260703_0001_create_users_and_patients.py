"""Create users and patients tables.

Revision ID: 20260703_0001
Revises: None
Create Date: 2026-07-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260703_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the auth profile tables used in later phases."""
    user_role = sa.Enum("patient", "doctor", "admin", name="user_role")
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("role", user_role, server_default=sa.text("'patient'"), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("gender", sa.String(length=50), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_patients_user_id"), "patients", ["user_id"], unique=True)


def downgrade() -> None:
    """Remove the auth profile tables if the migration is rolled back."""
    op.drop_index(op.f("ix_patients_user_id"), table_name="patients")
    op.drop_table("patients")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    user_role = sa.Enum("patient", "doctor", "admin", name="user_role")
    user_role.drop(op.get_bind(), checkfirst=True)