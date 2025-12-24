"""
SSO Authentication endpoints (Google + Apple)
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.db.models.user import User
from app.core.config import settings
from app.core.sso import SSOService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth/sso", tags=["sso"])


# State storage (in production, use Redis)
_oauth_states: dict = {}


class SSOInitResponse(BaseModel):
    """Response with OAuth authorization URL"""
    auth_url: str
    state: str


class SSOCallbackRequest(BaseModel):
    """Callback from OAuth provider"""
    code: str
    state: str
    id_token: Optional[str] = None  # Apple sends id_token in callback


class SSOTokenResponse(BaseModel):
    """Token response after successful SSO"""
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class LinkedAccountsResponse(BaseModel):
    """User's linked SSO accounts"""
    accounts: list


# ============================================
# GOOGLE SSO
# ============================================

@router.get("/google/init", response_model=SSOInitResponse)
async def google_sso_init(request: Request):
    """
    Initialize Google SSO flow.
    Returns the authorization URL to redirect the user to.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google SSO is not configured"
        )
    
    # Generate state and nonce for CSRF protection
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    
    # Store state (in production, use Redis with TTL)
    _oauth_states[state] = {
        "provider": "google",
        "nonce": nonce,
        "created_at": datetime.utcnow(),
    }
    
    redirect_uri = f"{settings.backend_url}/api/v1/auth/sso/google/callback"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "access_type": "offline",
        "prompt": "consent",
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return SSOInitResponse(auth_url=auth_url, state=state)


@router.get("/google/callback")
async def google_sso_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    Exchanges code for tokens and creates/links user account.
    """
    # Verify state
    stored_state = _oauth_states.pop(state, None)
    if not stored_state or stored_state["provider"] != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state"
        )
    
    # Check state age (max 10 minutes)
    if datetime.utcnow() - stored_state["created_at"] > timedelta(minutes=10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State expired"
        )
    
    sso_service = SSOService(db)
    redirect_uri = f"{settings.backend_url}/api/v1/auth/sso/google/callback"
    
    try:
        # Exchange code for tokens
        tokens = await sso_service.exchange_google_code(code, redirect_uri)
        
        # Decode ID token to get user info
        id_token = tokens.get("id_token")
        if not id_token:
            raise ValueError("No ID token in response")
        
        claims = sso_service.decode_google_id_token(id_token)
        
        # Extract user info from claims
        provider_account_id = claims["sub"]  # Stable Google ID
        email = claims.get("email")
        email_verified = claims.get("email_verified", False)
        name = claims.get("name")
        avatar_url = claims.get("picture")
        
        # Find or create user
        user, is_new = sso_service.find_or_create_user_from_sso(
            provider="google",
            provider_account_id=provider_account_id,
            email=email,
            email_verified=email_verified,
            name=name,
            avatar_url=avatar_url,
            tokens={
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "id_token": id_token,
                "expires_at": tokens.get("expires_in"),
            }
        )
        
        # Create session tokens
        session_tokens = sso_service.create_session_tokens(user)
        
        # Redirect to frontend with tokens
        frontend_callback = f"{settings.frontend_url}/auth/callback"
        params = {
            "access_token": session_tokens["access_token"],
            "refresh_token": session_tokens["refresh_token"],
            "is_new": "true" if is_new else "false",
        }
        
        return RedirectResponse(url=f"{frontend_callback}?{urlencode(params)}")
        
    except Exception as e:
        # Redirect to frontend with error
        error_url = f"{settings.frontend_url}/login?error={str(e)}"
        return RedirectResponse(url=error_url)


# ============================================
# APPLE SSO
# ============================================

