"""
Revolut Integration Service
============================

Business logic layer for Revolut Banking integration.
Orchestrates the OAuth flow, token management, account sync,
and transaction fetching — using the existing BankConnection model.

The Revolut connection is stored as a standard BankConnection with:
  - provider = "revolut"
  - bank_name = "Revolut Business"
  - bank_code = "REVOLT21"
  - access_token_encrypted / refresh_token_encrypted = Fernet-encrypted tokens
  - bank_metadata = { "token_expires_at": "...", "revolut_scopes": "READ", ... }
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.banking import (
    BankConnection, BankAccount, BankConsent, BankSyncLog,
    BankConnectionStatus, BankAccountType, ConsentType, ConsentStatus,
    SyncStatus, SyncTrigger,
)
from app.db.models.workspace import Workspace
from app.db.models.user import User
from app.core.encryption import encrypt_sensitive, decrypt_sensitive
from app.core.config import settings
from app.services.revolut_client import (
    get_consent_url,
    exchange_authorization_code,
    refresh_access_token,
    get_accounts as revolut_get_accounts,
    get_transactions as revolut_get_transactions,
    get_account_bank_details,
    RevolutAPIError,
    RevolutTokenExpiredError,
)

logger = logging.getLogger(__name__)

REVOLUT_PROVIDER = "revolut"
REVOLUT_BANK_NAME = "Revolut Business"
REVOLUT_BANK_CODE = "REVOLT21"


# ============================================================================
# HELPERS
# ============================================================================

def _get_access_token(connection: BankConnection) -> str:
    """Decrypt and return the access token."""
    if not connection.access_token_encrypted:
        raise ValueError("No access token stored for this connection")
    return decrypt_sensitive(connection.access_token_encrypted)


def _get_refresh_token(connection: BankConnection) -> str:
    """Decrypt and return the refresh token."""
    if not connection.refresh_token_encrypted:
        raise ValueError("No refresh token stored for this connection")
    return decrypt_sensitive(connection.refresh_token_encrypted)


def _is_token_expired(connection: BankConnection) -> bool:
    """Check if the access token is expired or close to expiry."""
    metadata = connection.bank_metadata or {}
    expires_at_str = metadata.get("token_expires_at")
    if not expires_at_str:
        return True  # Unknown expiry, assume expired
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        # Add 2 minute buffer
        return datetime.utcnow() >= (expires_at - timedelta(minutes=2))
    except (ValueError, TypeError):
        return True


def _add_audit_entry(connection: BankConnection, event: str, user_id: int, details: str = ""):
    """Add an entry to the connection's audit log."""
    audit_log = connection.audit_log or []
    audit_log.append({
        "event": event,
        "at": datetime.utcnow().isoformat(),
        "by": user_id,
        "details": details,
    })
    connection.audit_log = audit_log


def _map_revolut_account_type(revolut_account: Dict) -> BankAccountType:
    """Map Revolut account data to our BankAccountType enum."""
    name = (revolut_account.get("name") or "").lower()
    if "savings" in name:
        return BankAccountType.SAVINGS
    if "credit" in name:
        return BankAccountType.CREDIT_CARD
    return BankAccountType.BUSINESS


# ============================================================================
# OAUTH FLOW
# ============================================================================

