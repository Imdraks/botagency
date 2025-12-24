"""
Account model for SSO providers (Google, Apple)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Account(Base):
    """
    Account model for SSO providers.
    Links external OAuth providers to internal users.
    
    One user can have multiple accounts (Google + Apple + credentials).
    """
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Provider info
    provider = Column(String(50), nullable=False)  # 'google' | 'apple' | 'credentials'
    provider_account_id = Column(String(255), nullable=False)  # OIDC 'sub' claim (stable identifier)
    
    # Email from provider
    email = Column(String(255), nullable=True)  # May be masked for Apple Private Relay
    email_verified = Column(Boolean, default=False)
    
    # Tokens (only store if needed for API calls)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    id_token = Column(Text, nullable=True)
    expires_at = Column(BigInteger, nullable=True)  # Unix timestamp
    token_type = Column(String(50), nullable=True)
    scope = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    
    def __repr__(self):
        return f"<Account {self.provider}:{self.provider_account_id}>"
