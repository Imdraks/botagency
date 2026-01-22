"""add workspace_id to artist_analyses

Revision ID: 030_artist_workspace
Revises: 029
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030_artist_workspace'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade():
    # Add workspace_id column to artist_analyses
    op.add_column('artist_analyses', sa.Column('workspace_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_artist_analyses_workspace_id',
        'artist_analyses', 'workspaces',
        ['workspace_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create index for performance
    op.create_index('ix_artist_analyses_workspace_id', 'artist_analyses', ['workspace_id'])


def downgrade():
    op.drop_index('ix_artist_analyses_workspace_id', table_name='artist_analyses')
    op.drop_constraint('fk_artist_analyses_workspace_id', 'artist_analyses', type_='foreignkey')
    op.drop_column('artist_analyses', 'workspace_id')
