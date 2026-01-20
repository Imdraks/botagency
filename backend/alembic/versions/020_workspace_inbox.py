"""Workspace, Inbox & Google Drive integration

Revision ID: 020_workspace_inbox
Revises: 019_agency_cockpit
Create Date: 2026-01-20

Creates:
- workspaces: Multi-user workspace for team collaboration
- workspace_members: User roles within workspace
- inbox_items: Quick capture for ideas/tasks/bugs
- Extends: clients, deals, projects, deliverables with Drive/Docs IDs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '020_workspace_inbox'
down_revision = '019_agency_cockpit'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table already exists"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def enum_exists(enum_name):
    """Check if an enum type already exists"""
    bind = op.get_bind()
    result = bind.execute(sa.text(
        "SELECT 1 FROM pg_type WHERE typname = :name"
    ), {"name": enum_name})
    return result.fetchone() is not None


def upgrade():
    # ========================================================================
    # ENUMS
    # ========================================================================
    
    # Workspace member role
    if not enum_exists('workspacerole'):
        op.execute("CREATE TYPE workspacerole AS ENUM ('admin', 'member', 'viewer')")
    
    # Inbox item status
    if not enum_exists('inboxstatus'):
        op.execute("CREATE TYPE inboxstatus AS ENUM ('inbox', 'triaged', 'done', 'archived')")
    
    # Inbox item type
    if not enum_exists('inboxtype'):
        op.execute("CREATE TYPE inboxtype AS ENUM ('idea', 'request', 'bug', 'content', 'task', 'other')")

    # ========================================================================
    # WORKSPACES
    # ========================================================================
    if not table_exists('workspaces'):
        op.execute("""
            CREATE TABLE workspaces (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                owner_user_id INTEGER NOT NULL REFERENCES users(id),
                
                -- Google Drive Integration
                drive_root_folder_id VARCHAR(255),
                templates_folder_id VARCHAR(255),
                
                -- Google Templates
                brief_template_doc_id VARCHAR(255),
                report_template_sheet_id VARCHAR(255),
                devis_template_doc_id VARCHAR(255),
                
                -- Google Calendar
                calendar_id VARCHAR(255),
                
                -- Settings (JSON)
                settings JSONB DEFAULT '{}',
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_workspaces_owner_user_id ON workspaces(owner_user_id)")
        op.execute("CREATE INDEX ix_workspaces_name ON workspaces(name)")
    
    # ========================================================================
    # WORKSPACE MEMBERS
    # ========================================================================
    if not table_exists('workspace_members'):
        op.execute("""
            CREATE TABLE workspace_members (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role workspacerole NOT NULL DEFAULT 'member',
                
                -- Invite info
                invited_by INTEGER REFERENCES users(id),
                invited_at TIMESTAMP DEFAULT NOW(),
                accepted_at TIMESTAMP,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                
                -- Unique constraint
                UNIQUE(workspace_id, user_id)
            )
        """)
        op.execute("CREATE INDEX ix_workspace_members_workspace_id ON workspace_members(workspace_id)")
        op.execute("CREATE INDEX ix_workspace_members_user_id ON workspace_members(user_id)")
    
    # ========================================================================
    # INBOX ITEMS
    # ========================================================================
    if not table_exists('inbox_items'):
        op.execute("""
            CREATE TABLE inbox_items (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                created_by INTEGER NOT NULL REFERENCES users(id),
                
                -- Content
                text TEXT NOT NULL,
                link VARCHAR(2000),
                
                -- Classification
                type inboxtype DEFAULT 'other',
                tags JSONB DEFAULT '[]',
                
                -- Status
                status inboxstatus DEFAULT 'inbox',
                
                -- Due date (optional, parsed from "due:YYYY-MM-DD")
                due_date DATE,
                
                -- Triage info (when converted to Task/Deal/Project)
                triaged_to_type VARCHAR(50),  -- 'task', 'deal', 'project', 'deliverable'
                triaged_to_id INTEGER,
                triaged_at TIMESTAMP,
                triaged_by INTEGER REFERENCES users(id),
                
                -- Parsing hints
                mentioned_client VARCHAR(255),
                mentioned_project VARCHAR(255),
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        op.execute("CREATE INDEX ix_inbox_items_workspace_id ON inbox_items(workspace_id)")
        op.execute("CREATE INDEX ix_inbox_items_status ON inbox_items(status)")
        op.execute("CREATE INDEX ix_inbox_items_created_by ON inbox_items(created_by)")
        op.execute("CREATE INDEX ix_inbox_items_created_at ON inbox_items(created_at)")
        op.execute("CREATE INDEX ix_inbox_items_due_date ON inbox_items(due_date)")
    
    # ========================================================================
    # EXTEND CLIENTS TABLE - Add workspace & Drive
    # ========================================================================
    if table_exists('clients'):
        if not column_exists('clients', 'workspace_id'):
            op.execute("ALTER TABLE clients ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
            op.execute("CREATE INDEX ix_clients_workspace_id ON clients(workspace_id)")
        
        if not column_exists('clients', 'drive_folder_id'):
            op.execute("ALTER TABLE clients ADD COLUMN drive_folder_id VARCHAR(255)")
    
    # ========================================================================
    # EXTEND DEALS TABLE - Add workspace
    # ========================================================================
    if table_exists('deals'):
        if not column_exists('deals', 'workspace_id'):
            op.execute("ALTER TABLE deals ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
            op.execute("CREATE INDEX ix_deals_workspace_id ON deals(workspace_id)")
        
        if not column_exists('deals', 'drive_folder_id'):
            op.execute("ALTER TABLE deals ADD COLUMN drive_folder_id VARCHAR(255)")
        
        if not column_exists('deals', 'devis_doc_id'):
            op.execute("ALTER TABLE deals ADD COLUMN devis_doc_id VARCHAR(255)")
    
    # ========================================================================
    # EXTEND PROJECTS TABLE - Add Google Drive/Docs IDs
    # ========================================================================
    if table_exists('projects'):
        if not column_exists('projects', 'workspace_id'):
            op.execute("ALTER TABLE projects ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
            op.execute("CREATE INDEX ix_projects_workspace_id ON projects(workspace_id)")
        
        if not column_exists('projects', 'drive_folder_id'):
            op.execute("ALTER TABLE projects ADD COLUMN drive_folder_id VARCHAR(255)")
        
        if not column_exists('projects', 'brief_doc_id'):
            op.execute("ALTER TABLE projects ADD COLUMN brief_doc_id VARCHAR(255)")
        
        if not column_exists('projects', 'report_sheet_id'):
            op.execute("ALTER TABLE projects ADD COLUMN report_sheet_id VARCHAR(255)")
        
        if not column_exists('projects', 'calendar_event_id'):
            op.execute("ALTER TABLE projects ADD COLUMN calendar_event_id VARCHAR(255)")
    
    # ========================================================================
    # EXTEND DELIVERABLES TABLE - Add Drive file ID
    # ========================================================================
    if table_exists('deliverables'):
        if not column_exists('deliverables', 'drive_file_id'):
            op.execute("ALTER TABLE deliverables ADD COLUMN drive_file_id VARCHAR(255)")
        
        if not column_exists('deliverables', 'calendar_event_id'):
            op.execute("ALTER TABLE deliverables ADD COLUMN calendar_event_id VARCHAR(255)")
    
    # ========================================================================
    # EXTEND AGENCY_TASKS TABLE - Add workspace
    # ========================================================================
    if table_exists('agency_tasks'):
        if not column_exists('agency_tasks', 'workspace_id'):
            op.execute("ALTER TABLE agency_tasks ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)")
            op.execute("CREATE INDEX ix_agency_tasks_workspace_id ON agency_tasks(workspace_id)")
        
        if not column_exists('agency_tasks', 'source_inbox_id'):
            op.execute("ALTER TABLE agency_tasks ADD COLUMN source_inbox_id INTEGER REFERENCES inbox_items(id)")
    
    # ========================================================================
    # EXTEND USERS TABLE - Default workspace
    # ========================================================================
    if table_exists('users'):
        if not column_exists('users', 'default_workspace_id'):
            op.execute("ALTER TABLE users ADD COLUMN default_workspace_id INTEGER REFERENCES workspaces(id)")
        
        # Google tokens storage (encrypted in production)
        if not column_exists('users', 'google_tokens'):
            op.execute("ALTER TABLE users ADD COLUMN google_tokens JSONB")


def downgrade():
    # ========================================================================
    # REMOVE ADDED COLUMNS
    # ========================================================================
    
    # Users
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS default_workspace_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS google_tokens")
    
    # Agency tasks
    op.execute("ALTER TABLE agency_tasks DROP COLUMN IF EXISTS workspace_id")
    op.execute("ALTER TABLE agency_tasks DROP COLUMN IF EXISTS source_inbox_id")
    
    # Deliverables
    op.execute("ALTER TABLE deliverables DROP COLUMN IF EXISTS drive_file_id")
    op.execute("ALTER TABLE deliverables DROP COLUMN IF EXISTS calendar_event_id")
    
    # Projects
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS workspace_id")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS drive_folder_id")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS brief_doc_id")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS report_sheet_id")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS calendar_event_id")
    
    # Deals
    op.execute("ALTER TABLE deals DROP COLUMN IF EXISTS workspace_id")
    op.execute("ALTER TABLE deals DROP COLUMN IF EXISTS drive_folder_id")
    op.execute("ALTER TABLE deals DROP COLUMN IF EXISTS devis_doc_id")
    
    # Clients
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS workspace_id")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS drive_folder_id")
    
    # ========================================================================
    # DROP TABLES
    # ========================================================================
    op.execute("DROP TABLE IF EXISTS inbox_items CASCADE")
    op.execute("DROP TABLE IF EXISTS workspace_members CASCADE")
    op.execute("DROP TABLE IF EXISTS workspaces CASCADE")
    
    # ========================================================================
    # DROP ENUMS
    # ========================================================================
    op.execute("DROP TYPE IF EXISTS inboxtype")
    op.execute("DROP TYPE IF EXISTS inboxstatus")
    op.execute("DROP TYPE IF EXISTS workspacerole")
