"""
Banking API endpoints - Connexions bancaires
=============================================

Permission model:
- Super admin (global admin): enable/disable banking, view metadata ONLY
- Workspace admin: full CRUD on connections, manage OAuth, trigger sync
- Regular workspace member: read-only access (accounts list, balances)

Security:
- Tokens NEVER exposed in API responses
- All mutations require workspace admin role
- Audit trail on all sensitive operations
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.api.deps import (
    get_current_user,
    get_current_admin_user,
    get_user_workspace_id,
)
from app.db.models.user import User, Role
from app.db.models.banking import (
    BankConnection, BankAccount, BankConsent, BankSyncLog,
    BankConnectionStatus, SyncTrigger,
)
from app.schemas.banking import (
    BankConnectionCreate, BankConnectionUpdate, BankConnectionResponse,
    BankConnectionListResponse, BankConnectionDetail,
    BankAccountUpdate, BankAccountResponse, BankAccountListResponse,
    BankConsentResponse,
    BankSyncLogResponse, BankSyncLogListResponse,
    BankingDashboard, BankingFeatureToggle, WorkspaceBankingStatus,
    BankOAuthInitiate, BankOAuthInitiateResponse,
    BankOAuthCallback, BankOAuthCallbackResponse,
)
from app.services.banking_service import (
    is_workspace_admin, is_workspace_member, is_banking_enabled,
    get_connections, get_connection_detail, create_connection,
    update_connection_settings, delete_connection,
    suspend_connection, resume_connection,
    initiate_oauth, complete_oauth,
    trigger_sync, get_sync_logs,
    get_accounts, update_account_display,
    get_banking_dashboard, toggle_banking_feature, get_workspace_banking_status,
)
from app.core.encryption import decrypt_iban, mask_iban

router = APIRouter()


# ============================================================================
# HELPERS
# ============================================================================

def _require_banking_enabled(workspace_id: int, db: Session):
    """Raise 403 if banking is not enabled for the workspace."""
    if not is_banking_enabled(workspace_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La fonctionnalité Connexions bancaires n'est pas activée pour cet espace de travail.",
        )


def _require_workspace_admin(user: User, workspace_id: int, db: Session):
    """Raise 403 if user is not workspace admin."""
    if not is_workspace_admin(user, workspace_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un administrateur du workspace peut gérer les connexions bancaires.",
        )


def _connection_to_response(conn: BankConnection) -> BankConnectionResponse:
    """Convert a connection model to API response (no sensitive data)."""
    # Count accounts and total balance
    accounts_count = 0
    total_balance = Decimal("0")
    if conn.accounts:
        for acc in conn.accounts:
            if acc.is_active:
                accounts_count += 1
                if acc.balance is not None:
                    total_balance += acc.balance
    
    return BankConnectionResponse(
        id=conn.id,
        workspace_id=conn.workspace_id,
        bank_name=conn.bank_name,
        bank_code=conn.bank_code,
        bank_logo_url=conn.bank_logo_url,
        bank_country=conn.bank_country,
        provider=conn.provider,
        status=conn.status,
        status_message=conn.status_message,
        connected_at=conn.connected_at,
        last_sync_at=conn.last_sync_at,
        next_sync_at=conn.next_sync_at,
        consent_expires_at=conn.consent_expires_at,
        auto_sync_enabled=conn.auto_sync_enabled,
        sync_frequency_hours=conn.sync_frequency_hours,
        connected_by_id=conn.connected_by_id,
        accounts_count=accounts_count,
        total_balance=total_balance if accounts_count > 0 else None,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


def _account_to_response(acc: BankAccount) -> BankAccountResponse:
    """Convert an account model to API response (masked IBAN)."""
    iban_masked = None
    if acc.iban_encrypted:
        try:
            iban = decrypt_iban(acc.iban_encrypted)
            iban_masked = mask_iban(iban) if iban else None
        except Exception:
            iban_masked = None
    
    return BankAccountResponse(
        id=acc.id,
        connection_id=acc.connection_id,
        workspace_id=acc.workspace_id,
        account_name=acc.account_name,
        account_number_masked=acc.account_number_masked,
        iban_masked=iban_masked,
        account_type=acc.account_type,
        currency=acc.currency,
        balance=acc.balance,
        available_balance=acc.available_balance,
        balance_updated_at=acc.balance_updated_at,
        is_active=acc.is_active,
        is_visible=acc.is_visible,
        display_color=acc.display_color,
        display_order=acc.display_order,
        created_at=acc.created_at,
        updated_at=acc.updated_at,
    )


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/banking/dashboard", response_model=BankingDashboard)
def get_dashboard(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get banking dashboard overview.
    All workspace members can view the dashboard.
    """
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    dashboard_data = get_banking_dashboard(db, workspace_id)
    
    # Convert connections to response objects
    connections_response = [
        _connection_to_response(c) for c in dashboard_data["connections"]
    ]
    
    return BankingDashboard(
        banking_enabled=dashboard_data["banking_enabled"],
        total_connections=dashboard_data["total_connections"],
        active_connections=dashboard_data["active_connections"],
        total_accounts=dashboard_data["total_accounts"],
        connections=connections_response,
        total_balances=dashboard_data["total_balances"],
        status_summary=dashboard_data["status_summary"],
        expiring_consents=dashboard_data["expiring_consents"],
        last_sync_at=dashboard_data["last_sync_at"],
    )


