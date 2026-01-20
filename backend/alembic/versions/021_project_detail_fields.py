"""Add project detail fields for Google Drive integration and blocking

Revision ID: 021_project_detail_fields
Revises: 020_workspace_inbox
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '021_project_detail_fields'
down_revision = '020_workspace_inbox'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Add Google Drive fields to projects (if not exist)
    if not column_exists('projects', 'drive_folder_id'):
        op.add_column('projects', sa.Column('drive_folder_id', sa.String(100), nullable=True))
    if not column_exists('projects', 'brief_doc_id'):
        op.add_column('projects', sa.Column('brief_doc_id', sa.String(100), nullable=True))
    if not column_exists('projects', 'report_sheet_id'):
        op.add_column('projects', sa.Column('report_sheet_id', sa.String(100), nullable=True))
    
    # Add next action fields
    if not column_exists('projects', 'next_action_text'):
        op.add_column('projects', sa.Column('next_action_text', sa.String(500), nullable=True))
    if not column_exists('projects', 'next_action_due_date'):
        op.add_column('projects', sa.Column('next_action_due_date', sa.DateTime(), nullable=True))
    
    # Add blocked reason
    if not column_exists('projects', 'blocked_reason'):
        op.add_column('projects', sa.Column('blocked_reason', sa.String(500), nullable=True))
    
    # Add project activity logs table
    if not table_exists('project_activity_logs'):
        op.create_table(
            'project_activity_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
            sa.Column('message', sa.String(1000), nullable=False),
            sa.Column('activity_type', sa.String(50), nullable=True),  # creation, update, validation, delivery, comment
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        )
        op.create_index('ix_project_activity_logs_project_id', 'project_activity_logs', ['project_id'])
        op.create_index('ix_project_activity_logs_created_at', 'project_activity_logs', ['created_at'])
    
    # Add drive_file_id to deliverables
    if not column_exists('deliverables', 'drive_file_id'):
        op.add_column('deliverables', sa.Column('drive_file_id', sa.String(100), nullable=True))
    
    # Add asset_type to assets for template identification
    if not column_exists('assets', 'asset_type'):
        op.add_column('assets', sa.Column('asset_type', sa.String(50), nullable=True))  # brief, report, template, other


def downgrade() -> None:
    op.drop_column('assets', 'asset_type')
    op.drop_column('deliverables', 'drive_file_id')
    
    op.drop_index('ix_project_activity_logs_created_at', 'project_activity_logs')
    op.drop_index('ix_project_activity_logs_project_id', 'project_activity_logs')
    op.drop_table('project_activity_logs')
    
    op.drop_column('projects', 'blocked_reason')
    op.drop_column('projects', 'next_action_due_date')
    op.drop_column('projects', 'next_action_text')
    op.drop_column('projects', 'report_sheet_id')
    op.drop_column('projects', 'brief_doc_id')
    op.drop_column('projects', 'drive_folder_id')
