"""Workspace invites - authorized emails per workspace

Revision ID: 020_workspace_invites
Revises: 019_agency_cockpit
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '020_workspace_invites'
down_revision = '025_drive_folder_livrables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'workspace_invites',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), default='member'),
        sa.Column('invited_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('claimed', sa.Boolean(), default=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('claimed_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_workspace_invites_email', 'workspace_invites', ['email'])
    op.create_index('ix_workspace_invites_workspace_id', 'workspace_invites', ['workspace_id'])
    
    # Create unique constraint
    op.create_unique_constraint('uq_workspace_invite_email', 'workspace_invites', ['workspace_id', 'email'])


def downgrade():
    op.drop_table('workspace_invites')
