"""
Opportunity schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from app.db.models.opportunity import (
    SourceType, OpportunityCategory, OpportunityStatus, TaskStatus
)


class OpportunityBase(BaseModel):
    """Base opportunity schema"""
    title: str = Field(..., max_length=500)
    category: OpportunityCategory = OpportunityCategory.OTHER
    organization: Optional[str] = None
    description: Optional[str] = None
    snippet: Optional[str] = Field(None, max_length=500)
    url_primary: Optional[str] = None
    urls_all: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: str = "FR"
    budget_amount: Optional[Decimal] = None
    budget_currency: str = "EUR"
    budget_hint: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_url: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    """Create opportunity schema (for manual creation)"""
    source_type: SourceType = SourceType.API
    source_name: str = "manual"


class OpportunityUpdate(BaseModel):
    """Update opportunity schema"""
    title: Optional[str] = Field(None, max_length=500)
    category: Optional[OpportunityCategory] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    snippet: Optional[str] = Field(None, max_length=500)
    url_primary: Optional[str] = None
    deadline_at: Optional[datetime] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    budget_hint: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_url: Optional[str] = None
    status: Optional[OpportunityStatus] = None
    assigned_to_user_id: Optional[int] = None
    possible_duplicate: Optional[bool] = None


class OpportunityResponse(OpportunityBase):
    """Opportunity response schema"""
    id: int
    external_id: str
    source_type: SourceType
    source_name: str
    score: int
    score_breakdown: Dict[str, Any]
    status: OpportunityStatus
    assigned_to_user_id: Optional[int] = None
    possible_duplicate: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    """Paginated opportunity list response"""
    items: List[OpportunityResponse]
    total: int
    page: int
    size: int
    pages: int


class OpportunityFilters(BaseModel):
    """Opportunity filter parameters"""
    status: Optional[OpportunityStatus] = None
    statuses: Optional[List[OpportunityStatus]] = None
    category: Optional[OpportunityCategory] = None
    categories: Optional[List[OpportunityCategory]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    region: Optional[str] = None
    source_name: Optional[str] = None
    source_type: Optional[SourceType] = None
    q: Optional[str] = None  # Search query
    deadline_before: Optional[datetime] = None
    deadline_after: Optional[datetime] = None
    min_budget: Optional[Decimal] = None
    max_budget: Optional[Decimal] = None
    assigned_to_user_id: Optional[int] = None
    has_budget: Optional[bool] = None
    created_after: Optional[datetime] = None


# Notes
class NoteCreate(BaseModel):
    """Create note schema"""
    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    """Note response schema"""
    id: int
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tasks
class TaskCreate(BaseModel):
    """Create task schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Update task schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    assigned_to_id: Optional[int] = None


class TaskResponse(BaseModel):
    """Task response schema"""
    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: TaskStatus
    assigned_to_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Tags
class TagCreate(BaseModel):
    """Create tag schema"""
    name: str = Field(..., max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class TagResponse(BaseModel):
    """Tag response schema"""
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


# Budget stats for histogram
class BudgetStatsResponse(BaseModel):
    """Budget statistics for histogram filter"""
    min_budget: Optional[Decimal] = None
    max_budget: Optional[Decimal] = None
    avg_budget: Optional[Decimal] = None
    count_with_budget: int
    total_count: int
    histogram: List[Dict[str, Any]]  # [{min, max, count}, ...]
