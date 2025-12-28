"""
Schemas for Radar Features APIs:
- Profiles
- Shortlists
- Clusters
- Deadline Alerts
- Source Health
- Contact Finder
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# PROFILES
# ============================================================================

class ProfileWeights(BaseModel):
    """Weights for fit score calculation"""
    score_base: float = 0.4
    budget_match: float = 0.2
    deadline_proximity: float = 0.15
    contact_present: float = 0.15
    location_match: float = 0.1


class ProfileBase(BaseModel):
    """Base profile schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    keywords_include: List[str] = []
    keywords_exclude: List[str] = []
    regions: List[str] = []
    cities: List[str] = []
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    objectives: List[str] = []
    weights: ProfileWeights = ProfileWeights()


class ProfileCreate(ProfileBase):
    """Schema for creating a profile"""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating a profile"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    keywords_include: Optional[List[str]] = None
    keywords_exclude: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    objectives: Optional[List[str]] = None
    weights: Optional[ProfileWeights] = None


class ProfileResponse(ProfileBase):
    """Profile response schema"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """List of profiles"""
    profiles: List[ProfileResponse]
    total: int


# ============================================================================
# OPPORTUNITY PROFILE SCORES
# ============================================================================

class OpportunityFitScore(BaseModel):
    """Fit score for an opportunity against a profile"""
    opportunity_id: UUID
    profile_id: UUID
    profile_name: str
    fit_score: int = Field(..., ge=0, le=100)
    reasons: Dict[str, Any] = {}
    computed_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DAILY SHORTLISTS
# ============================================================================

class ShortlistItem(BaseModel):
    """Single item in a shortlist"""
    opportunity_id: UUID
    title: str
    organization: Optional[str] = None
    score: int
    fit_score: int
    reasons: List[str]
    deadline_at: Optional[datetime] = None
    url: Optional[str] = None
    category: Optional[str] = None


class DailyShortlistResponse(BaseModel):
    """Daily shortlist response"""
    id: UUID
    date: date
    profile_id: UUID
    profile_name: str
    items: List[ShortlistItem]
    total_candidates: int
    items_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShortlistListResponse(BaseModel):
    """List of shortlists"""
    shortlists: List[DailyShortlistResponse]
    total: int


# ============================================================================
# CLUSTERS
# ============================================================================

class ClusterMember(BaseModel):
    """Member of a cluster"""
    opportunity_id: UUID
    title: str
    source_name: str
    url: Optional[str] = None
    similarity_score: float
    match_type: str


class ClusterResponse(BaseModel):
    """Cluster information for an opportunity"""
    cluster_id: UUID
    canonical_opportunity_id: UUID
    canonical_title: str
    member_count: int
    cluster_score: float
    members: List[ClusterMember]

    class Config:
        from_attributes = True


class ClusterRebuildResponse(BaseModel):
    """Response from cluster rebuild"""
    clusters_created: int
    clusters_updated: int
    opportunities_clustered: int
    duration_seconds: float


# ============================================================================
# DEADLINE ALERTS
# ============================================================================

class DeadlineAlertResponse(BaseModel):
    """Deadline alert information"""
    id: UUID
    opportunity_id: UUID
    opportunity_title: str
    organization: Optional[str] = None
    alert_type: str  # D7, D3, D1
    scheduled_for: datetime
    deadline_at: datetime
    status: str
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpcomingDeadlinesResponse(BaseModel):
    """List of upcoming deadline alerts"""
    alerts: List[DeadlineAlertResponse]
    total: int


class TestNotificationRequest(BaseModel):
    """Request to test deadline notification"""
    opportunity_id: UUID
    channel: str = "email"  # email, webhook


class TestNotificationResponse(BaseModel):
    """Response from test notification"""
    success: bool
    message: str
    channel: str


# ============================================================================
# SOURCE HEALTH
# ============================================================================

class SourceHealthMetrics(BaseModel):
    """Health metrics for a source"""
    source_id: UUID
    source_name: str
    date: date
    requests: int
    success_rate: float
    avg_latency_ms: int
    items_found: int
    items_kept: int
    items_new: int
    duplicates_rate: float
    health_score: int
    last_error: Optional[str] = None
    error_types: Dict[str, int] = {}

    class Config:
        from_attributes = True


class SourceHealthListResponse(BaseModel):
    """List of source health metrics"""
    sources: List[SourceHealthMetrics]
    total: int
    date_from: date
    date_to: date


class SourceHealthSummary(BaseModel):
    """Summary of source health"""
    source_id: UUID
    source_name: str
    is_active: bool
    avg_health_score: float
    total_items_last_7_days: int
    error_rate_last_7_days: float
    recommendation: Optional[str] = None  # "disable", "repair", "prioritize", null


class SourceHealthOverview(BaseModel):
    """Overview of all sources health"""
    sources: List[SourceHealthSummary]
    total_active: int
    total_inactive: int
    avg_health_score: float
    sources_needing_attention: int


class SourceUpdateRequest(BaseModel):
    """Request to update source status"""
    is_active: Optional[bool] = None


# ============================================================================
# CONTACT FINDER
# ============================================================================

class ContactFinderRequest(BaseModel):
    """Request to find contact for an opportunity"""
    search_official_first: bool = True
    max_pages: int = Field(default=5, ge=1, le=20)
    allowed_domains: Optional[List[str]] = None  # If None, use same-domain-first


class ContactFinderResponse(BaseModel):
    """Response from contact finder"""
    id: UUID
    opportunity_id: UUID
    status: str  # pending, found, not_found, error
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    evidence_url: Optional[str] = None
    evidence_snippet: Optional[str] = None
    evidence_domain: Optional[str] = None
    search_duration_ms: Optional[int] = None
    pages_crawled: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# COMMON / UTILITY
# ============================================================================

class RecomputeRequest(BaseModel):
    """Request to recompute scores for a profile"""
    limit: int = Field(default=1000, ge=1, le=10000)
    only_new: bool = True  # Only compute for opportunities without a score


class RecomputeResponse(BaseModel):
    """Response from recompute operation"""
    profile_id: UUID
    opportunities_processed: int
    duration_seconds: float
