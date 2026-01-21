"""Add drive_folder_assets column to projects

Revision ID: 024_drive_folder_assets
Revises: 023_unified_assets
Create Date: 2026-01-21

This adds the 00_Assets subfolder to the project Drive structure
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '024_drive_folder_assets'
down_revision = '023_unified_assets'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('drive_folder_assets', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('projects', 'drive_folder_assets')
