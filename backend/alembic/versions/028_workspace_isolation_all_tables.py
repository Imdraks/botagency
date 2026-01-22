"""Add workspace_id to all tables for complete multi-tenancy isolation

Revision ID: 028
Revises: 027_add_workspace_isolation
Create Date: 2026-01-22

Each workspace is a complete sandbox - no data shared between workspaces.
"""
from alembic import op
import sqlalchemy as sa


revision = '028'
down_revision = '027_add_workspace_isolation'
branch_labels = None
depends_on = None


# Tables that need workspace_id added
TABLES_TO_ADD_WORKSPACE = [
    'entities',           # Artistes
    'dossiers',           # Dossiers
    'dossiers_v2',        # Dossiers v2
    'opportunities',      # Leads/Opportunities
    'daily_shortlists',   # Daily Picks
    'assets',             # Assets
    'calendar_events',    # Calendrier
    'briefs',             # Briefs
    'contacts',           # Contacts
    'documents',          # Documents
    'favorites',          # Favoris
    'tags',               # Tags
    'scoring_rules',      # Règles de scoring
    'source_configs',     # Sources
    'opportunity_tags',   # Tags d'opportunités
    'opportunity_clusters', # Clusters
    'extracts',           # Extraits
    'audit_logs',         # Logs d'audit
    'activity_logs',      # Logs d'activité
]


def upgrade():
    conn = op.get_bind()
    
    # Get first workspace id for migration
    result = conn.execute(sa.text("SELECT id FROM workspaces ORDER BY id LIMIT 1"))
    row = result.fetchone()
    default_workspace_id = row[0] if row else 1
    
    for table in TABLES_TO_ADD_WORKSPACE:
        # Check if table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table}'
            )
        """)).scalar()
        
        if not table_exists:
            print(f"Table {table} does not exist, skipping...")
            continue
            
        # Check if column already exists
        column_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'workspace_id'
            )
        """)).scalar()
        
        if column_exists:
            print(f"Column workspace_id already exists in {table}, skipping...")
            continue
        
        print(f"Adding workspace_id to {table}...")
        
        # Add column as nullable first
        op.add_column(table, sa.Column('workspace_id', sa.Integer(), nullable=True))
        
        # Update existing rows with default workspace
        op.execute(f"UPDATE {table} SET workspace_id = {default_workspace_id} WHERE workspace_id IS NULL")
        
        # Create foreign key (with unique constraint name)
        try:
            op.create_foreign_key(
                f'fk_{table}_workspace_id',
                table, 'workspaces',
                ['workspace_id'], ['id']
            )
        except Exception as e:
            print(f"Could not create FK for {table}: {e}")
        
        # Create index for performance
        try:
            op.create_index(f'ix_{table}_workspace_id', table, ['workspace_id'])
        except Exception as e:
            print(f"Could not create index for {table}: {e}")
        
        # Make non-nullable (only if there's data or table is empty)
        try:
            op.alter_column(table, 'workspace_id', nullable=False)
        except Exception as e:
            print(f"Could not make {table}.workspace_id non-nullable: {e}")


def downgrade():
    conn = op.get_bind()
    
    for table in reversed(TABLES_TO_ADD_WORKSPACE):
        # Check if table exists
        table_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table}'
            )
        """)).scalar()
        
        if not table_exists:
            continue
            
        # Check if column exists
        column_exists = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'workspace_id'
            )
        """)).scalar()
        
        if not column_exists:
            continue
            
        try:
            op.drop_index(f'ix_{table}_workspace_id', table_name=table)
        except:
            pass
            
        try:
            op.drop_constraint(f'fk_{table}_workspace_id', table, type_='foreignkey')
        except:
            pass
            
        try:
            op.drop_column(table, 'workspace_id')
        except:
            pass