# ============================================================================
# CONNECTIONS CRUD
# ============================================================================

@router.get("/banking/connections", response_model=BankConnectionListResponse)
def list_connections(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all bank connections for the workspace."""
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    connections = get_connections(db, workspace_id, include_accounts=True)
    enabled = is_banking_enabled(workspace_id, db)
    
    return BankConnectionListResponse(
        connections=[_connection_to_response(c) for c in connections],
        total=len(connections),
        banking_enabled=enabled,
    )


@router.get("/banking/connections/{connection_id}", response_model=BankConnectionDetail)
def get_connection(
    connection_id: int,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed info for a bank connection."""
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    # Build detail response
    accounts_resp = [_account_to_response(a) for a in (conn.accounts or [])]
    
    # Recent syncs
    syncs = get_sync_logs(db, connection_id, workspace_id, limit=10)
    syncs_resp = [BankSyncLogResponse.model_validate(s) for s in syncs]
    
    # Active consent
    active_consent = None
    for consent in (conn.consents or []):
        if consent.status.value == "ACTIVE":
            days_until = None
            if consent.expires_at:
                delta = consent.expires_at - datetime.utcnow()
                days_until = max(0, delta.days)
            active_consent = BankConsentResponse(
                id=consent.id,
                connection_id=consent.connection_id,
                consent_type=consent.consent_type,
                status=consent.status,
                granted_at=consent.granted_at,
                expires_at=consent.expires_at,
                revoked_at=consent.revoked_at,
                scope=consent.scope,
                days_until_expiry=days_until,
                created_at=consent.created_at,
            )
            break
    
    base = _connection_to_response(conn)
    return BankConnectionDetail(
        **base.model_dump(),
        accounts=accounts_resp,
        recent_syncs=syncs_resp,
        active_consent=active_consent,
    )


@router.post("/banking/connections", response_model=BankConnectionResponse, status_code=201)
def create_bank_connection(
    data: BankConnectionCreate,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new bank connection.
    Requires workspace admin role AND banking enabled.
    """
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = create_connection(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        bank_name=data.bank_name,
        bank_code=data.bank_code,
        bank_logo_url=data.bank_logo_url,
        bank_country=data.bank_country,
        provider=data.provider,
    )
    return _connection_to_response(conn)


@router.patch("/banking/connections/{connection_id}", response_model=BankConnectionResponse)
def update_connection(
    connection_id: int,
    data: BankConnectionUpdate,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update connection settings (workspace admin only)."""
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    conn = update_connection_settings(
        db=db,
        connection=conn,
        user_id=current_user.id,
        auto_sync_enabled=data.auto_sync_enabled,
        sync_frequency_hours=data.sync_frequency_hours,
    )
    return _connection_to_response(conn)


@router.delete("/banking/connections/{connection_id}", status_code=204)
def remove_connection(
    connection_id: int,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a bank connection and all its data.
    Requires workspace admin role. This action is irreversible.
    """
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    delete_connection(db, conn, current_user.id)
    return None


@router.post("/banking/connections/{connection_id}/suspend", response_model=BankConnectionResponse)
def suspend_bank_connection(
    connection_id: int,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Suspend a bank connection (workspace admin only)."""
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    conn = suspend_connection(db, conn, current_user.id)
    return _connection_to_response(conn)


@router.post("/banking/connections/{connection_id}/resume", response_model=BankConnectionResponse)
def resume_bank_connection(
    connection_id: int,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume a suspended bank connection (workspace admin only)."""
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    conn = resume_connection(db, conn, current_user.id)
    return _connection_to_response(conn)


# ============================================================================
# OAUTH FLOW
# ============================================================================

@router.post("/banking/connections/{connection_id}/oauth/initiate", response_model=BankOAuthInitiateResponse)
def initiate_bank_oauth(
    connection_id: int,
    data: BankOAuthInitiate,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate OAuth flow to connect a bank.
    Returns an authorization URL to redirect the user to.
    Workspace admin only.
    """
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    authorization_url, state_token = initiate_oauth(
        db=db,
        connection=conn,
        user_id=current_user.id,
        provider=data.provider,
        redirect_url=data.redirect_url,
    )
    
    return BankOAuthInitiateResponse(
        connection_id=conn.id,
        authorization_url=authorization_url,
        state=state_token,
    )


@router.post("/banking/connections/{connection_id}/oauth/callback", response_model=BankOAuthCallbackResponse)
def handle_bank_oauth_callback(
    connection_id: int,
    data: BankOAuthCallback,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback from bank provider.
    Completes the connection flow.
    """
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    # TODO: Exchange code for tokens using provider API
    # For now, simulate with dummy tokens
    access_token = f"simulated_access_{data.code}"
    refresh_token = f"simulated_refresh_{data.code}"
    
    conn = complete_oauth(
        db=db,
        connection=conn,
        user_id=current_user.id,
        access_token=access_token,
        refresh_token=refresh_token,
    )
    
    return BankOAuthCallbackResponse(
        connection_id=conn.id,
        status=conn.status,
        accounts_discovered=len(conn.accounts) if conn.accounts else 0,
        message="Connexion bancaire établie avec succès",
    )


# ============================================================================
# SYNC
# ============================================================================

@router.post("/banking/connections/{connection_id}/sync", response_model=BankSyncLogResponse)
def trigger_bank_sync(
    connection_id: int,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger a manual sync for a bank connection.
    Workspace admin only.
    """
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    conn = get_connection_detail(db, connection_id, workspace_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connexion bancaire introuvable")
    
    if conn.status not in (BankConnectionStatus.CONNECTED, BankConnectionStatus.SYNC_ERROR):
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de synchroniser : la connexion est en état '{conn.status.value}'",
        )
    
    sync_log = trigger_sync(
        db=db,
        connection=conn,
        user_id=current_user.id,
        trigger=SyncTrigger.MANUAL,
    )
    
    return BankSyncLogResponse.model_validate(sync_log)


@router.get("/banking/connections/{connection_id}/sync-logs", response_model=BankSyncLogListResponse)
def list_sync_logs(
    connection_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sync history for a connection."""
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    logs = get_sync_logs(db, connection_id, workspace_id, limit=limit)
    
    return BankSyncLogListResponse(
        logs=[BankSyncLogResponse.model_validate(l) for l in logs],
        total=len(logs),
    )


# ============================================================================
# ACCOUNTS
# ============================================================================

@router.get("/banking/accounts", response_model=BankAccountListResponse)
def list_accounts(
    connection_id: Optional[int] = Query(default=None),
    visible_only: bool = Query(default=False),
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List bank accounts for the workspace."""
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    accounts = get_accounts(
        db, workspace_id,
        connection_id=connection_id,
        active_only=True,
        visible_only=visible_only,
    )
    
    # Total balance
    total_balance = Decimal("0")
    for acc in accounts:
        if acc.balance is not None:
            total_balance += acc.balance
    
    return BankAccountListResponse(
        accounts=[_account_to_response(a) for a in accounts],
        total=len(accounts),
        total_balance=total_balance if accounts else None,
        currency="EUR",  # Primary currency
    )


@router.patch("/banking/accounts/{account_id}", response_model=BankAccountResponse)
def update_account(
    account_id: int,
    data: BankAccountUpdate,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update account display settings (workspace admin only)."""
    _require_banking_enabled(workspace_id, db)
    _require_workspace_admin(current_user, workspace_id, db)
    
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.workspace_id == workspace_id,
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire introuvable")
    
    account = update_account_display(
        db=db,
        account=account,
        account_name=data.account_name,
        is_visible=data.is_visible,
        display_color=data.display_color,
        display_order=data.display_order,
    )
    return _account_to_response(account)


# ============================================================================
# ADMIN ENDPOINTS (Super admin / Global admin only)
# ============================================================================

@router.post("/banking/admin/toggle", response_model=WorkspaceBankingStatus)
def admin_toggle_banking(
    data: BankingFeatureToggle,
    workspace_id: int = Query(..., description="Workspace to toggle banking for"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Enable or disable banking for a workspace.
    Super admin only. Does NOT give access to bank credentials.
    """
    success = toggle_banking_feature(db, workspace_id, data.enabled)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace introuvable")
    
    return WorkspaceBankingStatus(**get_workspace_banking_status(db, workspace_id))


@router.get("/banking/admin/status", response_model=WorkspaceBankingStatus)
def admin_get_banking_status(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get banking status for a workspace (metadata only).
    Super admin only. No credentials exposed.
    """
    status_data = get_workspace_banking_status(db, workspace_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Workspace introuvable")
    
    return WorkspaceBankingStatus(**status_data)
