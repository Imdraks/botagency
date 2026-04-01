"""Add French legal compliance fields to workspace

Revision ID: 020_french_legal_fields
Revises: 019_agency_cockpit
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = '020_french_legal_fields'
down_revision = '019_agency_cockpit'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workspaces', sa.Column('forme_juridique', sa.String(50), nullable=True))
    op.add_column('workspaces', sa.Column('capital_social', sa.String(50), nullable=True))
    op.add_column('workspaces', sa.Column('rcs_city', sa.String(100), nullable=True))
    op.add_column('workspaces', sa.Column('tva_franchise', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    op.drop_column('workspaces', 'tva_franchise')
    op.drop_column('workspaces', 'rcs_city')
    op.drop_column('workspaces', 'capital_social')
    op.drop_column('workspaces', 'forme_juridique')
