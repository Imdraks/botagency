"""
User schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import Role


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None
    role: Role = Role.VIEWER
    is_active: bool = True


class UserCreate(UserBase):
    """Create user schema"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Update user schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    is_whitelisted: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class LinkedAccountResponse(BaseModel):
    """Linked SSO account"""
    provider: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_superuser: bool
    is_whitelisted: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None
    auth_provider: Optional[str] = None
    avatar_url: Optional[str] = None
    linked_accounts: List[LinkedAccountResponse] = []

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str
    totp_code: Optional[str] = None  # 2FA code if enabled


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Login response - either tokens or 2FA required"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    temp_token: Optional[str] = None  # Temporary token to complete 2FA


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: str
    type: str
    exp: datetime
