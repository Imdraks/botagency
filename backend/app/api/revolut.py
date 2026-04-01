"""
Revolut Banking API Endpoints
==============================

Dedicated endpoints for the Revolut Business API integration.
Mounted under /banking/revolut/...

Flow:
1. POST /banking/revolut/connect     → Get consent URL + start OAuth
2. GET  /banking/revolut/callback    → Handle OAuth redirect with ?code=...
3. POST /banking/revolut/sync        → Trigger manual account sync
4. GET  /banking/revolut/transactions → Fetch transactions from Revolut
5. GET  /banking/revolut/status      → Connection status
6. DELETE /banking/revolut/disconnect → Remove Revolut connection
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db import get_db
from app.api.deps import get_current_user, get_user_workspace_id
from app.db.models.user import User
from app.services.banking_service import (
    is_workspace_admin, is_workspace_member, is_banking_enabled,
)
from app.services.revolut_service import (
    initiate_revolut_oauth,
    complete_revolut_oauth,
    sync_revolut_accounts,
    fetch_revolut_transactions,
    get_revolut_connection,
    disconnect_revolut,
    get_revolut_status,
)
from app.services.revolut_client import RevolutAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class RevolutConnectResponse(BaseModel):
    """Response with OAuth consent URL."""
    consent_url: str
    connection_id: int
    message: str = "Redirigez l'utilisateur vers consent_url pour autoriser l'accès"


class RevolutCallbackRequest(BaseModel):
    """OAuth callback data (when used as POST)."""
    code: str


class RevolutCallbackResponse(BaseModel):
    """OAuth callback result."""
    connection_id: int
    status: str
    accounts_synced: int = 0
    message: str


class RevolutStatusResponse(BaseModel):
    """Revolut connection status."""
    connected: bool
    connection_id: Optional[int] = None
    status: Optional[str] = None
    status_message: Optional[str] = None
    accounts_count: int = 0
    last_sync_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None


class RevolutTransactionLeg(BaseModel):
    """A single leg of a Revolut transaction."""
    leg_id: Optional[str] = None
    account_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    balance: Optional[float] = None
    bill_amount: Optional[float] = None
    bill_currency: Optional[str] = None


class RevolutMerchant(BaseModel):
    """Merchant info for card payments."""
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    category_code: Optional[str] = None


class RevolutTransaction(BaseModel):
    """A Revolut transaction."""
    id: str
    type: str
    state: str
    request_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    reference: Optional[str] = None
    legs: List[RevolutTransactionLeg] = []
    merchant: Optional[RevolutMerchant] = None


class RevolutTransactionsResponse(BaseModel):
    """List of Revolut transactions."""
    transactions: List[RevolutTransaction] = []
    total: int = 0
    account_id: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class RevolutSyncResponse(BaseModel):
    """Sync result."""
    accounts_synced: int
    message: str


# ============================================================================
# HELPERS
# ============================================================================

def _require_banking(workspace_id: int, db: Session):
    if not is_banking_enabled(workspace_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La fonctionnalité bancaire n'est pas activée.",
        )


def _require_admin(user: User, workspace_id: int, db: Session):
    if not is_workspace_admin(user, workspace_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un administrateur peut gérer la connexion Revolut.",
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/banking/revolut/connect", response_model=RevolutConnectResponse)
def revolut_connect(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🔗 Start Revolut OAuth Connection
    
    Initiates the Revolut Business API OAuth flow.
    Returns a consent URL to redirect the user to.
    """
    _require_banking(workspace_id, db)
    _require_admin(current_user, workspace_id, db)
    
    try:
        consent_url, connection_id = initiate_revolut_oauth(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return RevolutConnectResponse(
        consent_url=consent_url,
        connection_id=connection_id,
    )


@router.get("/banking/revolut/callback")
async def revolut_oauth_callback(
    code: str = Query(..., description="Authorization code from Revolut"),
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    🔄 Revolut OAuth Callback
    
    Called by Revolut after user consents.
    This endpoint can be called directly by the browser redirect.
    
    In production, redirects the user back to the banking page.
    """
    # If no workspace_id in query, try to find the connecting workspace
    if not workspace_id:
        from app.db.models.banking import BankConnection, BankConnectionStatus
        connecting = db.query(BankConnection).filter(
            BankConnection.provider == "revolut",
            BankConnection.status == BankConnectionStatus.CONNECTING,
        ).order_by(BankConnection.updated_at.desc()).first()
        
        if connecting:
            workspace_id = connecting.workspace_id
        else:
            # Redirect to frontend with error
            frontend_url = settings.frontend_url
            return RedirectResponse(
                url=f"{frontend_url}/banking?revolut_error=no_connection"
            )
    
    # Find the user who initiated (from the connection's connected_by_id)
    from app.db.models.banking import BankConnection
    connection = db.query(BankConnection).filter(
        BankConnection.workspace_id == workspace_id,
        BankConnection.provider == "revolut",
    ).first()
    
    user_id = connection.connected_by_id if connection else None
    
    try:
        connection = await complete_revolut_oauth(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id or 0,
            authorization_code=code,
        )
        
        accounts_count = len(connection.accounts) if connection.accounts else 0
        
        # Redirect to banking page with success
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/banking?revolut_connected=true&accounts={accounts_count}"
        )
    
    except (RevolutAPIError, ValueError) as e:
        logger.error(f"Revolut OAuth callback failed: {e}")
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/banking?revolut_error={str(e)[:100]}"
        )


@router.post("/banking/revolut/callback", response_model=RevolutCallbackResponse)
async def revolut_oauth_callback_post(
    data: RevolutCallbackRequest,
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🔄 Revolut OAuth Callback (POST version)
    
    For SPA frontends that capture the code and POST it back.
    """
    _require_banking(workspace_id, db)
    _require_admin(current_user, workspace_id, db)
    
    try:
        connection = await complete_revolut_oauth(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
            authorization_code=data.code,
        )
        
        accounts_count = len(connection.accounts) if connection.accounts else 0
        
        return RevolutCallbackResponse(
            connection_id=connection.id,
            status=connection.status.value,
            accounts_synced=accounts_count,
            message=f"Revolut connecté avec succès. {accounts_count} compte(s) synchronisé(s).",
        )
    
    except RevolutAPIError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur Revolut: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/banking/revolut/status", response_model=RevolutStatusResponse)
def revolut_status(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    📊 Get Revolut Connection Status
    """
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    status_data = get_revolut_status(db, workspace_id)
    return RevolutStatusResponse(**status_data)


@router.post("/banking/revolut/sync", response_model=RevolutSyncResponse)
async def revolut_sync(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🔄 Trigger Revolut Account Sync
    
    Refreshes accounts and balances from Revolut API.
    """
    _require_banking(workspace_id, db)
    _require_admin(current_user, workspace_id, db)
    
    connection = get_revolut_connection(db, workspace_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Aucune connexion Revolut trouvée")
    
    if connection.status != "CONNECTED":
        raise HTTPException(
            status_code=400,
            detail=f"La connexion Revolut est en état '{connection.status.value}'. Impossible de synchroniser.",
        )
    
    try:
        accounts_synced = await sync_revolut_accounts(
            db=db,
            connection=connection,
            user_id=current_user.id,
        )
        return RevolutSyncResponse(
            accounts_synced=accounts_synced,
            message=f"{accounts_synced} compte(s) synchronisé(s) avec succès.",
        )
    
    except RevolutAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur API Revolut: {e}",
        )


@router.get("/banking/revolut/transactions", response_model=RevolutTransactionsResponse)
async def revolut_transactions(
    from_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    to_date: Optional[str] = Query(None, description="End date (ISO format)"),
    account_id: Optional[str] = Query(None, description="Filter by Revolut account ID"),
    count: int = Query(50, ge=1, le=1000),
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    💳 Fetch Revolut Transactions
    
    Retrieves transactions from the Revolut API in real-time.
    Supports date range filtering and account filtering.
    """
    _require_banking(workspace_id, db)
    if not is_workspace_member(current_user, workspace_id, db):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    connection = get_revolut_connection(db, workspace_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Aucune connexion Revolut trouvée")
    
    if connection.status != "CONNECTED":
        raise HTTPException(
            status_code=400,
            detail="La connexion Revolut n'est pas active.",
        )
    
    # Default: last 30 days
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    try:
        raw_transactions = await fetch_revolut_transactions(
            db=db,
            connection=connection,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            count=count,
        )
        
        # Map to response schema
        transactions = []
        for tx in raw_transactions:
            legs = []
            for leg in tx.get("legs", []):
                legs.append(RevolutTransactionLeg(
                    leg_id=leg.get("leg_id"),
                    account_id=leg.get("account_id"),
                    amount=leg.get("amount"),
                    currency=leg.get("currency"),
                    description=leg.get("description"),
                    balance=leg.get("balance"),
                    bill_amount=leg.get("bill_amount"),
                    bill_currency=leg.get("bill_currency"),
                ))
            
            merchant = None
            if tx.get("merchant"):
                m = tx["merchant"]
                merchant = RevolutMerchant(
                    name=m.get("name"),
                    city=m.get("city"),
                    country=m.get("country"),
                    category_code=m.get("category_code"),
                )
            
            transactions.append(RevolutTransaction(
                id=tx.get("id", ""),
                type=tx.get("type", "unknown"),
                state=tx.get("state", "unknown"),
                request_id=tx.get("request_id"),
                created_at=tx.get("created_at"),
                updated_at=tx.get("updated_at"),
                completed_at=tx.get("completed_at"),
                reference=tx.get("reference"),
                legs=legs,
                merchant=merchant,
            ))
        
        return RevolutTransactionsResponse(
            transactions=transactions,
            total=len(transactions),
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
        )
    
    except RevolutAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur API Revolut: {e}",
        )


@router.delete("/banking/revolut/disconnect")
async def revolut_disconnect_endpoint(
    workspace_id: int = Depends(get_user_workspace_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🔌 Disconnect Revolut
    
    Removes the Revolut connection and all associated data.
    """
    _require_banking(workspace_id, db)
    _require_admin(current_user, workspace_id, db)
    
    success = await disconnect_revolut(db, workspace_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Aucune connexion Revolut trouvée")
    
    return {"message": "Connexion Revolut supprimée avec succès"}
