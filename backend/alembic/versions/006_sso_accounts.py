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
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'accounts' not in inspector.get_table_names():
        # Create accounts table for SSO providers
        # Note: user_id is Integer to match users.id type
        op.create_table(
            'accounts',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
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
    
    # Check existing columns in users table
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Make hashed_password nullable in users table (SSO users don't have passwords)
    # Only if not already nullable
    
    # Add auth_provider column to track primary auth method
    if 'auth_provider' not in existing_columns:
        op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=True, server_default='credentials'))
    
    # Add avatar_url for SSO profile pictures
    if 'avatar_url' not in existing_columns:
        op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'auth_provider')
    op.alter_column('users', 'hashed_password', nullable=False)
    op.drop_index('ix_accounts_provider', 'accounts')
    op.drop_index('ix_accounts_user_id', 'accounts')
    op.drop_constraint('uq_accounts_provider_account', 'accounts')
    op.drop_table('accounts')
