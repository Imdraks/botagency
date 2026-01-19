"""Agency Cockpit V2 - New data models

Revision ID: 019_agency_cockpit
Revises: 018_tags_comments_favorites
Create Date: 2026-01-19

Creates:
- clients
- deals
- projects
- deliverables
- approvals
- assets
- agency_tasks
- calendar_events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019_agency_cockpit'
down_revision = '018_tags_comments_favorites'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table already exists"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    # ========================================================================
    # CLIENTS
    # ========================================================================
    if not table_exists('clients'):
        op.create_table(
            'clients',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('contacts', sa.JSON(), default=[]),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_clients_name', 'clients', ['name'])

    # ========================================================================
    # DEALS
    # ========================================================================
    if not table_exists('deals'):
        # Create enum type
        deal_status = postgresql.ENUM(
            'new', 'contacted', 'quote_sent', 'negotiation', 'won', 'lost',
            name='dealstatus',
            create_type=False
        )
        deal_status.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'deals',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=False),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('status', sa.Enum('new', 'contacted', 'quote_sent', 'negotiation', 'won', 'lost', name='dealstatus'), default='new'),
            sa.Column('value', sa.Float()),
            sa.Column('next_action_date', sa.DateTime()),
            sa.Column('last_contact_at', sa.DateTime()),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('source', sa.String(100)),
            sa.Column('tags', sa.JSON(), default=[]),
            sa.Column('notes', sa.Text()),
            sa.Column('legacy_opportunity_id', sa.Integer()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_deals_status', 'deals', ['status'])
        op.create_index('ix_deals_client_id', 'deals', ['client_id'])
        op.create_index('ix_deals_owner_id', 'deals', ['owner_id'])
        op.create_index('ix_deals_next_action_date', 'deals', ['next_action_date'])
        op.create_index('ix_deals_last_contact_at', 'deals', ['last_contact_at'])

    # ========================================================================
    # PROJECTS
    # ========================================================================
    if not table_exists('projects'):
        project_status = postgresql.ENUM(
            'active', 'blocked', 'delivered', 'archived',
            name='projectstatus',
            create_type=False
        )
        project_status.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'projects',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=False),
            sa.Column('deal_id', sa.Integer(), sa.ForeignKey('deals.id')),
            sa.Column('name', sa.String(500), nullable=False),
            sa.Column('status', sa.Enum('active', 'blocked', 'delivered', 'archived', name='projectstatus'), default='active'),
            sa.Column('deadline', sa.DateTime()),
            sa.Column('budget', sa.Float()),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('description', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_projects_status', 'projects', ['status'])
        op.create_index('ix_projects_client_id', 'projects', ['client_id'])
        op.create_index('ix_projects_deadline', 'projects', ['deadline'])

    # ========================================================================
    # DELIVERABLES
    # ========================================================================
    if not table_exists('deliverables'):
        deliverable_status = postgresql.ENUM(
            'draft', 'to_review', 'changes_requested', 'approved', 'delivered',
            name='deliverablestatus',
            create_type=False
        )
        deliverable_status.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'deliverables',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
            sa.Column('name', sa.String(500), nullable=False),
            sa.Column('type', sa.String(100)),
            sa.Column('status', sa.Enum('draft', 'to_review', 'changes_requested', 'approved', 'delivered', name='deliverablestatus'), default='draft'),
            sa.Column('due_date', sa.DateTime()),
            sa.Column('link', sa.String(1000)),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_deliverables_project_id', 'deliverables', ['project_id'])
        op.create_index('ix_deliverables_status', 'deliverables', ['status'])
        op.create_index('ix_deliverables_due_date', 'deliverables', ['due_date'])

    # ========================================================================
    # APPROVALS
    # ========================================================================
    if not table_exists('approvals'):
        approval_status = postgresql.ENUM(
            'pending', 'changes', 'approved',
            name='approvalstatus',
            create_type=False
        )
        approval_status.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'approvals',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('deliverable_id', sa.Integer(), sa.ForeignKey('deliverables.id'), nullable=False),
            sa.Column('status', sa.Enum('pending', 'changes', 'approved', name='approvalstatus'), default='pending'),
            sa.Column('feedback', sa.Text()),
            sa.Column('requested_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('decided_at', sa.DateTime()),
            sa.Column('decided_by', sa.Integer(), sa.ForeignKey('users.id')),
        )
        op.create_index('ix_approvals_deliverable_id', 'approvals', ['deliverable_id'])
        op.create_index('ix_approvals_status', 'approvals', ['status'])

    # ========================================================================
    # ASSETS
    # ========================================================================
    if not table_exists('assets'):
        asset_kind = postgresql.ENUM('link', 'file', name='assetkind', create_type=False)
        asset_kind.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'assets',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
            sa.Column('kind', sa.Enum('link', 'file', name='assetkind'), default='link'),
            sa.Column('name', sa.String(500), nullable=False),
            sa.Column('url', sa.String(2000), nullable=False),
            sa.Column('version', sa.String(50)),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        )
        op.create_index('ix_assets_project_id', 'assets', ['project_id'])
        op.create_index('ix_assets_kind', 'assets', ['kind'])

    # ========================================================================
    # AGENCY TASKS
    # ========================================================================
    if not table_exists('agency_tasks'):
        task_status = postgresql.ENUM('todo', 'doing', 'done', name='taskstatus', create_type=False)
        task_status.create(op.get_bind(), checkfirst=True)
        
        task_priority = postgresql.ENUM('low', 'medium', 'high', name='taskpriority', create_type=False)
        task_priority.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'agency_tasks',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id')),
            sa.Column('deal_id', sa.Integer(), sa.ForeignKey('deals.id')),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('status', sa.Enum('todo', 'doing', 'done', name='taskstatus'), default='todo'),
            sa.Column('priority', sa.Enum('low', 'medium', 'high', name='taskpriority'), default='medium'),
            sa.Column('due_date', sa.DateTime()),
            sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('is_auto_generated', sa.Boolean(), default=False),
            sa.Column('auto_type', sa.String(50)),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_agency_tasks_project_id', 'agency_tasks', ['project_id'])
        op.create_index('ix_agency_tasks_deal_id', 'agency_tasks', ['deal_id'])
        op.create_index('ix_agency_tasks_status', 'agency_tasks', ['status'])
        op.create_index('ix_agency_tasks_priority', 'agency_tasks', ['priority'])
        op.create_index('ix_agency_tasks_due_date', 'agency_tasks', ['due_date'])
        op.create_index('ix_agency_tasks_assignee_id', 'agency_tasks', ['assignee_id'])

    # ========================================================================
    # CALENDAR EVENTS
    # ========================================================================
    if not table_exists('calendar_events'):
        event_type = postgresql.ENUM(
            'shoot', 'delivery', 'meeting', 'deadline', 'other',
            name='calendareventtype',
            create_type=False
        )
        event_type.create(op.get_bind(), checkfirst=True)
        
        op.create_table(
            'calendar_events',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id')),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('type', sa.Enum('shoot', 'delivery', 'meeting', 'deadline', 'other', name='calendareventtype'), default='other'),
            sa.Column('start', sa.DateTime(), nullable=False),
            sa.Column('end', sa.DateTime()),
            sa.Column('all_day', sa.Boolean(), default=False),
            sa.Column('location', sa.String(500)),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_calendar_events_project_id', 'calendar_events', ['project_id'])
        op.create_index('ix_calendar_events_start', 'calendar_events', ['start'])
        op.create_index('ix_calendar_events_type', 'calendar_events', ['type'])


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('calendar_events')
    op.drop_table('agency_tasks')
    op.drop_table('assets')
    op.drop_table('approvals')
    op.drop_table('deliverables')
    op.drop_table('projects')
    op.drop_table('deals')
    op.drop_table('clients')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS calendareventtype")
    op.execute("DROP TYPE IF EXISTS taskpriority")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS assetkind")
    op.execute("DROP TYPE IF EXISTS approvalstatus")
    op.execute("DROP TYPE IF EXISTS deliverablestatus")
    op.execute("DROP TYPE IF EXISTS projectstatus")
    op.execute("DROP TYPE IF EXISTS dealstatus")
