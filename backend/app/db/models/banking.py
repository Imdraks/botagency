"""
Banking Connections models for Radar Business
==============================================

Multi-tenant banking management:
- BankConnection: A connection to a bank (one per bank per workspace)
- BankAccount: Individual bank accounts within a connection
- BankConsent: AISP/PISP consent tracking (Open Banking)
- BankSyncLog: Sync history and error tracking

Security:
- All tokens/credentials encrypted via Fernet (app.core.encryption)
- Super admin can ONLY enable/disable the feature, NOT access credentials
- Workspace admin manages their own bank connections
- Regular users get read-only access to account metadata (no balances by default)
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Enum, ForeignKey,
    Integer, Numeric, JSON, Index
)
from sqlalchemy.orm import relationship

from app.db.base import Base


# ============================================================================
# ENUMS
# ============================================================================

class BankConnectionStatus(str, PyEnum):
    """Status of a bank connection"""
    NOT_CONNECTED = "NOT_CONNECTED"       # Initial / disconnected
    CONNECTING = "CONNECTING"             # OAuth flow in progress
    CONNECTED = "CONNECTED"               # Active and syncing
    SYNC_ERROR = "SYNC_ERROR"             # Sync failed (temporary)
    CONSENT_EXPIRED = "CONSENT_EXPIRED"   # Consent needs renewal (90 days PSD2)
    ACTION_REQUIRED = "ACTION_REQUIRED"   # User must re-authenticate (SCA)
    SUSPENDED = "SUSPENDED"               # Manually paused by workspace admin
    REVOKED = "REVOKED"                   # Connection permanently revoked


class BankAccountType(str, PyEnum):
    """Type of bank account"""
    CHECKING = "CHECKING"           # Compte courant
    SAVINGS = "SAVINGS"             # Compte épargne
    BUSINESS = "BUSINESS"           # Compte professionnel
    JOINT = "JOINT"                 # Compte joint
    CREDIT_CARD = "CREDIT_CARD"     # Carte de crédit
    LOAN = "LOAN"                   # Prêt / crédit
    OTHER = "OTHER"


class ConsentType(str, PyEnum):
    """Open Banking consent type"""
    AISP = "AISP"   # Account Information Service Provider (read-only)
    PISP = "PISP"   # Payment Initiation Service Provider (write)


class ConsentStatus(str, PyEnum):
    """Status of a banking consent"""
    PENDING = "PENDING"         # Awaiting user authorization
    ACTIVE = "ACTIVE"           # Valid and usable
    EXPIRED = "EXPIRED"         # Past validity date
    REVOKED = "REVOKED"         # Manually revoked
    REJECTED = "REJECTED"       # User rejected consent


class SyncStatus(str, PyEnum):
    """Status of a sync operation"""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"         # Some accounts synced, others failed
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SyncTrigger(str, PyEnum):
    """What triggered the sync"""
    MANUAL = "MANUAL"           # User clicked "Sync now"
    SCHEDULED = "SCHEDULED"     # Automated daily/hourly sync
    WEBHOOK = "WEBHOOK"         # Bank pushed a notification
    RECONNECT = "RECONNECT"     # After re-authentication


# ============================================================================
# BANK CONNECTION
# ============================================================================

class BankConnection(Base):
    """
    A connection to a bank institution for a workspace.
    One workspace can have multiple bank connections (one per bank).
    
    The access_token and refresh_token are encrypted at rest
    using Fernet symmetric encryption (app.core.encryption).
    """
    __tablename__ = "banking_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Bank institution info
    bank_name = Column(String(255), nullable=False)          # e.g. "Crédit Agricole"
    bank_code = Column(String(50), nullable=True)            # BIC/SWIFT or provider code
    bank_logo_url = Column(String(500), nullable=True)       # Logo URL for display
    bank_country = Column(String(10), default="FR")          # ISO country code
    
    # Provider info (Open Banking aggregator)
    provider = Column(String(100), nullable=True)            # e.g. "bridge", "plaid", "budget_insight"
    provider_connection_id = Column(String(255), nullable=True)  # External connection ID
    
    # Connection status
    status = Column(
        Enum(BankConnectionStatus, values_callable=lambda x: [e.value for e in x]),
        default=BankConnectionStatus.NOT_CONNECTED,
        nullable=False
    )
    status_message = Column(Text, nullable=True)             # Human-readable status detail
    
    # Encrypted credentials (NEVER expose in API responses)
    access_token_encrypted = Column(Text, nullable=True)     # Encrypted access token
    refresh_token_encrypted = Column(Text, nullable=True)    # Encrypted refresh token
    
    # Connection metadata
    connected_at = Column(DateTime, nullable=True)           # When connection was established
    last_sync_at = Column(DateTime, nullable=True)           # Last successful sync
    next_sync_at = Column(DateTime, nullable=True)           # Next scheduled sync
    
    # Consent tracking
    consent_expires_at = Column(DateTime, nullable=True)     # PSD2: consent valid 90 days max
    
    # Settings (per connection)
    auto_sync_enabled = Column(Boolean, default=True)        # Enable automatic sync
    sync_frequency_hours = Column(Integer, default=12)       # Sync every N hours
    
    # Connected by (workspace admin who set it up)
    connected_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Audit trail (JSON array of events)
    audit_log = Column(JSON, default=list)

    # Provider-specific metadata (token expiry, scopes, etc.)
    bank_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("BankAccount", back_populates="connection", cascade="all, delete-orphan")
    consents = relationship("BankConsent", back_populates="connection", cascade="all, delete-orphan")
    sync_logs = relationship("BankSyncLog", back_populates="connection", cascade="all, delete-orphan",
                             order_by="desc(BankSyncLog.started_at)")
    connected_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_banking_connections_workspace_status', 'workspace_id', 'status'),
        Index('ix_banking_connections_workspace_bank', 'workspace_id', 'bank_name'),
    )


# ============================================================================
# BANK ACCOUNT
# ============================================================================

class BankAccount(Base):
    """
    An individual bank account within a connection.
    A single bank connection can have multiple accounts
    (checking, savings, credit cards, etc.).
    """
    __tablename__ = "banking_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('banking_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Account identification
    account_name = Column(String(255), nullable=False)       # User-friendly name
    account_number_masked = Column(String(50), nullable=True)  # Last 4 digits only: ****1234
    iban_encrypted = Column(String(500), nullable=True)      # Encrypted IBAN
    
    # Provider reference
    provider_account_id = Column(String(255), nullable=True) # External account ID
    
    # Account type
    account_type = Column(
        Enum(BankAccountType, values_callable=lambda x: [e.value for e in x]),
        default=BankAccountType.CHECKING,
        nullable=False
    )
    
    # Currency
    currency = Column(String(3), default="EUR")              # ISO 4217
    
    # Balance (updated on sync)
    balance = Column(Numeric(14, 2), nullable=True)          # Current balance
    available_balance = Column(Numeric(14, 2), nullable=True)  # Available balance
    balance_updated_at = Column(DateTime, nullable=True)     # When balance was last updated
    
    # Account status
    is_active = Column(Boolean, default=True)                # Active account
    is_visible = Column(Boolean, default=True)               # Visible in dashboard
    
    # Display settings
    display_color = Column(String(7), nullable=True)         # Hex color for UI: #3B82F6
    display_order = Column(Integer, default=0)               # Sort order in UI
    
    # Metadata from bank
    bank_metadata = Column(JSON, nullable=True)              # Raw metadata from provider
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("BankConnection", back_populates="accounts")
    
    # Indexes
    __table_args__ = (
        Index('ix_banking_accounts_workspace_active', 'workspace_id', 'is_active'),
    )


# ============================================================================
# BANK CONSENT (PSD2 / Open Banking)
# ============================================================================

class BankConsent(Base):
    """
    Tracks Open Banking consents (PSD2 compliance).
    Each consent has a limited validity (typically 90 days for AISP).
    """
    __tablename__ = "banking_consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('banking_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Consent type
    consent_type = Column(
        Enum(ConsentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Status
    status = Column(
        Enum(ConsentStatus, values_callable=lambda x: [e.value for e in x]),
        default=ConsentStatus.PENDING,
        nullable=False
    )
    
    # Provider reference
    provider_consent_id = Column(String(255), nullable=True)
    
    # Validity
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)             # PSD2: max 90 days
    revoked_at = Column(DateTime, nullable=True)
    
    # Scope (what data is consented)
    scope = Column(JSON, nullable=True)                      # e.g. ["balances", "transactions"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("BankConnection", back_populates="consents")


# ============================================================================
# BANK SYNC LOG
# ============================================================================

class BankSyncLog(Base):
    """
    Log of sync operations for audit and debugging.
    Each sync attempt creates one log entry.
    """
    __tablename__ = "banking_sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey('banking_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, index=True)
    
    # Sync info
    status = Column(
        Enum(SyncStatus, values_callable=lambda x: [e.value for e in x]),
        default=SyncStatus.RUNNING,
        nullable=False
    )
    trigger = Column(
        Enum(SyncTrigger, values_callable=lambda x: [e.value for e in x]),
        default=SyncTrigger.MANUAL,
        nullable=False
    )
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)             # Duration in milliseconds
    
    # Results
    accounts_synced = Column(Integer, default=0)             # Number of accounts synced
    transactions_fetched = Column(Integer, default=0)        # New transactions found
    
    # Error details
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Triggered by
    triggered_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    connection = relationship("BankConnection", back_populates="sync_logs")
    triggered_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_banking_sync_logs_connection_started', 'connection_id', 'started_at'),
        Index('ix_banking_sync_logs_workspace_status', 'workspace_id', 'status'),
    )
