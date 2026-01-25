"""Drive folder map table

Revision ID: 034_drive_folder_map
Revises: 033_merge_billing
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '034_drive_folder_map'
down_revision = '033_merge_billing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create drive_folder_map table
    op.create_table(
        'drive_folder_map',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('google_account_id', sa.String(255), nullable=False),
        sa.Column('folder_type', sa.String(50), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('drive_folder_id', sa.String(255), nullable=False),
        sa.Column('drive_parent_id', sa.String(255), nullable=True),
        sa.Column('folder_name', sa.String(255), nullable=False),
        sa.Column('folder_path', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_drive_folder_map_workspace', 'drive_folder_map', ['workspace_id'])
    op.create_index('ix_drive_folder_map_google_account', 'drive_folder_map', ['google_account_id'])
    op.create_index('ix_drive_folder_map_type', 'drive_folder_map', ['folder_type'])
    op.create_index('ix_drive_folder_map_project', 'drive_folder_map', ['project_id'])
    
    # Create unique constraint
    op.create_unique_constraint(
        'uq_drive_folder_map',
        'drive_folder_map',
        ['workspace_id', 'google_account_id', 'folder_type', 'project_id']
    )


def downgrade() -> None:
    op.drop_table('drive_folder_map')
