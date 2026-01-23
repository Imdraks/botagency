"""Subscription Plans & Packs System

Revision ID: 031_subscription_plans
Revises: 030_artist_workspace
Create Date: 2026-01-23

Creates:
- Add plan and enabled_packs to workspaces
- subscription_history: Track plan changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '031_subscription_plans'
down_revision = '030_artist_workspace'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = :table AND column_name = :column
        )
    """), {"table": table_name, "column": column_name})
    return result.scalar()


def table_exists(table_name):
    """Check if a table already exists"""
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = :table
        )
    """), {"table": table_name})
    return result.scalar()


def upgrade():
    # ========================================================================
    # ADD SUBSCRIPTION FIELDS TO WORKSPACES
    # ========================================================================
    
    # Plan: mini, standard, premium
    if not column_exists('workspaces', 'plan'):
        op.add_column('workspaces', sa.Column('plan', sa.String(20), server_default='standard', nullable=False))
    
    # Enabled packs as JSON array
    # Default for STANDARD: ["core", "clients", "leads", "talents"]
    if not column_exists('workspaces', 'enabled_packs'):
        op.add_column('workspaces', sa.Column(
            'enabled_packs', 
            postgresql.JSONB, 
            server_default='["core", "clients", "leads", "talents"]',
            nullable=False
        ))
    
    # Add-ons as JSON array (e.g., ["radar_business"])
    if not column_exists('workspaces', 'addons'):
        op.add_column('workspaces', sa.Column(
            'addons', 
            postgresql.JSONB, 
            server_default='[]',
            nullable=False
        ))
    
    # Seat limits
    if not column_exists('workspaces', 'max_seats'):
        op.add_column('workspaces', sa.Column('max_seats', sa.Integer, server_default='10', nullable=False))
    
    # Billing info (Stripe customer ID etc.)
    if not column_exists('workspaces', 'stripe_customer_id'):
        op.add_column('workspaces', sa.Column('stripe_customer_id', sa.String(255)))
    
    if not column_exists('workspaces', 'stripe_subscription_id'):
        op.add_column('workspaces', sa.Column('stripe_subscription_id', sa.String(255)))
    
    if not column_exists('workspaces', 'billing_email'):
        op.add_column('workspaces', sa.Column('billing_email', sa.String(255)))
    
    if not column_exists('workspaces', 'plan_expires_at'):
        op.add_column('workspaces', sa.Column('plan_expires_at', sa.DateTime))
    
    # ========================================================================
    # SUBSCRIPTION HISTORY (for audit trail)
    # ========================================================================
    if not table_exists('subscription_history'):
        op.execute("""
            CREATE TABLE subscription_history (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                
                -- What changed
                action VARCHAR(50) NOT NULL,  -- 'plan_change', 'addon_add', 'addon_remove', 'seats_change'
                old_value JSONB,
                new_value JSONB,
                
                -- Who & when
                changed_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT NOW(),
                
                -- Notes
                reason VARCHAR(500)
            )
        """)
        op.execute("CREATE INDEX ix_subscription_history_workspace ON subscription_history(workspace_id)")
        op.execute("CREATE INDEX ix_subscription_history_created ON subscription_history(created_at)")


def downgrade():
    # Drop subscription_history
    op.execute("DROP TABLE IF EXISTS subscription_history CASCADE")
    
    # Remove columns from workspaces
    op.drop_column('workspaces', 'plan') if column_exists('workspaces', 'plan') else None
    op.drop_column('workspaces', 'enabled_packs') if column_exists('workspaces', 'enabled_packs') else None
    op.drop_column('workspaces', 'addons') if column_exists('workspaces', 'addons') else None
    op.drop_column('workspaces', 'max_seats') if column_exists('workspaces', 'max_seats') else None
    op.drop_column('workspaces', 'stripe_customer_id') if column_exists('workspaces', 'stripe_customer_id') else None
    op.drop_column('workspaces', 'stripe_subscription_id') if column_exists('workspaces', 'stripe_subscription_id') else None
    op.drop_column('workspaces', 'billing_email') if column_exists('workspaces', 'billing_email') else None
    op.drop_column('workspaces', 'plan_expires_at') if column_exists('workspaces', 'plan_expires_at') else None
