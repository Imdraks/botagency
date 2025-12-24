"""
Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), server_default='viewer', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_superuser', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Source configs table
    op.create_table(
        'source_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('css_selector_list', sa.String(length=500), nullable=True),
        sa.Column('css_selector_item', sa.String(length=500), nullable=True),
        sa.Column('css_selector_title', sa.String(length=500), nullable=True),
        sa.Column('css_selector_description', sa.String(length=500), nullable=True),
        sa.Column('css_selector_link', sa.String(length=500), nullable=True),
        sa.Column('css_selector_date', sa.String(length=500), nullable=True),
        sa.Column('email_folder', sa.String(length=255), server_default='INBOX', nullable=True),
        sa.Column('poll_interval_minutes', sa.Integer(), server_default='60', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_polled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_source_configs_name', 'source_configs', ['name'], unique=True)
    op.create_index('ix_source_configs_source_type', 'source_configs', ['source_type'], unique=False)
    
    # Opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uid', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_config_id', sa.Integer(), nullable=True),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('source_email', sa.String(length=255), nullable=True),
        sa.Column('url_primary', sa.Text(), nullable=True),
        sa.Column('url_secondary', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='new', nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('organization_name', sa.String(length=255), nullable=True),
        sa.Column('budget_amount', sa.Float(), nullable=True),
        sa.Column('budget_currency', sa.String(length=10), server_default='EUR', nullable=True),
        sa.Column('budget_text', sa.String(length=255), nullable=True),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_date_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_date_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('score', sa.Float(), server_default='0', nullable=True),
        sa.Column('score_breakdown', sa.JSON(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('duplicate_of_id', sa.Integer(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['opportunities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_config_id'], ['source_configs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_opportunities_uid', 'opportunities', ['uid'], unique=True)
    op.create_index('ix_opportunities_status', 'opportunities', ['status'], unique=False)
    op.create_index('ix_opportunities_category', 'opportunities', ['category'], unique=False)
    op.create_index('ix_opportunities_region', 'opportunities', ['region'], unique=False)
    op.create_index('ix_opportunities_score', 'opportunities', ['score'], unique=False)
    op.create_index('ix_opportunities_deadline_at', 'opportunities', ['deadline_at'], unique=False)
    op.create_index('ix_opportunities_ingested_at', 'opportunities', ['ingested_at'], unique=False)
    
    # Opportunity tags table
    op.create_table(
        'opportunity_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_opportunity_tags_name', 'opportunity_tags', ['name'], unique=False)
    
    # Opportunity notes table
    op.create_table(
        'opportunity_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Opportunity tasks table
    op.create_table(
        'opportunity_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Ingestion runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_config_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='running', nullable=False),
        sa.Column('items_found', sa.Integer(), server_default='0', nullable=True),
        sa.Column('items_new', sa.Integer(), server_default='0', nullable=True),
        sa.Column('items_duplicate', sa.Integer(), server_default='0', nullable=True),
        sa.Column('items_error', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['source_config_id'], ['source_configs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ingestion_runs_started_at', 'ingestion_runs', ['started_at'], unique=False)
    op.create_index('ix_ingestion_runs_status', 'ingestion_runs', ['status'], unique=False)
    
    # Scoring rules table
    op.create_table(
        'scoring_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_type', sa.String(length=100), nullable=False),
        sa.Column('condition_value', sa.JSON(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='50', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scoring_rules_name', 'scoring_rules', ['name'], unique=True)
    op.create_index('ix_scoring_rules_rule_type', 'scoring_rules', ['rule_type'], unique=False)


def downgrade() -> None:
    op.drop_table('scoring_rules')
    op.drop_table('ingestion_runs')
    op.drop_table('opportunity_tasks')
    op.drop_table('opportunity_notes')
    op.drop_table('opportunity_tags')
    op.drop_table('opportunities')
    op.drop_table('source_configs')
    op.drop_table('users')
