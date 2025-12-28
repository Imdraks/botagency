"""Merge all 011 heads

Revision ID: 011c_merge_heads
Revises: 011_refonte_collectes, 011_add_whitelist
Create Date: 2024-12-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011c_merge_heads'
down_revision = ('011_refonte_collectes', '011_add_whitelist')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
