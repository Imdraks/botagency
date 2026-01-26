"""
Discovery V3 - SQLAlchemy Models
Complete data model for artist discovery, enrichment pipeline, and comparison features.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey,
    PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# ============================================================================
# ENUMS
# ============================================================================

class DataQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TimingBucket(str, Enum):
    IMMINENT = "IMMINENT"      # < 1 month
    ONE_THREE_MONTHS = "1_3M"   # 1-3 months
    THREE_SIX_MONTHS = "3_6M"   # 3-6 months
    SIX_TWELVE_MONTHS = "6_12M" # 6-12 months
    LONG = "LONG"              # > 12 months


class Recommendation(str, Enum):
    BOOK = "BOOK"
    WATCHLIST = "WATCHLIST"
    IGNORE = "IGNORE"


class CandidateType(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    TRENDING = "TRENDING"


class SnapshotSource(str, Enum):
    VIBERATE = "VIBERATE"
    SPOTIFY = "SPOTIFY"
    SOCIAL = "SOCIAL"


class SnapshotStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DONE = "DONE"


class JobStep(str, Enum):
    MATCH = "MATCH"
    VIBERATE = "VIBERATE"
    SPOTIFY = "SPOTIFY"
    COMPUTE = "COMPUTE"


class InputType(str, Enum):
    VIBERATE_URL = "VIBERATE_URL"
    SPOTIFY_URL = "SPOTIFY_URL"
    NAME = "NAME"


# ============================================================================
# 1. DISCOVERY ARTIST - Main entity
# ============================================================================

class DiscoveryArtist(Base):
    """
    Main artist entity for Discovery V3.
    One artist per workspace with deduplication.
    """
    __tablename__ = "discovery_artists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identity
    canonical_name = Column(String(500), nullable=False)
    normalized_name = Column(String(500), nullable=False, index=True)
    
    # External links
    viberate_url = Column(String(1000), nullable=True)
    spotify_artist_id = Column(String(50), nullable=True, index=True)
    instagram_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    image_url = Column(String(1000), nullable=True)
    
    # Metadata
    genres = Column(JSONB, nullable=True)  # List[str]
    country = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_enriched_at = Column(DateTime, nullable=True)
    
    # Quality
    data_quality = Column(String(20), nullable=False, default="LOW")
    last_quality_reason = Column(Text, nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    workspace = relationship("Workspace", backref="discovery_artists")
    snapshots = relationship("DiscoverySnapshot", back_populates="artist", cascade="all, delete-orphan")
    computed_metrics = relationship("DiscoveryComputedMetrics", back_populates="artist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DiscoveryArtist {self.canonical_name} ({self.id})>"
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize artist name for deduplication."""
        import unicodedata
        import re
        # Lowercase
        name = name.lower().strip()
        # Remove accents
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        # Remove special chars except spaces
        name = re.sub(r'[^a-z0-9\s]', '', name)
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        return name


# ============================================================================
# 2. DISCOVERY SNAPSHOT - Raw data storage
# ============================================================================

class DiscoverySnapshot(Base):
    """
    Raw data snapshot for audit and debugging.
    Stores raw responses from Viberate, Spotify, etc.
    """
    __tablename__ = "discovery_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Source info
    source = Column(String(50), nullable=False)  # VIBERATE | SPOTIFY | SOCIAL
    fetched_at = Column(DateTime, server_default=func.now(), nullable=False)
    ttl_expires_at = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False)  # OK | PARTIAL | FAILED
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Raw data
    raw_payload = Column(JSONB, nullable=True)
    parser_version = Column(String(50), nullable=True)
    
    # Relationships
    artist = relationship("DiscoveryArtist", back_populates="snapshots")
    
    def __repr__(self):
        return f"<DiscoverySnapshot {self.source} {self.status} ({self.id})>"
    
    def is_expired(self) -> bool:
        """Check if snapshot has expired."""
        return datetime.utcnow() > self.ttl_expires_at


# ============================================================================
# 3. DISCOVERY COMPUTED METRICS - Pre-computed for UI
# ============================================================================

class DiscoveryComputedMetrics(Base):
    """
    Pre-computed metrics consumed by the UI.
    Never recalculated on-demand, only via enrichment pipeline.
    """
    __tablename__ = "discovery_computed_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Core metrics
    score = Column(Integer, nullable=False, default=0)  # 0-100
    timing_bucket = Column(String(20), nullable=False, default="LONG")
    recommendation = Column(String(20), nullable=False, default="IGNORE")
    
    # Drivers & Penalties
    drivers = Column(JSONB, nullable=True)  # [{label, value, impact}]
    penalties = Column(JSONB, nullable=True)  # [{label, value, impact}]
    
    # Time series
    monthly_listeners_series = Column(JSONB, nullable=True)  # [{date, value}]
    velocity = Column(Float, nullable=True)
    acceleration = Column(Float, nullable=True)
    
    # Signals & Patterns
    signals = Column(JSONB, nullable=True)  # [{type, strength, evidenceUrl, detectedAt, source}]
    patterns = Column(JSONB, nullable=True)  # [{type, confidence}]
    
    # Fee estimation
    fee_estimate_min = Column(Integer, nullable=True)
    fee_estimate_max = Column(Integer, nullable=True)
    
    # Quality & Meta
    confidence_index = Column(Integer, nullable=True)
    data_quality = Column(String(20), nullable=False, default="LOW")
    last_updated_by_source = Column(JSONB, nullable=True)
    algo_version = Column(String(20), nullable=False, default="v3.0")
    
    # Raw metrics
    monthly_listeners = Column(Integer, nullable=True)
    spotify_followers = Column(Integer, nullable=True)
    instagram_followers = Column(Integer, nullable=True)
    tiktok_followers = Column(Integer, nullable=True)
    youtube_subscribers = Column(Integer, nullable=True)
    total_social_followers = Column(Integer, nullable=True)
    
    # Relationships
    artist = relationship("DiscoveryArtist", back_populates="computed_metrics")
    
    def __repr__(self):
        return f"<DiscoveryComputedMetrics score={self.score} reco={self.recommendation} ({self.id})>"
    
    def to_feed_dict(self) -> Dict[str, Any]:
        """Convert to lightweight dict for feed display."""
        return {
            "artistId": str(self.artist_id),
            "score": self.score,
            "timing": self.timing_bucket,
            "recommendation": self.recommendation,
            "driversTop2": (self.drivers or [])[:2],
            "dataQuality": self.data_quality,
            "lastUpdated": self.computed_at.isoformat() if self.computed_at else None,
            "monthlyListeners": self.monthly_listeners,
            "feeMin": self.fee_estimate_min,
            "feeMax": self.fee_estimate_max,
        }


