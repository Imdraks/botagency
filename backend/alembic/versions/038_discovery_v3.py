"""Discovery V3 - Complete data model refactoring

Revision ID: 038_discovery_v3
Revises: 037
Create Date: 2026-01-26

New tables for Discovery V3:
- discovery_artists: Main artist entity with deduplication
- discovery_snapshots: Raw data storage for audit/debug
- discovery_computed_metrics: Pre-computed metrics for UI
- discovery_candidates: Materialized view for feed
- discovery_comparison_lists: Shortlists for comparison
- discovery_comparison_items: Items in shortlists
- discovery_enrichment_jobs: Job tracking for UI queue
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


# revision identifiers
revision = '038_discovery_v3'
down_revision = '037'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ================================================================
    # 1. DISCOVERY_ARTISTS - Main artist entity
    # ================================================================
    op.create_table(
        'discovery_artists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('canonical_name', sa.String(500), nullable=False),
        sa.Column('normalized_name', sa.String(500), nullable=False, index=True),
        sa.Column('viberate_url', sa.String(1000), nullable=True),
        sa.Column('spotify_artist_id', sa.String(50), nullable=True, index=True),
        sa.Column('instagram_url', sa.String(500), nullable=True),
        sa.Column('tiktok_url', sa.String(500), nullable=True),
        sa.Column('youtube_url', sa.String(500), nullable=True),
        sa.Column('image_url', sa.String(1000), nullable=True),
        sa.Column('genres', JSONB, nullable=True),  # List[str]
        sa.Column('country', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_enriched_at', sa.DateTime(), nullable=True),
        sa.Column('data_quality', sa.String(20), nullable=False, server_default='LOW'),  # HIGH | MEDIUM | LOW
        sa.Column('last_quality_reason', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
    )
    
    # Unique constraint on workspace + normalized_name to prevent duplicates
    op.create_index(
        'ix_discovery_artists_workspace_normalized',
        'discovery_artists',
        ['workspace_id', 'normalized_name'],
        unique=True
    )
    
    # ================================================================
    # 2. DISCOVERY_SNAPSHOTS - Raw data storage for audit
    # ================================================================
    op.create_table(
        'discovery_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('artist_id', UUID(as_uuid=True), sa.ForeignKey('discovery_artists.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=False),  # VIBERATE | SPOTIFY | SOCIAL
        sa.Column('fetched_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ttl_expires_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # OK | PARTIAL | FAILED
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_payload', JSONB, nullable=True),  # Compressed/stored data
        sa.Column('parser_version', sa.String(50), nullable=True),
    )
    
    op.create_index(
        'ix_discovery_snapshots_artist_source_date',
        'discovery_snapshots',
        ['artist_id', 'source', 'fetched_at'],
        postgresql_using='btree'
    )
    
    # ================================================================
    # 3. DISCOVERY_COMPUTED_METRICS - Pre-computed for UI consumption
    # ================================================================
    op.create_table(
        'discovery_computed_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('artist_id', UUID(as_uuid=True), sa.ForeignKey('discovery_artists.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        
        # Core metrics
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),  # 0-100
        sa.Column('timing_bucket', sa.String(20), nullable=False, server_default='LONG'),  # IMMINENT | 1_3M | 3_6M | 6_12M | LONG
        sa.Column('recommendation', sa.String(20), nullable=False, server_default='IGNORE'),  # BOOK | WATCHLIST | IGNORE
        
        # Drivers & Penalties
        sa.Column('drivers', JSONB, nullable=True),  # [{label, value, impact}]
        sa.Column('penalties', JSONB, nullable=True),  # [{label, value, impact}]
        
        # Time series
        sa.Column('monthly_listeners_series', JSONB, nullable=True),  # [{date, value}] 6 months
        sa.Column('velocity', sa.Float(), nullable=True),  # Growth rate
        sa.Column('acceleration', sa.Float(), nullable=True),  # Rate of change
        
        # Signals & Patterns
        sa.Column('signals', JSONB, nullable=True),  # [{type, strength, evidenceUrl, detectedAt, source}]
        sa.Column('patterns', JSONB, nullable=True),  # [{type, confidence}]
        
        # Fee estimation
        sa.Column('fee_estimate_min', sa.Integer(), nullable=True),
        sa.Column('fee_estimate_max', sa.Integer(), nullable=True),
        
        # Quality & Meta
        sa.Column('confidence_index', sa.Integer(), nullable=True),  # 0-100
        sa.Column('data_quality', sa.String(20), nullable=False, server_default='LOW'),
        sa.Column('last_updated_by_source', JSONB, nullable=True),  # {viberate: timestamp, spotify: timestamp}
        sa.Column('algo_version', sa.String(20), nullable=False, server_default='v3.0'),
        
        # Raw metrics for detailed view
        sa.Column('monthly_listeners', sa.Integer(), nullable=True),
        sa.Column('spotify_followers', sa.Integer(), nullable=True),
        sa.Column('instagram_followers', sa.Integer(), nullable=True),
        sa.Column('tiktok_followers', sa.Integer(), nullable=True),
        sa.Column('youtube_subscribers', sa.Integer(), nullable=True),
        sa.Column('total_social_followers', sa.Integer(), nullable=True),
    )
    
    # Latest computed per artist
    op.create_index(
        'ix_discovery_computed_artist_date',
        'discovery_computed_metrics',
        ['artist_id', 'computed_at'],
        postgresql_using='btree'
    )
    
    # ================================================================
    # 4. DISCOVERY_CANDIDATES - Materialized feed for Discovery page
    # ================================================================
    op.create_table(
        'discovery_candidates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('artist_id', UUID(as_uuid=True), sa.ForeignKey('discovery_artists.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('candidate_type', sa.String(20), nullable=False),  # RECOMMENDED | TRENDING
        sa.Column('rank_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('reasons', JSONB, nullable=True),  # Top 2-3 drivers for display
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ttl_expires_at', sa.DateTime(), nullable=False),
        sa.Column('segment_key', sa.String(100), nullable=True),
    )
    
    # Feed query optimization
    op.create_index(
        'ix_discovery_candidates_feed',
        'discovery_candidates',
        ['workspace_id', 'candidate_type', 'rank_score'],
        postgresql_using='btree'
    )
    
    # Unique constraint to prevent duplicate entries
    op.create_index(
        'ix_discovery_candidates_unique',
        'discovery_candidates',
        ['workspace_id', 'artist_id', 'candidate_type'],
        unique=True
    )
    
    # ================================================================
    # 5. DISCOVERY_COMPARISON_LISTS - Shortlists for comparison
    # ================================================================
    op.create_table(
        'discovery_comparison_lists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # ================================================================
    # 6. DISCOVERY_COMPARISON_ITEMS - Items in shortlists
    # ================================================================
    op.create_table(
        'discovery_comparison_items',
        sa.Column('list_id', UUID(as_uuid=True), sa.ForeignKey('discovery_comparison_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artist_id', UUID(as_uuid=True), sa.ForeignKey('discovery_artists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('list_id', 'artist_id')
    )
    
    op.create_index(
        'ix_discovery_comparison_items_list',
        'discovery_comparison_items',
        ['list_id', 'order_index']
    )
    
    # ================================================================
    # 7. DISCOVERY_ENRICHMENT_JOBS - Job tracking for UI queue
    # ================================================================
    op.create_table(
        'discovery_enrichment_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('requested_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        
        # Input
        sa.Column('input_type', sa.String(50), nullable=False),  # VIBERATE_URL | SPOTIFY_URL | NAME
        sa.Column('input_value', sa.String(1000), nullable=False),
        sa.Column('artist_id', UUID(as_uuid=True), sa.ForeignKey('discovery_artists.id', ondelete='SET NULL'), nullable=True),
        
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),  # QUEUED | RUNNING | PARTIAL | FAILED | DONE
        sa.Column('current_step', sa.String(20), nullable=True),  # MATCH | VIBERATE | SPOTIFY | COMPUTE
        sa.Column('progress_pct', sa.Integer(), nullable=False, server_default='0'),
        
        # Error handling
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        # Admin only
        sa.Column('logs_ref', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(100), nullable=True),
    )
    
    # Queue queries optimization
    op.create_index(
        'ix_discovery_jobs_workspace_status',
        'discovery_enrichment_jobs',
        ['workspace_id', 'status', 'created_at']
    )


def downgrade() -> None:
    op.drop_table('discovery_enrichment_jobs')
    op.drop_table('discovery_comparison_items')
    op.drop_table('discovery_comparison_lists')
    op.drop_table('discovery_candidates')
    op.drop_table('discovery_computed_metrics')
    op.drop_table('discovery_snapshots')
    op.drop_table('discovery_artists')