@router.get("/apple/init", response_model=SSOInitResponse)
async def apple_sso_init(request: Request):
    """
    Initialize Apple SSO flow.
    Returns the authorization URL to redirect the user to.
    """
    if not settings.apple_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Apple SSO is not configured"
        )
    
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    
    _oauth_states[state] = {
        "provider": "apple",
        "nonce": nonce,
        "created_at": datetime.utcnow(),
    }
    
    redirect_uri = f"{settings.backend_url}/api/v1/auth/sso/apple/callback"
    
    params = {
        "client_id": settings.apple_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code id_token",
        "scope": "name email",
        "response_mode": "form_post",
        "state": state,
        "nonce": nonce,
    }
    
    auth_url = f"https://appleid.apple.com/auth/authorize?{urlencode(params)}"
    
    return SSOInitResponse(auth_url=auth_url, state=state)


@router.post("/apple/callback")
async def apple_sso_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Apple OAuth callback (POST with form data).
    Apple uses form_post response mode.
    """
    form_data = await request.form()
    
    code = form_data.get("code")
    state = form_data.get("state")
    id_token = form_data.get("id_token")
    user_data = form_data.get("user")  # Only on first consent
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state"
        )
    
    # Verify state
    stored_state = _oauth_states.pop(state, None)
    if not stored_state or stored_state["provider"] != "apple":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state"
        )
    
    sso_service = SSOService(db)
    redirect_uri = f"{settings.backend_url}/api/v1/auth/sso/apple/callback"
    
    try:
        # If we don't have id_token from callback, exchange code
        if not id_token:
            tokens = await sso_service.exchange_apple_code(code, redirect_uri)
            id_token = tokens.get("id_token")
        else:
            tokens = {"id_token": id_token}
        
        if not id_token:
            raise ValueError("No ID token received from Apple")
        
        # Decode ID token
        claims = sso_service.decode_apple_id_token(id_token)
        
        provider_account_id = claims["sub"]  # Stable Apple ID
        email = claims.get("email")  # May be private relay
        email_verified = claims.get("email_verified", False)
        
        # Parse user data (only available on first consent)
        name = None
        if user_data:
            import json
            try:
                user_info = json.loads(user_data)
                first_name = user_info.get("name", {}).get("firstName", "")
                last_name = user_info.get("name", {}).get("lastName", "")
                name = f"{first_name} {last_name}".strip() or None
            except json.JSONDecodeError:
                pass
        
        # Find or create user
        user, is_new = sso_service.find_or_create_user_from_sso(
            provider="apple",
            provider_account_id=provider_account_id,
            email=email,
            email_verified=email_verified,
            name=name,
            avatar_url=None,  # Apple doesn't provide avatar
            tokens=tokens
        )
        
        # Create session tokens
        session_tokens = sso_service.create_session_tokens(user)
        
        # Redirect to frontend
        frontend_callback = f"{settings.frontend_url}/auth/callback"
        params = {
            "access_token": session_tokens["access_token"],
            "refresh_token": session_tokens["refresh_token"],
            "is_new": "true" if is_new else "false",
        }
        
        return RedirectResponse(url=f"{frontend_callback}?{urlencode(params)}")
        
    except Exception as e:
        error_url = f"{settings.frontend_url}/login?error={str(e)}"
        return RedirectResponse(url=error_url)


# ============================================
# ACCOUNT MANAGEMENT
# ============================================

@router.get("/accounts", response_model=LinkedAccountsResponse)
async def get_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all SSO accounts linked to the current user"""
    sso_service = SSOService(db)
    accounts = sso_service.get_user_accounts(current_user.id)
    return LinkedAccountsResponse(accounts=accounts)


@router.delete("/accounts/{provider}")
async def unlink_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unlink an SSO account from the current user.
    User must have another authentication method available.
    """
    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider"
        )
    
    sso_service = SSOService(db)
    
    try:
        success = sso_service.unlink_account(current_user.id, provider)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return {"status": "success", "message": f"{provider} account unlinked"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/providers")
async def get_available_providers():
    """Get list of configured SSO providers"""
    providers = []
    
    if settings.google_client_id:
        providers.append({
            "id": "google",
            "name": "Google",
            "enabled": True,
        })
    
    if settings.apple_client_id:
        providers.append({
            "id": "apple", 
            "name": "Apple",
            "enabled": True,
        })
    
    return {"providers": providers}