def initiate_revolut_oauth(
    db: Session,
    workspace_id: int,
    user_id: int,
) -> Tuple[str, int]:
    """
    Start the Revolut OAuth flow.
    
    1. Creates (or reuses) a BankConnection with provider=revolut
    2. Generates the Revolut consent URL
    3. Returns (consent_url, connection_id)
    """
    client_id = settings.revolut_client_id
    redirect_uri = settings.revolut_redirect_uri
    
    if not client_id:
        raise ValueError("REVOLUT_CLIENT_ID is not configured")
    if not redirect_uri:
        raise ValueError("REVOLUT_REDIRECT_URI is not configured")
    
    # Check if there's already a Revolut connection for this workspace
    existing = db.query(BankConnection).filter(
        BankConnection.workspace_id == workspace_id,
        BankConnection.provider == REVOLUT_PROVIDER,
    ).first()
    
    if existing and existing.status == BankConnectionStatus.CONNECTED:
        raise ValueError("Revolut is already connected for this workspace")
    
    if existing:
        # Reuse existing connection in non-connected state
        connection = existing
        connection.status = BankConnectionStatus.CONNECTING
        connection.status_message = "En attente d'autorisation Revolut"
        _add_audit_entry(connection, "revolut_oauth_reinitiated", user_id)
    else:
        # Create new connection
        connection = BankConnection(
            workspace_id=workspace_id,
            bank_name=REVOLUT_BANK_NAME,
            bank_code=REVOLUT_BANK_CODE,
            bank_logo_url="/revolut-logo.svg",
            bank_country="GB",
            provider=REVOLUT_PROVIDER,
            status=BankConnectionStatus.CONNECTING,
            status_message="En attente d'autorisation Revolut",
            connected_by_id=user_id,
            audit_log=[],
        )
        _add_audit_entry(connection, "revolut_oauth_initiated", user_id)
        db.add(connection)
    
    db.commit()
    db.refresh(connection)
    
    # Build the consent URL
    consent_url = get_consent_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes="READ",
    )
    
    logger.info(f"Revolut OAuth initiated for workspace {workspace_id}, connection {connection.id}")
    return consent_url, connection.id


async def complete_revolut_oauth(
    db: Session,
    workspace_id: int,
    user_id: int,
    authorization_code: str,
) -> BankConnection:
    """
    Complete the Revolut OAuth flow after user consent.
    
    1. Exchange authorization code for access_token + refresh_token
    2. Encrypt and store tokens
    3. Update connection status to CONNECTED
    4. Create AISP consent record
    5. Trigger initial account sync
    
    Returns the updated BankConnection.
    """
    client_id = settings.revolut_client_id
    
    # Find the connecting Revolut connection
    connection = db.query(BankConnection).filter(
        BankConnection.workspace_id == workspace_id,
        BankConnection.provider == REVOLUT_PROVIDER,
    ).first()
    
    if not connection:
        raise ValueError("No Revolut connection found for this workspace. Initiate OAuth first.")
    
    # Exchange code for tokens
    token_data = await exchange_authorization_code(
        code=authorization_code,
        client_id=client_id,
    )
    
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 2400)  # Default 40 minutes
    
    # Encrypt and store
    connection.access_token_encrypted = encrypt_sensitive(access_token)
    if refresh_token:
        connection.refresh_token_encrypted = encrypt_sensitive(refresh_token)
    
    # Update metadata with token expiry
    metadata = connection.bank_metadata or {}
    metadata["token_expires_at"] = (
        datetime.utcnow() + timedelta(seconds=expires_in)
    ).isoformat()
    metadata["revolut_scopes"] = "READ"
    metadata["token_type"] = token_data.get("token_type", "bearer")
    connection.bank_metadata = metadata
    flag_modified(connection, "bank_metadata")
    
    # Update connection status
    connection.status = BankConnectionStatus.CONNECTED
    connection.status_message = None
    connection.connected_at = datetime.utcnow()
    
    # Revolut doesn't have PSD2 90-day consent like banks — tokens don't expire
    # but we set a long consent for UI consistency
    connection.consent_expires_at = datetime.utcnow() + timedelta(days=365)
    
    _add_audit_entry(connection, "revolut_oauth_completed", user_id)
    
    # Create AISP consent
    consent = BankConsent(
        connection_id=connection.id,
        workspace_id=workspace_id,
        consent_type=ConsentType.AISP,
        status=ConsentStatus.ACTIVE,
        granted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        scope=["accounts", "transactions"],
    )
    db.add(consent)
    db.commit()
    db.refresh(connection)
    
    # Sync accounts immediately
    try:
        await sync_revolut_accounts(db, connection, user_id)
    except Exception as e:
        logger.warning(f"Initial Revolut account sync failed: {e}")
    
    logger.info(f"Revolut OAuth completed for workspace {workspace_id}")
    return connection


# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

