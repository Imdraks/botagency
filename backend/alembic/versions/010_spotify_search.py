"""Add spotify search tables

Revision ID: 010_spotify_search
Revises: 009_entity_brief_system
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_spotify_search'
down_revision = '009_entity_brief_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create spotify_search_jobs table
    op.create_table(
        'spotify_search_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('query', sa.String(200), nullable=False),
        sa.Column('limit', sa.Integer(), default=10),
        sa.Column('status', sa.String(20), default='QUEUED'),
        sa.Column('current_step', sa.String(20), default='SEARCH'),
        sa.Column('progress_pct', sa.Integer(), default=0),
        sa.Column('celery_task_id', sa.String(100), nullable=True),
        sa.Column('results_count', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
    )
    
    # Create spotify_search_results table
    op.create_table(
        'spotify_search_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('spotify_search_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('spotify_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('spotify_url', sa.Text(), nullable=True),
        sa.Column('followers', sa.Integer(), default=0),
        sa.Column('popularity', sa.Integer(), default=0),
        sa.Column('monthly_listeners', sa.Integer(), nullable=True),
        sa.Column('monthly_listeners_source', sa.String(20), default='estimated'),
        sa.Column('genres', postgresql.JSON(), default=list),
        sa.Column('label', sa.String(255), nullable=True),
        sa.Column('management', sa.String(255), nullable=True),
        sa.Column('social_stats', postgresql.JSON(), nullable=True),
        sa.Column('rank', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    
    # Indexes for performance
    op.create_index('ix_spotify_search_jobs_workspace_status', 'spotify_search_jobs', ['workspace_id', 'status'])
    op.create_index('ix_spotify_search_jobs_started_at', 'spotify_search_jobs', ['started_at'])
    op.create_index('ix_spotify_search_results_job_id', 'spotify_search_results', ['job_id'])


def downgrade():
    op.drop_index('ix_spotify_search_results_job_id')
    op.drop_index('ix_spotify_search_jobs_started_at')
    op.drop_index('ix_spotify_search_jobs_workspace_status')
    op.drop_table('spotify_search_results')
    op.drop_table('spotify_search_jobs')
