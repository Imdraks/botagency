"""Add Drive subfolder IDs to projects

Revision ID: 022_drive_subfolders
Revises: 021_project_detail_fields
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '022_drive_subfolders'
down_revision = '021_project_detail_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add subfolder columns to projects table
    op.add_column('projects', sa.Column('drive_folder_brief', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('drive_folder_production', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('drive_folder_postprod', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('drive_folder_exports', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('drive_folder_admin', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('drive_folder_archive', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('projects', 'drive_folder_archive')
    op.drop_column('projects', 'drive_folder_admin')
    op.drop_column('projects', 'drive_folder_exports')
    op.drop_column('projects', 'drive_folder_postprod')
    op.drop_column('projects', 'drive_folder_production')
    op.drop_column('projects', 'drive_folder_brief')
