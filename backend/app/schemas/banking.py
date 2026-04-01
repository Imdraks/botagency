"""
Banking schemas for API request/response validation
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from app.db.models.banking import (
    BankConnectionStatus,
    BankAccountType,
    ConsentType,
    ConsentStatus,
    SyncStatus,
    SyncTrigger,
)


# ============================================================================
# BANK CONNECTION SCHEMAS
# ============================================================================

class BankConnectionCreate(BaseModel):
    """Create a new bank connection (initiate OAuth flow)"""
    bank_name: str = Field(..., max_length=255)
    bank_code: Optional[str] = None
    bank_logo_url: Optional[str] = None
    bank_country: str = "FR"
    provider: Optional[str] = None  # e.g. "bridge", "plaid"


class BankConnectionUpdate(BaseModel):
    """Update connection settings"""
    auto_sync_enabled: Optional[bool] = None
    sync_frequency_hours: Optional[int] = Field(None, ge=1, le=168)  # 1h to 7 days


class BankConnectionResponse(BaseModel):
    """Bank connection response (never includes tokens)"""
    id: int
    workspace_id: int
    bank_name: str
    bank_code: Optional[str] = None
    bank_logo_url: Optional[str] = None
    bank_country: str = "FR"
    provider: Optional[str] = None
    status: BankConnectionStatus
    status_message: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None
    consent_expires_at: Optional[datetime] = None
    auto_sync_enabled: bool = True
    sync_frequency_hours: int = 12
    connected_by_id: Optional[int] = None
    accounts_count: int = 0
    total_balance: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankConnectionListResponse(BaseModel):
    """List of bank connections"""
    connections: List[BankConnectionResponse]
    total: int
    banking_enabled: bool = True


class BankConnectionDetail(BankConnectionResponse):
    """Detailed view with accounts and recent syncs"""
    accounts: List["BankAccountResponse"] = []
    recent_syncs: List["BankSyncLogResponse"] = []
    active_consent: Optional["BankConsentResponse"] = None


# ============================================================================
# BANK ACCOUNT SCHEMAS
# ============================================================================

class BankAccountUpdate(BaseModel):
    """Update account display settings"""
    account_name: Optional[str] = Field(None, max_length=255)
    is_visible: Optional[bool] = None
    display_color: Optional[str] = Field(None, max_length=7)
    display_order: Optional[int] = None


class BankAccountResponse(BaseModel):
    """Bank account response"""
    id: int
    connection_id: int
    workspace_id: int
    account_name: str
    account_number_masked: Optional[str] = None
    iban_masked: Optional[str] = None  # Only masked IBAN for display
    account_type: BankAccountType
    currency: str = "EUR"
    balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    balance_updated_at: Optional[datetime] = None
    is_active: bool = True
    is_visible: bool = True
    display_color: Optional[str] = None
    display_order: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankAccountListResponse(BaseModel):
    """List of bank accounts"""
    accounts: List[BankAccountResponse]
    total: int
    total_balance: Optional[Decimal] = None
    currency: str = "EUR"


# ============================================================================
# BANK CONSENT SCHEMAS
# ============================================================================

class BankConsentResponse(BaseModel):
    """Bank consent response"""
    id: int
    connection_id: int
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    scope: Optional[list] = None
    days_until_expiry: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BANK SYNC LOG SCHEMAS
# ============================================================================

class BankSyncLogResponse(BaseModel):
    """Sync log response"""
    id: int
    connection_id: int
    status: SyncStatus
    trigger: SyncTrigger
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    accounts_synced: int = 0
    transactions_fetched: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    triggered_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BankSyncLogListResponse(BaseModel):
    """List of sync logs"""
    logs: List[BankSyncLogResponse]
    total: int


# ============================================================================
# BANKING DASHBOARD SCHEMAS
# ============================================================================

class BankingDashboard(BaseModel):
    """Overview dashboard for banking module"""
    banking_enabled: bool
    total_connections: int = 0
    active_connections: int = 0
    total_accounts: int = 0
    connections: List[BankConnectionResponse] = []
    # Aggregate balances per currency
    total_balances: dict = {}  # {"EUR": 12345.67, "USD": 1000.00}
    # Status summary
    status_summary: dict = {}  # {"CONNECTED": 2, "SYNC_ERROR": 1}
    # Consent alerts
    expiring_consents: int = 0  # Consents expiring within 14 days
    last_sync_at: Optional[datetime] = None


# ============================================================================
# ADMIN SCHEMAS (Super admin only)
# ============================================================================

class BankingFeatureToggle(BaseModel):
    """Toggle banking feature for a workspace (super admin only)"""
    enabled: bool


class WorkspaceBankingStatus(BaseModel):
    """Banking status for admin overview (no credentials exposed)"""
    workspace_id: int
    workspace_name: str
    banking_enabled: bool
    connections_count: int = 0
    active_connections: int = 0
    last_sync_at: Optional[datetime] = None


# ============================================================================
# OAUTH FLOW SCHEMAS
# ============================================================================

class BankOAuthInitiate(BaseModel):
    """Initiate OAuth flow with a bank"""
    bank_name: str = Field(..., max_length=255)
    bank_code: Optional[str] = None
    provider: str = Field(..., max_length=100)  # Required for OAuth
    redirect_url: Optional[str] = None  # Frontend callback URL


class BankOAuthInitiateResponse(BaseModel):
    """Response with OAuth redirect URL"""
    connection_id: int
    authorization_url: str
    state: str  # CSRF state parameter


class BankOAuthCallback(BaseModel):
    """OAuth callback data"""
    connection_id: int
    code: str
    state: str


class BankOAuthCallbackResponse(BaseModel):
    """OAuth callback result"""
    connection_id: int
    status: BankConnectionStatus
    accounts_discovered: int = 0
    message: str = ""


# Forward references
BankConnectionDetail.model_rebuild()
