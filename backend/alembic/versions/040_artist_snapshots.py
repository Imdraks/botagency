"""Artist Snapshots for Predictions

Revision ID: 040_artist_snapshots
Revises: 039_spotify_search
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040_artist_snapshots'
down_revision = '039_spotify_search'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create artist_snapshots table
    op.create_table(
        'artist_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artist_name', sa.String(255), nullable=False),
        sa.Column('artist_name_normalized', sa.String(255), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        
        # Spotify metrics
        sa.Column('spotify_monthly_listeners', sa.Integer(), nullable=True),
        sa.Column('spotify_followers', sa.Integer(), nullable=True),
        sa.Column('spotify_popularity', sa.Integer(), nullable=True),
        
        # TikTok metrics
        sa.Column('tiktok_followers', sa.Integer(), nullable=True),
        sa.Column('tiktok_likes', sa.Integer(), nullable=True),
        
        # YouTube metrics
        sa.Column('youtube_subscribers', sa.Integer(), nullable=True),
        sa.Column('youtube_views_30d', sa.Integer(), nullable=True),
        sa.Column('youtube_total_views', sa.Integer(), nullable=True),
        
        # Instagram metrics
        sa.Column('instagram_followers', sa.Integer(), nullable=True),
        
        # Concert metrics
        sa.Column('concerts_next_30d', sa.Integer(), default=0),
        sa.Column('concerts_next_90d', sa.Integer(), default=0),
        
        # Data quality
        sa.Column('source_quality_score', sa.Float(), default=50.0),
        sa.Column('sources_used', sa.String(500), nullable=True),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_artist_snapshots_id', 'artist_snapshots', ['id'])
    op.create_index('ix_artist_snapshots_artist_name', 'artist_snapshots', ['artist_name'])
    op.create_index('ix_artist_snapshots_artist_name_normalized', 'artist_snapshots', ['artist_name_normalized'])
    op.create_index('ix_artist_snapshots_workspace_id', 'artist_snapshots', ['workspace_id'])
    op.create_index('ix_artist_snapshots_snapshot_date', 'artist_snapshots', ['snapshot_date'])
    op.create_index('ix_artist_snapshots_artist_date', 'artist_snapshots', ['artist_name_normalized', 'snapshot_date'])
    op.create_index('ix_artist_snapshots_workspace_artist', 'artist_snapshots', ['workspace_id', 'artist_name_normalized'])


def downgrade() -> None:
    op.drop_index('ix_artist_snapshots_workspace_artist', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_artist_date', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_snapshot_date', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_workspace_id', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_artist_name_normalized', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_artist_name', 'artist_snapshots')
    op.drop_index('ix_artist_snapshots_id', 'artist_snapshots')
    op.drop_table('artist_snapshots')
