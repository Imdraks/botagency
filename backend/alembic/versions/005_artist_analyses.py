"""Add artist analyses table

Revision ID: 005_artist_analyses
Revises: 001_initial
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_artist_analyses'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'artist_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artist_name', sa.String(255), nullable=False, index=True),
        sa.Column('real_name', sa.String(255), nullable=True),
        sa.Column('genre', sa.String(100), nullable=True),
        sa.Column('spotify_monthly_listeners', sa.Integer(), default=0),
        sa.Column('youtube_subscribers', sa.Integer(), default=0),
        sa.Column('instagram_followers', sa.Integer(), default=0),
        sa.Column('tiktok_followers', sa.Integer(), default=0),
        sa.Column('total_followers', sa.Integer(), default=0),
        sa.Column('fee_min', sa.Float(), default=0),
        sa.Column('fee_max', sa.Float(), default=0),
        sa.Column('market_tier', sa.String(50), nullable=True),
        sa.Column('popularity_score', sa.Float(), default=0),
        sa.Column('record_label', sa.String(255), nullable=True),
        sa.Column('management', sa.String(255), nullable=True),
        sa.Column('booking_agency', sa.String(255), nullable=True),
        sa.Column('booking_email', sa.String(255), nullable=True),
        sa.Column('market_trend', sa.String(50), default='stable'),
        sa.Column('confidence_score', sa.Float(), default=0),
        sa.Column('full_data', sa.JSON(), nullable=True),
        sa.Column('sources_scanned', sa.Text(), nullable=True),
        sa.Column('analyzed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, index=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_artist_analyses_artist_name', 'artist_analyses', ['artist_name'])
    op.create_index('ix_artist_analyses_created_at', 'artist_analyses', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_artist_analyses_created_at', table_name='artist_analyses')
    op.drop_index('ix_artist_analyses_artist_name', table_name='artist_analyses')
    op.drop_table('artist_analyses')