# ============================================================================
# 4. DISCOVERY CANDIDATE - Materialized feed
# ============================================================================

class DiscoveryCandidate(Base):
    """
    Materialized view for Discovery page feed.
    Pre-computed by scheduled job, consumed read-only by UI.
    """
    __tablename__ = "discovery_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Feed type
    candidate_type = Column(String(20), nullable=False)  # RECOMMENDED | TRENDING
    rank_score = Column(Float, nullable=False, default=0)
    reasons = Column(JSONB, nullable=True)  # Top 2-3 reasons
    
    # Timestamps
    computed_at = Column(DateTime, server_default=func.now(), nullable=False)
    ttl_expires_at = Column(DateTime, nullable=False)
    
    # Segmentation (optional)
    segment_key = Column(String(100), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", backref="discovery_candidates")
    artist = relationship("DiscoveryArtist")
    
    def __repr__(self):
        return f"<DiscoveryCandidate {self.candidate_type} rank={self.rank_score:.2f} ({self.id})>"


# ============================================================================
# 5. COMPARISON LIST - Shortlists
# ============================================================================

class DiscoveryComparisonList(Base):
    """Shortlist for comparing artists."""
    __tablename__ = "discovery_comparison_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", backref="discovery_comparison_lists")
    creator = relationship("User", backref="discovery_comparison_lists")
    items = relationship("DiscoveryComparisonItem", back_populates="list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DiscoveryComparisonList '{self.name}' ({self.id})>"


# ============================================================================
# 6. COMPARISON ITEM - Items in shortlists
# ============================================================================

class DiscoveryComparisonItem(Base):
    """Item in a comparison shortlist."""
    __tablename__ = "discovery_comparison_items"
    __table_args__ = (
        PrimaryKeyConstraint('list_id', 'artist_id'),
    )

    list_id = Column(UUID(as_uuid=True), ForeignKey("discovery_comparison_lists.id", ondelete="CASCADE"), nullable=False)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    
    # Relationships
    list = relationship("DiscoveryComparisonList", back_populates="items")
    artist = relationship("DiscoveryArtist")
    
    def __repr__(self):
        return f"<DiscoveryComparisonItem list={self.list_id} artist={self.artist_id}>"


# ============================================================================
# 7. ENRICHMENT JOB - Job tracking for UI queue
# ============================================================================

class DiscoveryEnrichmentJob(Base):
    """
    Enrichment job tracking for UI queue panel.
    Tracks progress through MATCH -> VIBERATE -> SPOTIFY -> COMPUTE.
    """
    __tablename__ = "discovery_enrichment_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Input
    input_type = Column(String(50), nullable=False)  # VIBERATE_URL | SPOTIFY_URL | NAME
    input_value = Column(String(1000), nullable=False)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="SET NULL"), nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="QUEUED")
    current_step = Column(String(20), nullable=True)
    progress_pct = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Admin only
    logs_ref = Column(Text, nullable=True)
    celery_task_id = Column(String(100), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", backref="discovery_enrichment_jobs")
    requester = relationship("User", backref="discovery_enrichment_jobs")
    artist = relationship("DiscoveryArtist")
    
    def __repr__(self):
        return f"<DiscoveryEnrichmentJob {self.status} step={self.current_step} ({self.id})>"
    
    def to_queue_dict(self) -> Dict[str, Any]:
        """Convert to dict for queue panel display."""
        return {
            "id": str(self.id),
            "inputType": self.input_type,
            "inputValue": self.input_value,
            "artistId": str(self.artist_id) if self.artist_id else None,
            "status": self.status,
            "currentStep": self.current_step,
            "progressPct": self.progress_pct,
            "errorCode": self.error_code,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
    
    def update_progress(self, step: str, progress: int, status: str = None):
        """Update job progress."""
        self.current_step = step
        self.progress_pct = progress
        if status:
            self.status = status
        self.updated_at = datetime.utcnow()
    
    def mark_running(self, step: str = "MATCH"):
        """Mark job as running."""
        self.status = "RUNNING"
        self.current_step = step
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, partial: bool = False):
        """Mark job as completed."""
        self.status = "PARTIAL" if partial else "DONE"
        self.progress_pct = 100
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_code: str, error_message: str):
        """Mark job as failed."""
        self.status = "FAILED"
        self.error_code = error_code
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
