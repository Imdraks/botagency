"""Banking Connections tables

Revision ID: 041_banking_connections
Revises: 040_artist_snapshots
Create Date: 2026-02-01

"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '041_banking_connections'
down_revision = '040_artist_snapshots'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── Create enums (idempotent) ──
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE bankconnectionstatus AS ENUM (
                'NOT_CONNECTED','CONNECTING','CONNECTED','SYNC_ERROR',
                'CONSENT_EXPIRED','ACTION_REQUIRED','SUSPENDED','REVOKED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE bankaccounttype AS ENUM (
                'CHECKING','SAVINGS','BUSINESS','JOINT','CREDIT_CARD','LOAN','OTHER'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE consenttype AS ENUM ('AISP','PISP');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE consentstatus AS ENUM ('PENDING','ACTIVE','EXPIRED','REVOKED','REJECTED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE syncstatus AS ENUM ('RUNNING','SUCCESS','PARTIAL','FAILED','CANCELLED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE synctrigger AS ENUM ('MANUAL','SCHEDULED','WEBHOOK','RECONNECT');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # ── banking_connections ──
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS banking_connections (
            id SERIAL PRIMARY KEY,
            workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
            bank_name VARCHAR(255) NOT NULL,
            bank_code VARCHAR(50),
            bank_logo_url VARCHAR(500),
            bank_country VARCHAR(10) DEFAULT 'FR',
            provider VARCHAR(100),
            provider_connection_id VARCHAR(255),
            status bankconnectionstatus NOT NULL DEFAULT 'NOT_CONNECTED',
            status_message TEXT,
            access_token_encrypted TEXT,
            refresh_token_encrypted TEXT,
            connected_at TIMESTAMP,
            last_sync_at TIMESTAMP,
            next_sync_at TIMESTAMP,
            consent_expires_at TIMESTAMP,
            auto_sync_enabled BOOLEAN DEFAULT TRUE,
            sync_frequency_hours INTEGER DEFAULT 12,
            connected_by_id INTEGER REFERENCES users(id),
            audit_log JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bc_ws ON banking_connections(workspace_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bc_ws_status ON banking_connections(workspace_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bc_ws_bank ON banking_connections(workspace_id, bank_name)"))

    # ── banking_accounts ──
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS banking_accounts (
            id SERIAL PRIMARY KEY,
            connection_id INTEGER NOT NULL REFERENCES banking_connections(id) ON DELETE CASCADE,
            workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
            account_name VARCHAR(255) NOT NULL,
            account_number_masked VARCHAR(50),
            iban_encrypted VARCHAR(500),
            provider_account_id VARCHAR(255),
            account_type bankaccounttype NOT NULL DEFAULT 'CHECKING',
            currency VARCHAR(3) DEFAULT 'EUR',
            balance NUMERIC(14,2),
            available_balance NUMERIC(14,2),
            balance_updated_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            is_visible BOOLEAN DEFAULT TRUE,
            display_color VARCHAR(7),
            display_order INTEGER DEFAULT 0,
            bank_metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ba_conn ON banking_accounts(connection_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ba_ws ON banking_accounts(workspace_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ba_ws_active ON banking_accounts(workspace_id, is_active)"))

    # ── banking_consents ──
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS banking_consents (
            id SERIAL PRIMARY KEY,
            connection_id INTEGER NOT NULL REFERENCES banking_connections(id) ON DELETE CASCADE,
            workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
            consent_type consenttype NOT NULL,
            status consentstatus NOT NULL DEFAULT 'PENDING',
            provider_consent_id VARCHAR(255),
            granted_at TIMESTAMP,
            expires_at TIMESTAMP,
            revoked_at TIMESTAMP,
            scope JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bcon_conn ON banking_consents(connection_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bcon_ws ON banking_consents(workspace_id)"))

    # ── banking_sync_logs ──
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS banking_sync_logs (
            id SERIAL PRIMARY KEY,
            connection_id INTEGER NOT NULL REFERENCES banking_connections(id) ON DELETE CASCADE,
            workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
            status syncstatus NOT NULL DEFAULT 'RUNNING',
            trigger synctrigger NOT NULL DEFAULT 'MANUAL',
            started_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP,
            duration_ms INTEGER,
            accounts_synced INTEGER DEFAULT 0,
            transactions_fetched INTEGER DEFAULT 0,
            error_code VARCHAR(100),
            error_message TEXT,
            triggered_by_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bsl_conn ON banking_sync_logs(connection_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bsl_ws ON banking_sync_logs(workspace_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bsl_conn_started ON banking_sync_logs(connection_id, started_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bsl_ws_status ON banking_sync_logs(workspace_id, status)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS banking_sync_logs CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS banking_consents CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS banking_accounts CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS banking_connections CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS synctrigger"))
    conn.execute(text("DROP TYPE IF EXISTS syncstatus"))
    conn.execute(text("DROP TYPE IF EXISTS consentstatus"))
    conn.execute(text("DROP TYPE IF EXISTS consenttype"))
    conn.execute(text("DROP TYPE IF EXISTS bankaccounttype"))
    conn.execute(text("DROP TYPE IF EXISTS bankconnectionstatus"))
