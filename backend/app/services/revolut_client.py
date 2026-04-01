"""
Revolut Business API Client
============================

HTTP client for the Revolut Business API v1.0.
Handles JWT client-assertion generation, OAuth token exchange,
automatic token refresh, and all API calls.

Auth flow:
1. Generate JWT client assertion (signed with private key)
2. User consents via Revolut web app → receives auth code
3. Exchange auth code for access_token + refresh_token
4. Use Bearer access_token for API calls (expires in 40min)
5. Auto-refresh using refresh_token + JWT assertion

API Reference: https://developer.revolut.com/docs/business/business-api/
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import httpx
import jwt  # PyJWT

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

REVOLUT_PROD_BASE = "https://b2b.revolut.com/api/1.0"
REVOLUT_SANDBOX_BASE = "https://sandbox-b2b.revolut.com/api/1.0"

REVOLUT_PROD_AUTH = "https://business.revolut.com"
REVOLUT_SANDBOX_AUTH = "https://sandbox-business.revolut.com"

TOKEN_EXPIRY_BUFFER_SECONDS = 120  # Refresh 2 minutes before actual expiry


# ============================================================================
# JWT CLIENT ASSERTION
# ============================================================================

def _get_private_key() -> str:
    """Load the RSA private key for JWT signing."""
    key_path = settings.revolut_private_key_path
    if not key_path:
        raise ValueError("REVOLUT_PRIVATE_KEY_PATH is not configured")
    
    try:
        with open(key_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"Revolut private key not found at: {key_path}")


def generate_client_assertion(client_id: str) -> str:
    """
    Generate a JWT client assertion for Revolut OAuth.
    
    Header: {"alg": "RS256", "typ": "JWT"}
    Payload: {
        "iss": "<redirect_domain>",
        "sub": "<client_id>",
        "aud": "https://revolut.com",
        "exp": <timestamp>
    }
    """
    private_key = _get_private_key()
    
    # Extract domain from redirect URI for issuer
    redirect_uri = settings.revolut_redirect_uri or settings.backend_url
    # Use the domain part as issuer
    from urllib.parse import urlparse
    parsed = urlparse(redirect_uri)
    issuer = parsed.netloc or parsed.hostname or "radar.local"
    
    now = int(time.time())
    payload = {
        "iss": issuer,
        "sub": client_id,
        "aud": "https://revolut.com",
        "exp": now + 600,  # 10 minutes validity
        "iat": now,
    }
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


# ============================================================================
# API BASE URL HELPERS
# ============================================================================

def _get_api_base() -> str:
    """Get the Revolut API base URL based on environment."""
    if settings.revolut_sandbox:
        return REVOLUT_SANDBOX_BASE
    return REVOLUT_PROD_BASE


def _get_auth_base() -> str:
    """Get the Revolut auth base URL based on environment."""
    if settings.revolut_sandbox:
        return REVOLUT_SANDBOX_AUTH
    return REVOLUT_PROD_AUTH


# ============================================================================
# OAUTH FLOW
# ============================================================================

def get_consent_url(client_id: str, redirect_uri: str, scopes: str = "READ") -> str:
    """
    Build the Revolut consent URL where user authorizes the app.
    
    Args:
        client_id: The Revolut app ClientID
        redirect_uri: OAuth redirect URI registered in Revolut
        scopes: Comma-separated scopes (READ, WRITE, PAY)
    
    Returns:
        Full consent URL to redirect the user to
    """
    auth_base = _get_auth_base()
    url = (
        f"{auth_base}/app-confirm"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
    )
    return url


async def exchange_authorization_code(
    code: str,
    client_id: str,
) -> Dict[str, Any]:
    """
    Exchange an authorization code for access_token + refresh_token.
    
    POST /api/1.0/auth/token
    Content-Type: application/x-www-form-urlencoded
    
    Returns: {
        "access_token": "...",
        "token_type": "bearer",
        "expires_in": 2399,
        "refresh_token": "..."
    }
    """
    client_assertion = generate_client_assertion(client_id)
    api_base = _get_api_base()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": client_assertion,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code != 200:
        logger.error(f"Revolut token exchange failed: {response.status_code} - {response.text}")
        raise RevolutAPIError(
            f"Token exchange failed: {response.status_code}",
            status_code=response.status_code,
            detail=response.text,
        )
    
    data = response.json()
    logger.info("Revolut access token obtained successfully")
    return data


async def refresh_access_token(
    refresh_token: str,
    client_id: str,
) -> Dict[str, Any]:
    """
    Refresh an expired access token using the refresh token.
    
    Returns: {
        "access_token": "...",
        "token_type": "bearer",
        "expires_in": 2399
    }
    
    Note: refresh_token does not expire and is NOT returned again.
    """
    client_assertion = generate_client_assertion(client_id)
    api_base = _get_api_base()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/auth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": client_assertion,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    
    if response.status_code != 200:
        logger.error(f"Revolut token refresh failed: {response.status_code} - {response.text}")
        raise RevolutAPIError(
            f"Token refresh failed: {response.status_code}",
            status_code=response.status_code,
            detail=response.text,
        )
    
    data = response.json()
    logger.info("Revolut access token refreshed successfully")
    return data


# ============================================================================
# API CALLS
# ============================================================================

async def _api_request(
    method: str,
    path: str,
    access_token: str,
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
) -> Any:
    """Make an authenticated API request to Revolut."""
    api_base = _get_api_base()
    url = f"{api_base}{path}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method,
            url=url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            params=params,
            json=json_data,
        )
    
    if response.status_code == 401:
        raise RevolutTokenExpiredError("Access token expired")
    
    if response.status_code >= 400:
        logger.error(f"Revolut API error: {response.status_code} {method} {path} - {response.text}")
        raise RevolutAPIError(
            f"API error: {response.status_code}",
            status_code=response.status_code,
            detail=response.text,
        )
    
    return response.json()


async def get_accounts(access_token: str) -> List[Dict[str, Any]]:
    """
    GET /accounts - Retrieve all business accounts.
    
    Returns list of:
    {
        "id": "uuid",
        "name": "Current GBP account",
        "balance": 100.0,
        "currency": "GBP",
        "state": "active",
        "public": false,
        "created_at": "2022-08-05T14:29:22.215785Z",
        "updated_at": "2022-08-05T14:29:22.215785Z"
    }
    """
    return await _api_request("GET", "/accounts", access_token)


async def get_account(access_token: str, account_id: str) -> Dict[str, Any]:
    """GET /accounts/{id} - Retrieve a single account."""
    return await _api_request("GET", f"/accounts/{account_id}", access_token)


async def get_account_bank_details(access_token: str, account_id: str) -> Dict[str, Any]:
    """
    GET /accounts/{id}/bank-details - Get full bank details (IBAN, BIC, etc.)
    """
    return await _api_request("GET", f"/accounts/{account_id}/bank-details", access_token)


async def get_transactions(
    access_token: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    account_id: Optional[str] = None,
    count: int = 100,
    tx_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    GET /transactions - Retrieve historical transactions.
    
    Args:
        from_date: ISO datetime or date string
        to_date: ISO datetime or date string
        account_id: Filter by account UUID
        count: Max results per page (max 1000)
        tx_type: Filter by type (transfer, card_payment, etc.)
    
    Returns list of:
    {
        "id": "uuid",
        "type": "transfer" | "card_payment" | ...,
        "state": "pending" | "completed" | "declined" | "reverted" | "failed",
        "created_at": "...",
        "completed_at": "...",
        "reference": "invoice00912345",
        "legs": [{
            "leg_id": "uuid",
            "account_id": "uuid",
            "amount": -1.16,
            "currency": "EUR",
            "description": "To John Doe",
            "balance": 7.74
        }],
        "merchant": { "name": "...", "city": "...", "country": "..." },
        "card": { ... }
    }
    """
    params: Dict[str, Any] = {"count": min(count, 1000)}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if account_id:
        params["account"] = account_id
    if tx_type:
        params["type"] = tx_type
    
    return await _api_request("GET", "/transactions", access_token, params=params)


async def get_transaction(access_token: str, transaction_id: str) -> Dict[str, Any]:
    """GET /transactions/{id} - Retrieve a single transaction."""
    return await _api_request("GET", f"/transactions/{transaction_id}", access_token)


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RevolutAPIError(Exception):
    """General Revolut API error."""
    def __init__(self, message: str, status_code: int = 0, detail: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class RevolutTokenExpiredError(RevolutAPIError):
    """Token has expired, need to refresh."""
    def __init__(self, message: str = "Access token expired"):
        super().__init__(message, status_code=401, detail="")
