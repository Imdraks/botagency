"""Add tags, comments, and favorites tables

Revision ID: 018_tags_comments_favorites
Revises: 017_audit_logs
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '018_tags_comments_favorites'
down_revision = '017_audit_logs'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Create tags table
    if not table_exists('tags'):
        op.create_table(
            'tags',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(50), nullable=False),
            sa.Column('color', sa.String(20), nullable=False, server_default='blue'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', 'user_id', name='uq_tag_name_user')
        )
        op.create_index('ix_tags_user_id', 'tags', ['user_id'])
        op.create_index('ix_tags_name', 'tags', ['name'])

    # Create opportunity_tags association table
    if not table_exists('opportunity_tags'):
        op.create_table(
            'opportunity_tags',
            sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('opportunity_id', 'tag_id')
        )
        op.create_index('ix_opportunity_tags_opportunity_id', 'opportunity_tags', ['opportunity_id'])
        op.create_index('ix_opportunity_tags_tag_id', 'opportunity_tags', ['tag_id'])

    # Create comments table
    if not table_exists('comments'):
        op.create_table(
            'comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('parent_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True),
            sa.Column('is_edited', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_comments_opportunity_id', 'comments', ['opportunity_id'])
        op.create_index('ix_comments_user_id', 'comments', ['user_id'])
        op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
        op.create_index('ix_comments_created_at', 'comments', ['created_at'])

    # Create favorites table
    if not table_exists('favorites'):
        op.create_table(
            'favorites',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('opportunity_id', sa.Integer(), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('opportunity_id', 'user_id', name='uq_favorite_opportunity_user')
        )
        op.create_index('ix_favorites_user_id', 'favorites', ['user_id'])
        op.create_index('ix_favorites_opportunity_id', 'favorites', ['opportunity_id'])


def downgrade() -> None:
    if table_exists('favorites'):
        op.drop_table('favorites')
    if table_exists('comments'):
        op.drop_table('comments')
    if table_exists('opportunity_tags'):
        op.drop_table('opportunity_tags')
    if table_exists('tags'):
        op.drop_table('tags')
