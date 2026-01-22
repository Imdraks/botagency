"""
Authentication dependencies
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models.user import User, Role
from app.core.security import verify_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


def require_workspace_member(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Require user to be a member of at least one workspace.
    Returns user with workspace_id attribute attached.
    """
    from app.db.models.workspace import WorkspaceMember
    
    # Admin/superuser can proceed (they can access any workspace)
    if current_user.is_superuser or current_user.role == Role.ADMIN:
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user.id
        ).first()
        current_user.workspace_id = member.workspace_id if member else None
        return current_user
    
    # Regular user must be a member of at least one workspace
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NO_WORKSPACE_ACCESS",
            headers={"X-Error-Code": "NO_WORKSPACE_ACCESS"},
        )
    
    # Attach workspace_id to user for convenience
    current_user.workspace_id = member.workspace_id
    return current_user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


class RoleChecker:
    """Role-based access control dependency"""
    
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


# Pre-configured role checkers
require_admin = RoleChecker([Role.ADMIN])
require_bizdev = RoleChecker([Role.ADMIN, Role.BIZDEV])
require_pm = RoleChecker([Role.ADMIN, Role.BIZDEV, Role.PM])
require_viewer = RoleChecker([Role.ADMIN, Role.BIZDEV, Role.PM, Role.VIEWER])


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user only if admin or superuser"""
    if not current_user.is_superuser and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_user_workspace_id(
    workspace_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Get the workspace_id for the current user.
    - If workspace_id is provided, validate user has access
    - If not provided, get user's primary workspace
    - Global admins can access any workspace
    """
    from app.db.models.workspace import WorkspaceMember
    
    # Global admin can access any workspace
    if current_user.role == Role.ADMIN or current_user.is_superuser:
        if workspace_id:
            return workspace_id
        # For admin without workspace_id, return first workspace or None
        first_member = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user.id
        ).first()
        if first_member:
            return first_member.workspace_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No workspace found. Please specify workspace_id.",
        )
    
    # Regular user - check access
    if workspace_id:
        has_access = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.workspace_id == workspace_id
        ).first()
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace",
            )
        return workspace_id
    
    # No workspace_id provided - get user's primary/only workspace
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of any workspace",
        )
    return member.workspace_id


def get_current_workspace(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current workspace for the authenticated user.
    Returns the Workspace object.
    """
    from app.db.models.workspace import Workspace, WorkspaceMember
    
    # Find the user's workspace membership
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NO_WORKSPACE_ACCESS",
            headers={"X-Error-Code": "NO_WORKSPACE_ACCESS"},
        )
    
    workspace = db.query(Workspace).filter(Workspace.id == member.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    
    return workspace