async def _ensure_valid_token(db: Session, connection: BankConnection) -> str:
    """
    Ensure the access token is valid, refreshing if necessary.
    Returns the valid access token.
    """
    if not _is_token_expired(connection):
        return _get_access_token(connection)
    
    # Token expired, refresh it
    logger.info(f"Refreshing Revolut token for connection {connection.id}")
    
    refresh_token = _get_refresh_token(connection)
    client_id = settings.revolut_client_id
    
    try:
        token_data = await refresh_access_token(refresh_token, client_id)
    except RevolutAPIError as e:
        logger.error(f"Failed to refresh Revolut token: {e}")
        connection.status = BankConnectionStatus.ACTION_REQUIRED
        connection.status_message = "Échec du rafraîchissement du token. Reconnexion nécessaire."
        db.commit()
        raise
    
    new_access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 2400)
    
    # Update stored token
    connection.access_token_encrypted = encrypt_sensitive(new_access_token)
    
    # Update metadata
    metadata = connection.bank_metadata or {}
    metadata["token_expires_at"] = (
        datetime.utcnow() + timedelta(seconds=expires_in)
    ).isoformat()
    metadata["last_token_refresh"] = datetime.utcnow().isoformat()
    connection.bank_metadata = metadata
    flag_modified(connection, "bank_metadata")
    
    db.commit()
    
    return new_access_token


# ============================================================================
# ACCOUNT SYNC
# ============================================================================

async def sync_revolut_accounts(
    db: Session,
    connection: BankConnection,
    user_id: Optional[int] = None,
) -> int:
    """
    Sync Revolut accounts into our BankAccount model.
    
    - Fetches all accounts from Revolut API
    - Creates or updates BankAccount records
    - Updates balances
    
    Returns the number of accounts synced.
    """
    access_token = await _ensure_valid_token(db, connection)
    
    # Create sync log
    sync_log = BankSyncLog(
        connection_id=connection.id,
        workspace_id=connection.workspace_id,
        status=SyncStatus.RUNNING,
        trigger=SyncTrigger.MANUAL if user_id else SyncTrigger.SCHEDULED,
        started_at=datetime.utcnow(),
        triggered_by_id=user_id,
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)
    
    try:
        # Fetch accounts from Revolut
        revolut_accounts = await revolut_get_accounts(access_token)
        
        accounts_synced = 0
        
        for rev_acc in revolut_accounts:
            rev_id = rev_acc.get("id", "")
            
            # Find existing account or create new
            existing = db.query(BankAccount).filter(
                BankAccount.connection_id == connection.id,
                BankAccount.provider_account_id == rev_id,
            ).first()
            
            balance = Decimal(str(rev_acc.get("balance", 0)))
            currency = rev_acc.get("currency", "EUR")
            name = rev_acc.get("name", f"Revolut {currency}")
            state = rev_acc.get("state", "active")
            
            if existing:
                # Update balance and metadata
                existing.balance = balance
                existing.available_balance = balance
                existing.balance_updated_at = datetime.utcnow()
                existing.account_name = name
                existing.currency = currency
                existing.is_active = state == "active"
                existing.bank_metadata = rev_acc
                flag_modified(existing, "bank_metadata")
            else:
                # Create new account
                new_account = BankAccount(
                    connection_id=connection.id,
                    workspace_id=connection.workspace_id,
                    account_name=name,
                    provider_account_id=rev_id,
                    account_type=_map_revolut_account_type(rev_acc),
                    currency=currency,
                    balance=balance,
                    available_balance=balance,
                    balance_updated_at=datetime.utcnow(),
                    is_active=state == "active",
                    is_visible=True,
                    bank_metadata=rev_acc,
                )
                db.add(new_account)
            
            accounts_synced += 1
        
        # Try to get bank details (IBAN) for each account
        for rev_acc in revolut_accounts:
            rev_id = rev_acc.get("id", "")
            try:
                details = await get_account_bank_details(access_token, rev_id)
                if details:
                    account = db.query(BankAccount).filter(
                        BankAccount.connection_id == connection.id,
                        BankAccount.provider_account_id == rev_id,
                    ).first()
                    if account and details.get("iban"):
                        from app.core.encryption import encrypt_iban
                        account.iban_encrypted = encrypt_iban(details["iban"])
                        # Show last 4 of IBAN
                        iban = details["iban"].replace(" ", "")
                        account.account_number_masked = f"****{iban[-4:]}"
            except Exception as e:
                logger.debug(f"Could not get bank details for account {rev_id}: {e}")
        
        # Update connection
        connection.last_sync_at = datetime.utcnow()
        connection.next_sync_at = datetime.utcnow() + timedelta(
            hours=connection.sync_frequency_hours or 12
        )
        
        # Complete sync log
        sync_log.status = SyncStatus.SUCCESS
        sync_log.completed_at = datetime.utcnow()
        sync_log.duration_ms = int(
            (sync_log.completed_at - sync_log.started_at).total_seconds() * 1000
        )
        sync_log.accounts_synced = accounts_synced
        
        if user_id:
            _add_audit_entry(connection, "revolut_accounts_synced", user_id,
                           f"{accounts_synced} accounts synced")
        
        db.commit()
        logger.info(f"Revolut sync completed: {accounts_synced} accounts for connection {connection.id}")
        return accounts_synced
    
    except RevolutTokenExpiredError:
        # Token refresh already attempted in _ensure_valid_token
        sync_log.status = SyncStatus.FAILED
        sync_log.completed_at = datetime.utcnow()
        sync_log.error_code = "TOKEN_EXPIRED"
        sync_log.error_message = "Token Revolut expiré. Reconnexion nécessaire."
        db.commit()
        raise
    
    except RevolutAPIError as e:
        sync_log.status = SyncStatus.FAILED
        sync_log.completed_at = datetime.utcnow()
        sync_log.error_code = f"REVOLUT_API_{e.status_code}"
        sync_log.error_message = str(e)
        connection.status = BankConnectionStatus.SYNC_ERROR
        connection.status_message = f"Erreur API Revolut: {e.status_code}"
        db.commit()
        raise
    
    except Exception as e:
        sync_log.status = SyncStatus.FAILED
        sync_log.completed_at = datetime.utcnow()
        sync_log.error_code = "UNKNOWN"
        sync_log.error_message = str(e)
        db.commit()
        raise


