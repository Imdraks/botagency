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
