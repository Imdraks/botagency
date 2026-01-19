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


def enum_exists(enum_name):
    """Check if an enum type already exists"""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM pg_type WHERE typname = :name"
    ), {"name": enum_name})
    return result.fetchone() is not None


def upgrade():
    # ========================================================================
    # CREATE ENUM TYPES FIRST (using raw SQL with IF NOT EXISTS equivalent)
    # ========================================================================
    
    # dealstatus
    if not enum_exists('dealstatus'):
        op.execute("CREATE TYPE dealstatus AS ENUM ('new', 'contacted', 'quote_sent', 'negotiation', 'won', 'lost')")
    
    # projectstatus
    if not enum_exists('projectstatus'):
        op.execute("CREATE TYPE projectstatus AS ENUM ('active', 'blocked', 'delivered', 'archived')")
    
    # deliverablestatus
    if not enum_exists('deliverablestatus'):
        op.execute("CREATE TYPE deliverablestatus AS ENUM ('draft', 'to_review', 'changes_requested', 'approved', 'delivered')")
    
    # approvalstatus
    if not enum_exists('approvalstatus'):
        op.execute("CREATE TYPE approvalstatus AS ENUM ('pending', 'changes', 'approved')")
    
    # assetkind
    if not enum_exists('assetkind'):
        op.execute("CREATE TYPE assetkind AS ENUM ('link', 'file')")
    
    # taskstatus
    if not enum_exists('taskstatus'):
        op.execute("CREATE TYPE taskstatus AS ENUM ('todo', 'doing', 'done')")
    
    # taskpriority
    if not enum_exists('taskpriority'):
        op.execute("CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high')")
    
    # calendareventtype
    if not enum_exists('calendareventtype'):
        op.execute("CREATE TYPE calendareventtype AS ENUM ('shoot', 'delivery', 'meeting', 'deadline', 'other')")

    # ========================================================================
    # CLIENTS
    # ========================================================================
    if not table_exists('clients'):
        op.execute("""
            CREATE TABLE clients (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                contacts JSONB DEFAULT '[]',
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_clients_name ON clients(name)")

    # ========================================================================
    # DEALS
    # ========================================================================
    if not table_exists('deals'):
        op.execute("""
            CREATE TABLE deals (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                title VARCHAR(500) NOT NULL,
                status dealstatus DEFAULT 'new',
                value FLOAT,
                next_action_date TIMESTAMP,
                last_contact_at TIMESTAMP,
                owner_id INTEGER REFERENCES users(id),
                source VARCHAR(100),
                tags JSONB DEFAULT '[]',
                notes TEXT,
                legacy_opportunity_id INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_deals_status ON deals(status)")
        op.execute("CREATE INDEX ix_deals_client_id ON deals(client_id)")
        op.execute("CREATE INDEX ix_deals_owner_id ON deals(owner_id)")
        op.execute("CREATE INDEX ix_deals_next_action_date ON deals(next_action_date)")
        op.execute("CREATE INDEX ix_deals_last_contact_at ON deals(last_contact_at)")

    # ========================================================================
    # PROJECTS
    # ========================================================================
    if not table_exists('projects'):
        op.execute("""
            CREATE TABLE projects (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                deal_id INTEGER REFERENCES deals(id),
                name VARCHAR(500) NOT NULL,
                status projectstatus DEFAULT 'active',
                deadline TIMESTAMP,
                budget FLOAT,
                owner_id INTEGER REFERENCES users(id),
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_projects_status ON projects(status)")
        op.execute("CREATE INDEX ix_projects_client_id ON projects(client_id)")
        op.execute("CREATE INDEX ix_projects_deadline ON projects(deadline)")

    # ========================================================================
    # DELIVERABLES
    # ========================================================================
    if not table_exists('deliverables'):
        op.execute("""
            CREATE TABLE deliverables (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                name VARCHAR(500) NOT NULL,
                type VARCHAR(100),
                status deliverablestatus DEFAULT 'draft',
                due_date TIMESTAMP,
                link VARCHAR(1000),
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_deliverables_project_id ON deliverables(project_id)")
        op.execute("CREATE INDEX ix_deliverables_status ON deliverables(status)")
        op.execute("CREATE INDEX ix_deliverables_due_date ON deliverables(due_date)")

    # ========================================================================
    # APPROVALS
    # ========================================================================
    if not table_exists('approvals'):
        op.execute("""
            CREATE TABLE approvals (
                id SERIAL PRIMARY KEY,
                deliverable_id INTEGER NOT NULL REFERENCES deliverables(id),
                status approvalstatus DEFAULT 'pending',
                feedback TEXT,
                requested_at TIMESTAMP DEFAULT NOW(),
                decided_at TIMESTAMP,
                decided_by INTEGER REFERENCES users(id)
            )
        """)
        op.execute("CREATE INDEX ix_approvals_deliverable_id ON approvals(deliverable_id)")
        op.execute("CREATE INDEX ix_approvals_status ON approvals(status)")

    # ========================================================================
    # ASSETS
    # ========================================================================
    if not table_exists('assets'):
        op.execute("""
            CREATE TABLE assets (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                kind assetkind DEFAULT 'link',
                name VARCHAR(500) NOT NULL,
                url VARCHAR(2000) NOT NULL,
                version VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                created_by INTEGER REFERENCES users(id)
            )
        """)
        op.execute("CREATE INDEX ix_assets_project_id ON assets(project_id)")
        op.execute("CREATE INDEX ix_assets_kind ON assets(kind)")

    # ========================================================================
    # AGENCY TASKS
    # ========================================================================
    if not table_exists('agency_tasks'):
        op.execute("""
            CREATE TABLE agency_tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                deal_id INTEGER REFERENCES deals(id),
                title VARCHAR(500) NOT NULL,
                description TEXT,
                status taskstatus DEFAULT 'todo',
                priority taskpriority DEFAULT 'medium',
                due_date TIMESTAMP,
                assignee_id INTEGER REFERENCES users(id),
                is_auto_generated BOOLEAN DEFAULT FALSE,
                auto_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_agency_tasks_project_id ON agency_tasks(project_id)")
        op.execute("CREATE INDEX ix_agency_tasks_deal_id ON agency_tasks(deal_id)")
        op.execute("CREATE INDEX ix_agency_tasks_status ON agency_tasks(status)")
        op.execute("CREATE INDEX ix_agency_tasks_priority ON agency_tasks(priority)")
        op.execute("CREATE INDEX ix_agency_tasks_due_date ON agency_tasks(due_date)")
        op.execute("CREATE INDEX ix_agency_tasks_assignee_id ON agency_tasks(assignee_id)")

    # ========================================================================
    # CALENDAR EVENTS
    # ========================================================================
    if not table_exists('calendar_events'):
        op.execute("""
            CREATE TABLE calendar_events (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                title VARCHAR(500) NOT NULL,
                type calendareventtype DEFAULT 'other',
                start TIMESTAMP NOT NULL,
                "end" TIMESTAMP,
                all_day BOOLEAN DEFAULT FALSE,
                location VARCHAR(500),
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_calendar_events_project_id ON calendar_events(project_id)")
        op.execute("CREATE INDEX ix_calendar_events_start ON calendar_events(start)")
        op.execute("CREATE INDEX ix_calendar_events_type ON calendar_events(type)")


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.execute("DROP TABLE IF EXISTS calendar_events CASCADE")
    op.execute("DROP TABLE IF EXISTS agency_tasks CASCADE")
    op.execute("DROP TABLE IF EXISTS assets CASCADE")
    op.execute("DROP TABLE IF EXISTS approvals CASCADE")
    op.execute("DROP TABLE IF EXISTS deliverables CASCADE")
    op.execute("DROP TABLE IF EXISTS projects CASCADE")
    op.execute("DROP TABLE IF EXISTS deals CASCADE")
    op.execute("DROP TABLE IF EXISTS clients CASCADE")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS calendareventtype CASCADE")
    op.execute("DROP TYPE IF EXISTS taskpriority CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS assetkind CASCADE")
    op.execute("DROP TYPE IF EXISTS approvalstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS deliverablestatus CASCADE")
    op.execute("DROP TYPE IF EXISTS projectstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS dealstatus CASCADE")
