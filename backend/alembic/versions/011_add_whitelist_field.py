"""Add is_whitelisted field to users

Revision ID: 011_add_whitelist
Revises: 010_add_ai_found
Create Date: 2025-12-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_add_whitelist'
down_revision = '010d_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_whitelisted column with default False
    op.add_column('users', sa.Column('is_whitelisted', sa.Boolean(), nullable=True, server_default='false'))
    
    # Set existing superusers and active users as whitelisted
    op.execute("UPDATE users SET is_whitelisted = true WHERE is_superuser = true")
    op.execute("UPDATE users SET is_whitelisted = true WHERE is_active = true")


def downgrade():
    op.drop_column('users', 'is_whitelisted')
