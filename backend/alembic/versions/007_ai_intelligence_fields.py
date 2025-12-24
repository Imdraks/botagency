"""Add AI Intelligence fields to artist_analyses

Revision ID: 007_ai_intelligence
Revises: 006_sso_accounts
Create Date: 2024-12-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_ai_intelligence'
down_revision = '006_sso_accounts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI Intelligence fields to artist_analyses table
    
    # AI Score & Tier
    op.add_column('artist_analyses', sa.Column('ai_score', sa.Float(), nullable=True, default=0))
    op.add_column('artist_analyses', sa.Column('ai_tier', sa.String(50), nullable=True))
    
    # Growth Predictions
    op.add_column('artist_analyses', sa.Column('growth_trend', sa.String(50), nullable=True))
    op.add_column('artist_analyses', sa.Column('predicted_listeners_30d', sa.Integer(), nullable=True))
    op.add_column('artist_analyses', sa.Column('predicted_listeners_90d', sa.Integer(), nullable=True))
    op.add_column('artist_analyses', sa.Column('predicted_listeners_180d', sa.Integer(), nullable=True))
    op.add_column('artist_analyses', sa.Column('growth_rate_monthly', sa.Float(), nullable=True))
    
    # SWOT Analysis
    op.add_column('artist_analyses', sa.Column('strengths', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('weaknesses', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('opportunities', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('threats', sa.JSON(), nullable=True))
    
    # Booking Intelligence
    op.add_column('artist_analyses', sa.Column('optimal_fee', sa.Float(), nullable=True))
    op.add_column('artist_analyses', sa.Column('negotiation_power', sa.String(50), nullable=True))
    op.add_column('artist_analyses', sa.Column('best_booking_window', sa.String(100), nullable=True))
    op.add_column('artist_analyses', sa.Column('event_type_fit', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('territory_strength', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('seasonal_demand', sa.JSON(), nullable=True))
    
    # Risk & Opportunity
    op.add_column('artist_analyses', sa.Column('risk_score', sa.Float(), nullable=True))
    op.add_column('artist_analyses', sa.Column('risk_factors', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('opportunity_score', sa.Float(), nullable=True))
    op.add_column('artist_analyses', sa.Column('key_opportunities', sa.JSON(), nullable=True))
    
    # Content Strategy
    op.add_column('artist_analyses', sa.Column('best_platforms', sa.JSON(), nullable=True))
    op.add_column('artist_analyses', sa.Column('engagement_rate', sa.Float(), nullable=True))
    op.add_column('artist_analyses', sa.Column('viral_potential', sa.Float(), nullable=True))
    op.add_column('artist_analyses', sa.Column('content_recommendations', sa.JSON(), nullable=True))
    
    # AI Summary
    op.add_column('artist_analyses', sa.Column('ai_summary', sa.Text(), nullable=True))
    op.add_column('artist_analyses', sa.Column('ai_recommendations', sa.JSON(), nullable=True))
    
    # Full AI Report
    op.add_column('artist_analyses', sa.Column('ai_report', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove AI Intelligence fields
    op.drop_column('artist_analyses', 'ai_report')
    op.drop_column('artist_analyses', 'ai_recommendations')
    op.drop_column('artist_analyses', 'ai_summary')
    op.drop_column('artist_analyses', 'content_recommendations')
    op.drop_column('artist_analyses', 'viral_potential')
    op.drop_column('artist_analyses', 'engagement_rate')
    op.drop_column('artist_analyses', 'best_platforms')
    op.drop_column('artist_analyses', 'key_opportunities')
    op.drop_column('artist_analyses', 'opportunity_score')
    op.drop_column('artist_analyses', 'risk_factors')
    op.drop_column('artist_analyses', 'risk_score')
    op.drop_column('artist_analyses', 'seasonal_demand')
    op.drop_column('artist_analyses', 'territory_strength')
    op.drop_column('artist_analyses', 'event_type_fit')
    op.drop_column('artist_analyses', 'best_booking_window')
    op.drop_column('artist_analyses', 'negotiation_power')
    op.drop_column('artist_analyses', 'optimal_fee')
    op.drop_column('artist_analyses', 'threats')
    op.drop_column('artist_analyses', 'opportunities')
    op.drop_column('artist_analyses', 'weaknesses')
    op.drop_column('artist_analyses', 'strengths')
    op.drop_column('artist_analyses', 'growth_rate_monthly')
    op.drop_column('artist_analyses', 'predicted_listeners_180d')
    op.drop_column('artist_analyses', 'predicted_listeners_90d')
    op.drop_column('artist_analyses', 'predicted_listeners_30d')
    op.drop_column('artist_analyses', 'growth_trend')
    op.drop_column('artist_analyses', 'ai_tier')
    op.drop_column('artist_analyses', 'ai_score')