# ============================================================================
# TRANSACTIONS
# ============================================================================

async def fetch_revolut_transactions(
    db: Session,
    connection: BankConnection,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    account_id: Optional[str] = None,
    count: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch transactions from Revolut API.
    
    Returns raw transaction data from Revolut (not stored in DB).
    The frontend can display them directly.
    
    Each transaction has:
    - id, type, state, created_at, completed_at
    - reference (payment reference)
    - legs[]: account_id, amount, currency, description, balance
    - merchant: name, city, country (for card payments)
    """
    access_token = await _ensure_valid_token(db, connection)
    
    transactions = await revolut_get_transactions(
        access_token=access_token,
        from_date=from_date,
        to_date=to_date,
        account_id=account_id,
        count=count,
    )
    
    return transactions


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

def get_revolut_connection(db: Session, workspace_id: int) -> Optional[BankConnection]:
    """Get the Revolut connection for a workspace (if any)."""
    return db.query(BankConnection).filter(
        BankConnection.workspace_id == workspace_id,
        BankConnection.provider == REVOLUT_PROVIDER,
    ).first()


async def disconnect_revolut(
    db: Session,
    workspace_id: int,
    user_id: int,
) -> bool:
    """
    Disconnect Revolut from a workspace.
    Removes the connection and all associated data.
    """
    connection = get_revolut_connection(db, workspace_id)
    if not connection:
        return False
    
    connection_id = connection.id
    _add_audit_entry(connection, "revolut_disconnected", user_id)
    
    db.delete(connection)
    db.commit()
    
    logger.info(f"Revolut disconnected for workspace {workspace_id} (connection {connection_id})")
    return True


def get_revolut_status(db: Session, workspace_id: int) -> Dict[str, Any]:
    """Get Revolut connection status overview."""
    connection = get_revolut_connection(db, workspace_id)
    
    if not connection:
        return {
            "connected": False,
            "status": None,
            "accounts_count": 0,
            "last_sync_at": None,
        }
    
    accounts_count = db.query(BankAccount).filter(
        BankAccount.connection_id == connection.id,
        BankAccount.is_active == True,
    ).count()
    
    return {
        "connected": connection.status == BankConnectionStatus.CONNECTED,
        "connection_id": connection.id,
        "status": connection.status.value,
        "status_message": connection.status_message,
        "accounts_count": accounts_count,
        "last_sync_at": connection.last_sync_at,
        "connected_at": connection.connected_at,
    }
