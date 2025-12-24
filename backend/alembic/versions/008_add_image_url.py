"""Add image_url to artist_analyses

Revision ID: 008_add_image_url
Revises: 007_ai_intelligence
Create Date: 2024-12-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_image_url'
down_revision = '007_ai_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_url column for artist photo
    op.add_column('artist_analyses', sa.Column('image_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('artist_analyses', 'image_url')
