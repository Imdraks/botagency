"""
Email Whitelist Service
Checks if an email is authorized to register/login based on:
1. Workspace invitations
2. Allowed email domains
3. Specific allowed emails
"""
from typing import Tuple, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.workspace import WorkspaceInvite


def is_email_allowed(db: Session, email: str) -> Tuple[bool, str]:
    """
    Check if an email is allowed to register/login.
    
    Returns:
        Tuple of (is_allowed, reason)
        - (True, "invite") - Has pending workspace invite
        - (True, "domain") - Email domain is in allowed list
        - (True, "email") - Email is specifically allowed
        - (True, "disabled") - Whitelist is disabled
        - (False, "not_allowed") - Email is not authorized
    """
    email = email.lower().strip()
    
    # If whitelist is disabled, allow everyone
    if not settings.require_workspace_invite:
        return (True, "disabled")
    
    # Check allowed emails list
    if settings.allowed_emails:
        allowed_list = [e.strip().lower() for e in settings.allowed_emails.split(",") if e.strip()]
        if email in allowed_list:
            return (True, "email")
    
    # Check allowed domains
    if settings.allowed_email_domains:
        email_domain = email.split("@")[-1] if "@" in email else ""
        allowed_domains = [d.strip().lower() for d in settings.allowed_email_domains.split(",") if d.strip()]
        if email_domain in allowed_domains:
            return (True, "domain")
    
    # Check for pending workspace invite
    invite = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.email == email,
        WorkspaceInvite.claimed == False
    ).first()
    
    if invite:
        return (True, "invite")
    
    # Check if user already exists and has workspace membership
    from app.db.models.user import User
    from app.db.models.workspace import WorkspaceMember
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Existing user - check if they have any workspace membership
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == user.id
        ).first()
        if member:
            return (True, "existing_member")
        
        # Check if they're a workspace owner
        from app.db.models.workspace import Workspace
        workspace = db.query(Workspace).filter(Workspace.owner_user_id == user.id).first()
        if workspace:
            return (True, "workspace_owner")
    
    # Not allowed
    return (False, "not_allowed")


def get_pending_invites(db: Session, email: str) -> List[Dict[str, Any]]:
    """
    Get all pending workspace invites for an email.
    """
    email = email.lower().strip()
    
    invites = db.query(WorkspaceInvite).filter(
        WorkspaceInvite.email == email,
        WorkspaceInvite.claimed == False
    ).all()
    
    return [
        {
            "workspace_id": inv.workspace_id,
            "role": inv.role,
            "invited_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invites
    ]
