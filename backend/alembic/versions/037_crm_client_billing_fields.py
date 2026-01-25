"""Add billing fields to CRM clients

Revision ID: 037
"""
from alembic import op
import sqlalchemy as sa


revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade():
    # Add address fields
    op.add_column('clients', sa.Column('address_line1', sa.String(255), nullable=True))
    op.add_column('clients', sa.Column('address_line2', sa.String(255), nullable=True))
    op.add_column('clients', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('clients', sa.Column('postal_code', sa.String(20), nullable=True))
    op.add_column('clients', sa.Column('country', sa.String(100), nullable=True, server_default='France'))
    
    # Add legal info fields
    op.add_column('clients', sa.Column('siret', sa.String(20), nullable=True))
    op.add_column('clients', sa.Column('vat_number', sa.String(30), nullable=True))


def downgrade():
    op.drop_column('clients', 'vat_number')
    op.drop_column('clients', 'siret')
    op.drop_column('clients', 'country')
    op.drop_column('clients', 'postal_code')
    op.drop_column('clients', 'city')
    op.drop_column('clients', 'address_line2')
    op.drop_column('clients', 'address_line1')
