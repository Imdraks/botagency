"""Add contact and banking fields to billing_clients

Revision ID: 036
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '036_billing_client_extended_fields'
down_revision = '035_billing_crm_sync'
branch_labels = None
depends_on = None


def upgrade():
    # Add contact person fields
    op.add_column('billing_clients', sa.Column('contact_first_name', sa.String(100), nullable=True))
    op.add_column('billing_clients', sa.Column('contact_last_name', sa.String(100), nullable=True))
    op.add_column('billing_clients', sa.Column('contact_email', sa.String(255), nullable=True))
    op.add_column('billing_clients', sa.Column('contact_phone', sa.String(50), nullable=True))
    op.add_column('billing_clients', sa.Column('contact_role', sa.String(100), nullable=True))
    
    # Add banking info fields (IBAN encrypted for security)
    op.add_column('billing_clients', sa.Column('iban_encrypted', sa.String(500), nullable=True))
    op.add_column('billing_clients', sa.Column('bic', sa.String(20), nullable=True))
    op.add_column('billing_clients', sa.Column('bank_name', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('billing_clients', 'bank_name')
    op.drop_column('billing_clients', 'bic')
    op.drop_column('billing_clients', 'iban_encrypted')
    op.drop_column('billing_clients', 'contact_role')
    op.drop_column('billing_clients', 'contact_phone')
    op.drop_column('billing_clients', 'contact_email')
    op.drop_column('billing_clients', 'contact_last_name')
    op.drop_column('billing_clients', 'contact_first_name')
