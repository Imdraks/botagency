"""Add bank_metadata column to banking_connections

Revision ID: 042_add_bank_metadata_to_connections
Revises: 041_banking_connections
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '042_bank_metadata_conn'
down_revision = '041_banking_connections'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('banking_connections', sa.Column('bank_metadata', JSON, nullable=True))


def downgrade() -> None:
    op.drop_column('banking_connections', 'bank_metadata')
