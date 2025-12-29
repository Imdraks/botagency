"""
Source configuration schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.db.models.opportunity import SourceType


class SourceConfigBase(BaseModel):
    """Base source config schema"""
    name: str = Field(..., max_length=255)
    source_type: SourceType
    description: Optional[str] = None
    is_active: bool = True
    url: Optional[str] = None
    email_folder: Optional[str] = None
    email_sender_filter: Optional[str] = None
    html_selectors: Optional[Dict[str, Any]] = None
    api_headers: Optional[Dict[str, str]] = None
    api_params: Optional[Dict[str, str]] = None
    api_response_mapping: Optional[Dict[str, str]] = None
    poll_interval_minutes: int = 360


class SourceConfigCreate(SourceConfigBase):
    """Create source config schema"""
    pass


class SourceConfigUpdate(BaseModel):
    """Update source config schema"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    url: Optional[str] = None
    email_folder: Optional[str] = None
    email_sender_filter: Optional[str] = None
    html_selectors: Optional[Dict[str, Any]] = None
    api_headers: Optional[Dict[str, str]] = None
    api_params: Optional[Dict[str, str]] = None
    api_response_mapping: Optional[Dict[str, str]] = None
    poll_interval_minutes: Optional[int] = None


class SourceConfigResponse(SourceConfigBase):
    """Source config response schema"""
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    total_items_fetched: int
    total_errors: int
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceTestResult(BaseModel):
    """Result of testing a source"""
    success: bool
    message: str
    items_found: int = 0
    sample_items: list = Field(default_factory=list)
    errors: list = Field(default_factory=list)
