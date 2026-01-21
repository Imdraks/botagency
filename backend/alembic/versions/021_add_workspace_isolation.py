"""Add workspace_id to lead_items, collections, profiles for multi-tenant isolation

Revision ID: 021_add_workspace_isolation
Revises: 020_workspace_inbox
Create Date: 2026-01-21

This is a CRITICAL security migration that adds workspace isolation to prevent
data leakage between agencies/workspaces.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021_add_workspace_isolation'
down_revision = '020_workspace_inbox'
branch_labels = None
depends_on = None


def upgrade():
    # Add workspace_id to lead_items table
    op.add_column('lead_items', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_index('ix_lead_items_workspace_id', 'lead_items', ['workspace_id'], unique=False)
    op.create_foreign_key(
        'fk_lead_items_workspace_id',
        'lead_items', 'workspaces',
        ['workspace_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add workspace_id to collections table
    op.add_column('collections', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_index('ix_collections_workspace_id', 'collections', ['workspace_id'], unique=False)
    op.create_foreign_key(
        'fk_collections_workspace_id',
        'collections', 'workspaces',
        ['workspace_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add workspace_id to profiles table
    op.add_column('profiles', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.create_index('ix_profiles_workspace_id', 'profiles', ['workspace_id'], unique=False)
    op.create_foreign_key(
        'fk_profiles_workspace_id',
        'profiles', 'workspaces',
        ['workspace_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Remove unique constraint on profiles.name (now unique per workspace, not globally)
    op.drop_constraint('profiles_name_key', 'profiles', type_='unique')
    # Add unique constraint per workspace
    op.create_unique_constraint('uq_profiles_workspace_name', 'profiles', ['workspace_id', 'name'])


def downgrade():
    # Remove workspace isolation from profiles
    op.drop_constraint('uq_profiles_workspace_name', 'profiles', type_='unique')
    op.create_unique_constraint('profiles_name_key', 'profiles', ['name'])
    op.drop_constraint('fk_profiles_workspace_id', 'profiles', type_='foreignkey')
    op.drop_index('ix_profiles_workspace_id', table_name='profiles')
    op.drop_column('profiles', 'workspace_id')
    
    # Remove workspace isolation from collections
    op.drop_constraint('fk_collections_workspace_id', 'collections', type_='foreignkey')
    op.drop_index('ix_collections_workspace_id', table_name='collections')
    op.drop_column('collections', 'workspace_id')
    
    # Remove workspace isolation from lead_items
    op.drop_constraint('fk_lead_items_workspace_id', 'lead_items', type_='foreignkey')
    op.drop_index('ix_lead_items_workspace_id', table_name='lead_items')
    op.drop_column('lead_items', 'workspace_id')
