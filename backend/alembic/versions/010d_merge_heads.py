"""Merge all 010 heads

Revision ID: 010d_merge_heads
Revises: 010_activity_logs, 010_add_ai_found, 010_dossier_system
Create Date: 2024-12-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010d_merge_heads'
down_revision = ('010_activity_logs', '010_add_ai_found', '010_dossier_system')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
