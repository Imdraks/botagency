"""Make activity_logs.workspace_id nullable for login events

Revision ID: 029
Revises: 028
Create Date: 2026-01-22

Login events happen before workspace selection, so workspace_id must be nullable.
"""
from alembic import op
import sqlalchemy as sa


revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade():
    # Make workspace_id nullable for activity_logs (login happens before workspace selection)
    op.alter_column('activity_logs', 'workspace_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    # Also make it nullable for audit_logs if it exists (same reason)
    conn = op.get_bind()
    audit_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'workspace_id'
        )
    """)).scalar()
    
    if audit_exists:
        op.alter_column('audit_logs', 'workspace_id',
                        existing_type=sa.Integer(),
                        nullable=True)


def downgrade():
    # Revert to non-nullable
    op.alter_column('activity_logs', 'workspace_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    conn = op.get_bind()
    audit_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'workspace_id'
        )
    """)).scalar()
    
    if audit_exists:
        op.alter_column('audit_logs', 'workspace_id',
                        existing_type=sa.Integer(),
                        nullable=False)
