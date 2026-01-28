"""
Spotify Search Database Models
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    Float, Text, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SpotifyJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DONE = "DONE"


class SpotifyJobStep(str, Enum):
    SEARCH = "SEARCH"       # Search Spotify API
    ENRICH = "ENRICH"       # Enrich with Viberate data
    COMPLETE = "COMPLETE"   # Finalize results


class SpotifySearchJob(Base):
    """Job de recherche Spotify avec enrichissement"""
    
    __tablename__ = "spotify_search_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    # Search params
    query = Column(String(200), nullable=False)
    limit = Column(Integer, default=10)
    
    # Job status
    status = Column(String(20), default="QUEUED")
    current_step = Column(String(20), default="SEARCH")
    progress_pct = Column(Integer, default=0)
    celery_task_id = Column(String(100), nullable=True)
    
    # Results tracking
    results_count = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Relationships
    results = relationship("SpotifySearchResult", back_populates="job", cascade="all, delete-orphan")
    
    def mark_running(self, step: str = "SEARCH"):
        self.status = SpotifyJobStatus.RUNNING.value
        self.current_step = step
    
    def update_progress(self, step: str, pct: int):
        self.current_step = step
        self.progress_pct = min(pct, 100)
    
    def mark_completed(self, partial: bool = False, results_count: int = 0):
        self.status = SpotifyJobStatus.PARTIAL.value if partial else SpotifyJobStatus.DONE.value
        self.current_step = SpotifyJobStep.COMPLETE.value
        self.progress_pct = 100
        self.results_count = results_count
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error_code: str, message: str):
        self.status = SpotifyJobStatus.FAILED.value
        self.error_code = error_code
        self.error_message = message
        self.completed_at = datetime.utcnow()


class SpotifySearchResult(Base):
    """Résultat individuel d'une recherche Spotify"""
    
    __tablename__ = "spotify_search_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("spotify_search_jobs.id"), nullable=False)
    
    # Spotify data
    spotify_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    image_url = Column(Text, nullable=True)
    spotify_url = Column(Text, nullable=True)
    
    # Metrics
    followers = Column(Integer, default=0)
    popularity = Column(Integer, default=0)
    monthly_listeners = Column(Integer, nullable=True)
    monthly_listeners_source = Column(String(20), default="estimated")
    genres = Column(JSON, default=list)
    
    # Enrichment data
    label = Column(String(255), nullable=True)
    management = Column(String(255), nullable=True)
    social_stats = Column(JSON, nullable=True)
    
    # Ordering
    rank = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("SpotifySearchJob", back_populates="results")
