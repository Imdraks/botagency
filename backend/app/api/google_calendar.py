"""
Google Calendar Integration API
OAuth flow and calendar sync for deadlines
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from app.db import get_db
from app.db.models.user import User
from app.db.models.opportunity import Opportunity, OpportunityStatus
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/calendar/google", tags=["google-calendar"])

# OAuth state storage (use Redis in production)
_oauth_states: dict = {}

# Google Calendar API constants
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class CalendarConnectionStatus(BaseModel):
    connected: bool
    email: Optional[str] = None
    calendar_id: Optional[str] = None
    last_sync: Optional[str] = None


class CalendarEvent(BaseModel):
    id: Optional[str] = None
    summary: str
    description: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    all_day: bool = True
    reminder_minutes: int = 60


class SyncResult(BaseModel):
    success: bool
    events_created: int
    events_updated: int
    errors: List[str]


# ============================================================================
# OAUTH FLOW
# ============================================================================

@router.get("/init")
async def init_google_calendar_oauth(
    current_user: User = Depends(get_current_user),
):
    """
    Initialize Google Calendar OAuth flow.
    Returns the authorization URL to redirect the user to.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state with user ID
    _oauth_states[state] = {
        "user_id": current_user.id,
        "type": "calendar",
        "created_at": datetime.utcnow(),
    }
    
    # Use different redirect URI for calendar (vs login)
    redirect_uri = f"{settings.backend_url}/api/v1/calendar/google/callback"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_CALENDAR_SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def google_calendar_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Handle Google Calendar OAuth callback.
    Exchanges code for tokens and stores them for the user.
    """
    # Verify state
    stored_state = _oauth_states.pop(state, None)
    if not stored_state or stored_state.get("type") != "calendar":
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
    
    user_id = stored_state["user_id"]
    redirect_uri = f"{settings.backend_url}/api/v1/calendar/google/callback"
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            
            tokens = response.json()
        
        # Get user email from Google
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            user_info = user_info_response.json()
        
        # Store tokens in user record or separate table
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Store in user's extra data or a separate table
            # For now, we'll use a simple approach with user metadata
            if not hasattr(user, 'calendar_tokens'):
                # Add to user's settings/preferences
                pass
            
            # Store tokens securely (in production, encrypt these)
            from app.core.cache import cache_set
            cache_set(
                f"google_calendar_tokens:{user_id}",
                {
                    "access_token": tokens.get("access_token"),
                    "refresh_token": tokens.get("refresh_token"),
                    "expires_at": datetime.utcnow().timestamp() + tokens.get("expires_in", 3600),
                    "email": user_info.get("email"),
                },
                ttl=86400 * 30  # 30 days
            )
        
        # Redirect to frontend settings page with success
        return RedirectResponse(
            url=f"{settings.frontend_url}/settings?tab=calendar&connected=true"
        )
        
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.frontend_url}/settings?tab=calendar&error={str(e)}"
        )


@router.get("/status", response_model=CalendarConnectionStatus)
async def get_calendar_status(
    current_user: User = Depends(get_current_user),
):
    """Check if user has connected Google Calendar"""
    from app.core.cache import cache_get
    
    tokens = cache_get(f"google_calendar_tokens:{current_user.id}")
    
    if not tokens:
        return CalendarConnectionStatus(connected=False)
    
    # Check if token is expired
    if tokens.get("expires_at", 0) < datetime.utcnow().timestamp():
        # Token expired, try to refresh
        if tokens.get("refresh_token"):
            try:
                new_tokens = await refresh_google_token(tokens["refresh_token"])
                from app.core.cache import cache_set
                cache_set(
                    f"google_calendar_tokens:{current_user.id}",
                    {**tokens, **new_tokens},
                    ttl=86400 * 30
                )
                tokens = {**tokens, **new_tokens}
            except Exception:
                return CalendarConnectionStatus(connected=False)
        else:
            return CalendarConnectionStatus(connected=False)
    
    return CalendarConnectionStatus(
        connected=True,
        email=tokens.get("email"),
        calendar_id="primary",
        last_sync=None  # TODO: Track last sync time
    )


@router.delete("/disconnect")
async def disconnect_calendar(
    current_user: User = Depends(get_current_user),
):
    """Disconnect Google Calendar integration"""
    from app.core.cache import cache_delete
    cache_delete(f"google_calendar_tokens:{current_user.id}")
    return {"success": True, "message": "Google Calendar disconnected"}


# ============================================================================
# CALENDAR SYNC
# ============================================================================

@router.post("/sync")
async def sync_deadlines_to_calendar(
    opportunity_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncResult:
    """
    Sync opportunity deadlines to Google Calendar.
    If no IDs provided, syncs all active opportunities with deadlines.
    """
    from app.core.cache import cache_get
    
    tokens = cache_get(f"google_calendar_tokens:{current_user.id}")
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Calendar not connected"
        )
    
    # Get opportunities to sync
    query = db.query(Opportunity).filter(
        Opportunity.deadline_at.isnot(None),
        Opportunity.status.notin_([
            OpportunityStatus.WON,
            OpportunityStatus.LOST,
            OpportunityStatus.CANCELLED
        ])
    )
    
    if opportunity_ids:
        query = query.filter(Opportunity.id.in_(opportunity_ids))
    
    opportunities = query.limit(50).all()
    
    created = 0
    updated = 0
    errors = []
    
    access_token = tokens.get("access_token")
    
    async with httpx.AsyncClient() as client:
        for opp in opportunities:
            try:
                event_data = {
                    "summary": f"[Deadline] {opp.title[:50] if opp.title else 'Opportunité'}",
                    "description": f"Organisation: {opp.organization or 'N/A'}\nBudget: {opp.budget_amount or 'N/A'}€\nScore: {opp.score or 'N/A'}\n\nVoir: {settings.frontend_url}/leads/{opp.id}",
                    "start": {
                        "date": opp.deadline_at.strftime("%Y-%m-%d"),
                    },
                    "end": {
                        "date": (opp.deadline_at + timedelta(days=1)).strftime("%Y-%m-%d"),
                    },
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 1440},  # 1 day before
                            {"method": "popup", "minutes": 10080},  # 1 week before
                        ]
                    },
                    "transparency": "transparent",
                }
                
                # Check if event already exists (by searching)
                # For simplicity, we create new events each time
                # In production, store event IDs and update instead
                
                response = await client.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json=event_data,
                )
                
                if response.status_code in [200, 201]:
                    created += 1
                else:
                    errors.append(f"Failed to create event for {opp.id}: {response.text}")
                    
            except Exception as e:
                errors.append(f"Error syncing {opp.id}: {str(e)}")
    
    return SyncResult(
        success=len(errors) == 0,
        events_created=created,
        events_updated=updated,
        errors=errors[:5]  # Limit error messages
    )


@router.post("/sync-single/{opportunity_id}")
async def sync_single_deadline(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync a single opportunity deadline to Google Calendar"""
    result = await sync_deadlines_to_calendar(
        opportunity_ids=[opportunity_id],
        db=db,
        current_user=current_user,
    )
    return result


# ============================================================================
# HELPERS
# ============================================================================

async def refresh_google_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh an expired Google access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )
        
        if response.status_code != 200:
            raise ValueError("Failed to refresh token")
        
        tokens = response.json()
        return {
            "access_token": tokens.get("access_token"),
            "expires_at": datetime.utcnow().timestamp() + tokens.get("expires_in", 3600),
        }
