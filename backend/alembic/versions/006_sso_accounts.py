"""Add SSO accounts table for Google/Apple authentication

Revision ID: 006_sso_accounts
Revises: 005_artist_analyses
Create Date: 2024-12-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '006_sso_accounts'
down_revision = '005_artist_analyses'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounts table for SSO providers
    op.create_table(
        'accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),  # 'google' | 'apple' | 'credentials'
        sa.Column('provider_account_id', sa.String(255), nullable=False),  # OIDC 'sub' claim
        sa.Column('email', sa.String(255), nullable=True),  # Email from provider (may be masked for Apple)
        sa.Column('email_verified', sa.Boolean, default=False),
        sa.Column('access_token', sa.Text, nullable=True),  # Encrypted if stored
        sa.Column('refresh_token', sa.Text, nullable=True),  # Encrypted if stored
        sa.Column('id_token', sa.Text, nullable=True),  # JWT from OIDC
        sa.Column('expires_at', sa.BigInteger, nullable=True),  # Token expiry timestamp
        sa.Column('token_type', sa.String(50), nullable=True),
        sa.Column('scope', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )
    
    # Unique constraint: one provider account per provider
    op.create_unique_constraint(
        'uq_accounts_provider_account', 
        'accounts', 
        ['provider', 'provider_account_id']
    )
    
    # Index for faster lookups
    op.create_index('ix_accounts_user_id', 'accounts', ['user_id'])
    op.create_index('ix_accounts_provider', 'accounts', ['provider'])
    
    # Make hashed_password nullable in users table (SSO users don't have passwords)
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Add auth_provider column to track primary auth method
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=True, server_default='credentials'))
    
    # Add avatar_url for SSO profile pictures
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'auth_provider')
    op.alter_column('users', 'hashed_password', nullable=False)
    op.drop_index('ix_accounts_provider', 'accounts')
    op.drop_index('ix_accounts_user_id', 'accounts')
    op.drop_constraint('uq_accounts_provider_account', 'accounts')
    op.drop_table('accounts')
