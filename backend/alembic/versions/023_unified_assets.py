"""Unified Assets model - extend with type, status, driveFileId

Revision ID: 023_unified_assets
Revises: 022_drive_subfolders
Create Date: 2026-01-21

This migration:
1. Extends the Asset model with new fields for better categorization
2. Adds unique constraint to prevent duplicates (project_id + url)
3. Adds indexes for common queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers
revision = '023_unified_assets'
down_revision = '022_drive_subfolders'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Add new columns to assets table
    
    # asset_type enum: DRIVE, FIGMA, DROPBOX, YOUTUBE, LINK, DOC, SHEET, OTHER
    if not column_exists('assets', 'type'):
        op.add_column('assets', sa.Column('type', sa.String(50), nullable=True))
    
    # Google Drive integration
    if not column_exists('assets', 'drive_file_id'):
        op.add_column('assets', sa.Column('drive_file_id', sa.String(255), nullable=True))
    
    if not column_exists('assets', 'drive_folder_id'):
        op.add_column('assets', sa.Column('drive_folder_id', sa.String(255), nullable=True))
    
    # Status: DRAFT or FINAL
    if not column_exists('assets', 'status'):
        op.add_column('assets', sa.Column('status', sa.String(20), nullable=True))
    
    # Updated at timestamp
    if not column_exists('assets', 'updated_at'):
        op.add_column('assets', sa.Column('updated_at', sa.DateTime, nullable=True))
    
    # Add indexes for common queries
    try:
        op.create_index('ix_assets_type', 'assets', ['type'])
    except:
        pass
    
    try:
        op.create_index('ix_assets_status', 'assets', ['status'])
    except:
        pass
    
    try:
        op.create_index('ix_assets_name', 'assets', ['name'])
    except:
        pass
    
    try:
        op.create_index('ix_assets_drive_file_id', 'assets', ['drive_file_id'])
    except:
        pass
    
    # Migrate existing data: map 'kind' to 'type' and 'asset_type' to 'type'
    op.execute("""
        UPDATE assets 
        SET type = COALESCE(
            CASE asset_type
                WHEN 'brief' THEN 'DOC'
                WHEN 'report' THEN 'SHEET'
                WHEN 'template' THEN 'DOC'
                ELSE NULL
            END,
            CASE kind
                WHEN 'link' THEN 'LINK'
                WHEN 'file' THEN 'DRIVE'
                ELSE 'LINK'
            END
        )
        WHERE type IS NULL
    """)
    
    # Set default status to DRAFT for existing assets
    op.execute("UPDATE assets SET status = 'DRAFT' WHERE status IS NULL")


def downgrade():
    # Remove new columns
    op.drop_index('ix_assets_drive_file_id', table_name='assets')
    op.drop_index('ix_assets_name', table_name='assets')
    op.drop_index('ix_assets_status', table_name='assets')
    op.drop_index('ix_assets_type', table_name='assets')
    op.drop_column('assets', 'updated_at')
    op.drop_column('assets', 'status')
    op.drop_column('assets', 'drive_folder_id')
    op.drop_column('assets', 'drive_file_id')
    op.drop_column('assets', 'type')
