"""Add performance indexes

Revision ID: 014_performance_indexes
Revises: 013_radar_harvest_reports
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '014_performance_indexes'
down_revision = '013_radar_harvest_reports'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check and create indexes only if they don't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Helper function to check if index exists
    def index_exists(table_name, index_name):
        try:
            indexes = inspector.get_indexes(table_name)
            return any(idx['name'] == index_name for idx in indexes)
        except Exception:
            return True  # Skip if table doesn't exist
    
    # Helper function to check if table exists
    def table_exists(table_name):
        return table_name in inspector.get_table_names()
    
    # Opportunities table indexes for common queries
    if table_exists('opportunities'):
        if not index_exists('opportunities', 'ix_opportunities_status_score'):
            op.create_index(
                'ix_opportunities_status_score',
                'opportunities',
                ['status', 'score'],
                postgresql_using='btree'
            )
        
        if not index_exists('opportunities', 'ix_opportunities_deadline_at'):
            op.create_index(
                'ix_opportunities_deadline_at',
                'opportunities',
                ['deadline_at'],
                postgresql_where=sa.text('deadline_at IS NOT NULL')
            )
        
        if not index_exists('opportunities', 'ix_opportunities_created_at'):
            op.create_index(
                'ix_opportunities_created_at',
                'opportunities',
                ['created_at'],
                postgresql_using='btree'
            )
        
        if not index_exists('opportunities', 'ix_opportunities_category'):
            op.create_index(
                'ix_opportunities_category',
                'opportunities',
                ['category'],
                postgresql_using='btree'
            )
        
        # Composite index for dashboard queries
        if not index_exists('opportunities', 'ix_opportunities_status_deadline'):
            op.create_index(
                'ix_opportunities_status_deadline',
                'opportunities',
                ['status', 'deadline_at'],
                postgresql_using='btree'
            )
    
    # Source health table indexes
    if table_exists('source_health'):
        if not index_exists('source_health', 'ix_source_health_source_date'):
            op.create_index(
                'ix_source_health_source_date',
                'source_health',
                ['source_id', 'date'],
                postgresql_using='btree'
            )
    
    # Activity logs index for admin queries
    if table_exists('activity_logs'):
        if not index_exists('activity_logs', 'ix_activity_logs_created_at'):
            op.create_index(
                'ix_activity_logs_created_at',
                'activity_logs',
                ['created_at'],
                postgresql_using='btree'
            )
    
    # Profiles index - active profiles
    if table_exists('profiles'):
        if not index_exists('profiles', 'ix_profiles_is_active'):
            op.create_index(
                'ix_profiles_is_active',
                'profiles',
                ['is_active'],
                postgresql_using='btree'
            )
    
    # Shortlists index for daily queries (only if table exists)
    if table_exists('shortlists'):
        if not index_exists('shortlists', 'ix_shortlists_profile_date'):
            op.create_index(
                'ix_shortlists_profile_date',
                'shortlists',
                ['profile_id', 'date'],
                postgresql_using='btree'
            )


def downgrade() -> None:
    # Drop all created indexes
    indexes_to_drop = [
        ('opportunities', 'ix_opportunities_status_score'),
        ('opportunities', 'ix_opportunities_deadline_at'),
        ('opportunities', 'ix_opportunities_created_at'),
        ('opportunities', 'ix_opportunities_category'),
        ('opportunities', 'ix_opportunities_status_deadline'),
        ('source_health', 'ix_source_health_source_date'),
        ('activity_logs', 'ix_activity_logs_created_at'),
        ('profiles', 'ix_profiles_is_active'),
        ('shortlists', 'ix_shortlists_profile_date'),
    ]
    
    for table, index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, table_name=table)
        except Exception:
            pass  # Index might not exist
