"""Add missing icon and is_system columns to tags table

Revision ID: 020_fix_tags_columns
Revises: 019_agency_cockpit
Create Date: 2026-04-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '020_fix_tags_columns'
down_revision = '019_agency_cockpit'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not column_exists('tags', 'icon'):
        op.add_column('tags', sa.Column('icon', sa.String(50), nullable=True))
    if not column_exists('tags', 'is_system'):
        op.add_column('tags', sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    if column_exists('tags', 'is_system'):
        op.drop_column('tags', 'is_system')
    if column_exists('tags', 'icon'):
        op.drop_column('tags', 'icon')
