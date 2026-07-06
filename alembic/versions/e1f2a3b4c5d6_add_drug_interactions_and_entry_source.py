"""add drug interactions table and medication entry source

Revision ID: e1f2a3b4c5d6
Revises: dcc950e82e69
Create Date: 2026-07-06 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'e1f2a3b4c5d6'
down_revision = 'dcc950e82e69'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'drug_interactions',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('drug_a_normalized', sa.Text(), nullable=False),
        sa.Column('drug_b_normalized', sa.Text(), nullable=False),
        sa.Column('severity', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.add_column(
        'medications',
        sa.Column('entry_source', sa.Text(), server_default=sa.text("'ocr_extraction'"), nullable=True)
    )

    # Note: This is a short curated starter reference set of well-known drug interactions,
    # NOT a comprehensive medical database. In production/V2, this should be backed by or
    # replaced with an external clinical interaction API (e.g., RxNorm / DrugBank / openFDA).
    op.bulk_insert(
        sa.table(
            'drug_interactions',
            sa.column('drug_a_normalized', sa.Text),
            sa.column('drug_b_normalized', sa.Text),
            sa.column('severity', sa.Text),
            sa.column('description', sa.Text),
        ),
        [
            {
                'drug_a_normalized': 'diclofenac',
                'drug_b_normalized': 'metformin',
                'severity': 'moderate',
                'description': 'NSAIDs like Diclofenac can impair renal function and reduce Metformin clearance, increasing the risk of lactic acidosis.'
            },
            {
                'drug_a_normalized': 'ibuprofen',
                'drug_b_normalized': 'metformin',
                'severity': 'moderate',
                'description': 'NSAIDs like Ibuprofen can impair kidney function and reduce Metformin excretion, increasing the risk of metabolic complications.'
            },
            {
                'drug_a_normalized': 'diclofenac',
                'drug_b_normalized': 'aspirin',
                'severity': 'severe',
                'description': 'Concurrent use of Diclofenac and Aspirin significantly increases the risk of gastrointestinal bleeding and ulceration.'
            },
            {
                'drug_a_normalized': 'diclofenac',
                'drug_b_normalized': 'warfarin',
                'severity': 'severe',
                'description': 'NSAIDs like Diclofenac increase bleeding risk when taken with anticoagulants like Warfarin due to platelet inhibition and gastric mucosal injury.'
            },
            {
                'drug_a_normalized': 'ibuprofen',
                'drug_b_normalized': 'aspirin',
                'severity': 'severe',
                'description': 'Ibuprofen can interfere with the antiplatelet effect of low-dose Aspirin and increase gastrointestinal bleeding risk.'
            },
        ]
    )


def downgrade() -> None:
    op.drop_column('medications', 'entry_source')
    op.drop_table('drug_interactions')
