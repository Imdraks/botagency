"""Add crm_client_id to billing_clients for CRM sync

Revision ID: 035_billing_crm_sync
Revises: 034_drive_folder_map
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa

revision = '035_billing_crm_sync'
down_revision = '034_drive_folder_map'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # Add crm_client_id to billing_clients
    if not column_exists('billing_clients', 'crm_client_id'):
        op.add_column('billing_clients', sa.Column('crm_client_id', sa.Integer(), nullable=True))
        op.create_index('ix_billing_clients_crm_client_id', 'billing_clients', ['crm_client_id'])
        # Add foreign key if clients table exists
        try:
            op.create_foreign_key(
                'fk_billing_clients_crm_client',
                'billing_clients', 'clients',
                ['crm_client_id'], ['id'],
                ondelete='SET NULL'
            )
        except Exception:
            pass  # FK may fail if clients table doesn't exist


def downgrade():
    # Remove crm_client_id from billing_clients
    try:
        op.drop_constraint('fk_billing_clients_crm_client', 'billing_clients', type_='foreignkey')
    except Exception:
        pass
    
    if column_exists('billing_clients', 'crm_client_id'):
        op.drop_index('ix_billing_clients_crm_client_id', 'billing_clients')
        op.drop_column('billing_clients', 'crm_client_id')
