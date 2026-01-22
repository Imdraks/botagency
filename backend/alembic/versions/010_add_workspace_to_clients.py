"""Add workspace_id to clients for multi-tenancy

Revision ID: 010
Revises: 009
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009_entity_brief_system'
branch_labels = None
depends_on = None


def upgrade():
    # Add workspace_id column - nullable first for existing data
    op.add_column('clients', sa.Column('workspace_id', sa.Integer(), nullable=True))
    
    # Create foreign key
    op.create_foreign_key(
        'fk_clients_workspace_id',
        'clients', 'workspaces',
        ['workspace_id'], ['id']
    )
    
    # Create index for performance
    op.create_index('ix_clients_workspace_id', 'clients', ['workspace_id'])
    
    # Migrate existing data: assign all existing clients to workspace 1 (or first workspace)
    # This is a data migration - adjust workspace_id as needed
    op.execute("""
        UPDATE clients 
        SET workspace_id = (SELECT id FROM workspaces ORDER BY id LIMIT 1)
        WHERE workspace_id IS NULL
    """)
    
    # Now make it non-nullable
    op.alter_column('clients', 'workspace_id', nullable=False)


def downgrade():
    op.drop_index('ix_clients_workspace_id', table_name='clients')
    op.drop_constraint('fk_clients_workspace_id', 'clients', type_='foreignkey')
    op.drop_column('clients', 'workspace_id')
