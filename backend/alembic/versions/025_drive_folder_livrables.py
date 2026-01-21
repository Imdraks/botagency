"""Add drive_folder_livrables column to projects

Revision ID: 025_drive_folder_livrables
Revises: 024_drive_folder_assets
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '025_drive_folder_livrables'
down_revision = '024_drive_folder_assets'
branch_labels = None
depends_on = None


def upgrade():
    # Add drive_folder_livrables column for 07_Livrables subfolder
    op.add_column('projects', sa.Column('drive_folder_livrables', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('projects', 'drive_folder_livrables')
