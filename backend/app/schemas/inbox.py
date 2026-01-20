"""
Pydantic Schemas for Inbox
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class InboxStatus(str, Enum):
    INBOX = "inbox"
    TRIAGED = "triaged"
    DONE = "done"
    ARCHIVED = "archived"


class InboxType(str, Enum):
    IDEA = "idea"
    REQUEST = "request"
    BUG = "bug"
    CONTENT = "content"
    TASK = "task"
    OTHER = "other"


class TriageTarget(str, Enum):
    """Where an inbox item can be triaged to"""
    TASK = "task"
    DEAL = "deal"
    PROJECT = "project"
    DELIVERABLE = "deliverable"


# ============================================================================
# INBOX ITEM
# ============================================================================

class InboxItemCreate(BaseModel):
    """
    Create inbox item with quick capture format.
    Supports: @client #project due:YYYY-MM-DD type:idea|request|bug|content
    """
    text: str = Field(..., min_length=1, max_length=5000)
    link: Optional[str] = Field(None, max_length=2000)
    
    # Optional manual classification (if not parsed from text)
    type: Optional[InboxType] = None
    tags: Optional[List[str]] = None
    due_date: Optional[date] = None


class InboxItemUpdate(BaseModel):
    """Update inbox item"""
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    link: Optional[str] = Field(None, max_length=2000)
    type: Optional[InboxType] = None
    tags: Optional[List[str]] = None
    status: Optional[InboxStatus] = None
    due_date: Optional[date] = None


class InboxItemResponse(BaseModel):
    id: int
    workspace_id: int
    created_by: int
    creator_name: Optional[str] = None
    
    # Content
    text: str
    link: Optional[str] = None
    
    # Classification
    type: InboxType
    tags: List[str] = []
    
    # Status
    status: InboxStatus
    
    # Due date
    due_date: Optional[date] = None
    
    # Parsed hints
    mentioned_client: Optional[str] = None
    mentioned_project: Optional[str] = None
    
    # Triage info
    triaged_to_type: Optional[str] = None
    triaged_to_id: Optional[int] = None
    triaged_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_overdue: bool = False
    age_hours: Optional[int] = None

    class Config:
        from_attributes = True


class InboxListResponse(BaseModel):
    items: List[InboxItemResponse]
    total: int
    inbox_count: int
    triaged_count: int
    done_count: int


# ============================================================================
# TRIAGE
# ============================================================================

class TriageRequest(BaseModel):
    """Triage inbox item to another entity"""
    target: TriageTarget
    
    # For TASK
    task_title: Optional[str] = None
    task_priority: Optional[str] = None  # low, medium, high
    task_assignee_id: Optional[int] = None
    task_project_id: Optional[int] = None
    task_due_date: Optional[date] = None
    
    # For DEAL
    deal_title: Optional[str] = None
    deal_client_id: Optional[int] = None
    deal_value: Optional[float] = None
    
    # For PROJECT
    project_name: Optional[str] = None
    project_client_id: Optional[int] = None
    project_deadline: Optional[date] = None
    
    # For DELIVERABLE
    deliverable_name: Optional[str] = None
    deliverable_project_id: Optional[int] = None
    deliverable_type: Optional[str] = None
    deliverable_due_date: Optional[date] = None


class TriageResponse(BaseModel):
    success: bool
    inbox_item_id: int
    triaged_to_type: str
    triaged_to_id: int
    message: str


# ============================================================================
# QUICK CAPTURE PARSING
# ============================================================================

class ParsedQuickCapture(BaseModel):
    """Result of parsing quick capture text"""
    original_text: str
    clean_text: str
    mentioned_client: Optional[str] = None
    mentioned_project: Optional[str] = None
    tags: List[str] = []
    due_date: Optional[date] = None
    type: InboxType = InboxType.OTHER
    suggested_actions: List[str] = []


class QuickCaptureTestRequest(BaseModel):
    """Test parsing of quick capture text"""
    text: str


class QuickCaptureTestResponse(BaseModel):
    """Response with parsed result"""
    parsed: ParsedQuickCapture
