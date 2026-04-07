"""020 - Artist events table for Ticketmaster integration

Revision ID: 020_artist_events
Revises: 019_agency_cockpit
Create Date: 2025-04-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import inspect as sa_inspect


revision = "045_artist_events"
down_revision = "044_fix_tags_columns"
branch_labels = None
depends_on = None


def table_exists(table_name):
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not table_exists("artist_events"):
        op.execute("""
            CREATE TABLE artist_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                artist_id UUID REFERENCES discovery_artists(id) ON DELETE CASCADE,
                
                external_id VARCHAR(255),
                source VARCHAR(50) NOT NULL DEFAULT 'ticketmaster',
                
                artist_name VARCHAR(500) NOT NULL,
                artist_image TEXT,
                artist_genres JSONB DEFAULT '[]'::jsonb,
                artist_score FLOAT,
                monthly_listeners INTEGER,
                
                event_name VARCHAR(1000) NOT NULL,
                event_type VARCHAR(50) NOT NULL DEFAULT 'concert',
                event_url TEXT,
                event_image TEXT,
                
                venue VARCHAR(500),
                city VARCHAR(255),
                country VARCHAR(100) DEFAULT 'FR',
                lat FLOAT,
                lng FLOAT,
                
                event_date TIMESTAMP,
                on_sale_date TIMESTAMP,
                price_min FLOAT,
                price_max FLOAT,
                currency VARCHAR(10) DEFAULT 'EUR',
                capacity INTEGER,
                
                status VARCHAR(50),
                promoter VARCHAR(500),
                segment VARCHAR(100),
                genre_classification VARCHAR(255),
                
                raw_data JSONB,
                fetched_at TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)

        op.execute("CREATE INDEX ix_artist_events_workspace ON artist_events(workspace_id)")
        op.execute("CREATE INDEX ix_artist_events_artist ON artist_events(artist_id)")
        op.execute("CREATE INDEX ix_artist_events_date ON artist_events(event_date)")
        op.execute("CREATE INDEX ix_artist_events_city ON artist_events(city)")
        op.execute("CREATE INDEX ix_artist_events_type ON artist_events(event_type)")
        op.execute("""
            ALTER TABLE artist_events
            ADD CONSTRAINT uq_workspace_event_source UNIQUE (workspace_id, external_id, source)
        """)


def downgrade():
    if table_exists("artist_events"):
        op.execute("DROP TABLE artist_events CASCADE")
