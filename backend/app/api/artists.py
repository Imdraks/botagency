"""
Artists API - "Google des artistes" endpoints
Search-first approach with async analysis jobs
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, and_
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user, get_current_workspace
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.discovery import (
    DiscoveryArtist,
    DiscoveryComputedMetrics,
    DiscoveryEnrichmentJob,
    DiscoverySnapshot,
    JobStatus,
    InputType,
)
from app.db.models.artist_analysis import ArtistAnalysis
from app.workers.discovery_pipeline import run_enrichment_pipeline

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class AutocompleteItem(BaseModel):
    artist_id: Optional[str] = None  # UUID if from DB
    display_name: str
    avatar_url: Optional[str] = None
    sources: List[str] = []  # ["DB", "VIBERATE", "SPOTIFY"]
    viberate_url: Optional[str] = None
    spotify_artist_id: Optional[str] = None
    monthly_listeners: Optional[int] = None
    genre: Optional[str] = None
    country: Optional[str] = None
    status: str = "NEW"  # "ANALYZED" | "NEW"
    data_quality: Optional[str] = None  # "HIGH" | "MEDIUM" | "LOW"
    last_enriched_at: Optional[datetime] = None
    score: Optional[int] = None


class AutocompleteResponse(BaseModel):
    items: List[AutocompleteItem]
    query: str
    cached: bool = False


class SearchRequest(BaseModel):
    input_type: str = Field(..., regex="^(NAME|VIBERATE_URL|SPOTIFY_URL)$")
    input_value: str


class SearchCandidate(BaseModel):
    display_name: str
    viberate_url: Optional[str] = None
    spotify_artist_id: Optional[str] = None
    avatar_url: Optional[str] = None
    source: str


class SearchResponse(BaseModel):
    status: str  # "FOUND" | "RESOLVED" | "NEED_SELECTION" | "NOT_FOUND"
    artist_id: Optional[str] = None
    resolved: Optional[Dict[str, Any]] = None
    can_analyze: bool = False
    candidates: Optional[List[SearchCandidate]] = None


class AnalyzeRequest(BaseModel):
    resolved: Dict[str, Any]  # {viberate_url?, spotify_artist_id?, display_name?}


class AnalyzeResponse(BaseModel):
    status: str  # "JOB_CREATED" | "ALREADY_RUNNING" | "ERROR"
    job_id: Optional[str] = None
    artist_id: Optional[str] = None
    message: Optional[str] = None


class JobItem(BaseModel):
    id: str
    input_type: str
    input_value: str
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    status: str
    current_step: Optional[str] = None
    progress_pct: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobQueueResponse(BaseModel):
    jobs: List[JobItem]
    running_count: int
    pending_count: int
    completed_count: int


class HistoryItem(BaseModel):
    id: str
    artist_name: str
    image_url: Optional[str] = None
    genre: Optional[str] = None
    score: Optional[int] = None
    ai_tier: Optional[str] = None
    growth_trend: Optional[str] = None
    monthly_listeners: Optional[int] = None
    fee_min: Optional[int] = None
    fee_max: Optional[int] = None
    data_quality: Optional[str] = None
    last_enriched_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int


class ArtistStatistics(BaseModel):
    total_analyses: int
    unique_artists: int
    total_budget_min: int
    total_budget_max: int
    avg_budget_min: int
    avg_budget_max: int
    most_searched_artist: Optional[str] = None
    avg_score: Optional[float] = None


# =============================================================================
# HELPERS
# =============================================================================

def normalize_name(name: str) -> str:
    """Normalize artist name for search/deduplication."""
    name = name.lower().strip()
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def extract_spotify_id(url_or_id: str) -> Optional[str]:
    """Extract Spotify artist ID from URL or validate ID."""
    if re.match(r'^[a-zA-Z0-9]{22}$', url_or_id):
        return url_or_id
    match = re.search(r'artist/([a-zA-Z0-9]{22})', url_or_id)
    return match.group(1) if match else None


def extract_viberate_slug(url: str) -> Optional[str]:
    """Extract artist slug from Viberate URL."""
    match = re.search(r'viberate\.com/artist/([^/?#]+)', url)
    return match.group(1) if match else None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """
    Fast autocomplete for artist search.
    Returns DB results first, then external providers if needed.
    """
    items: List[AutocompleteItem] = []
    normalized_q = normalize_name(q)
    
    # 1) Search in DiscoveryArtist (DB)
    db_artists = db.query(DiscoveryArtist).filter(
        DiscoveryArtist.workspace_id == current_workspace.id,
        DiscoveryArtist.is_deleted == False,
        or_(
            DiscoveryArtist.normalized_name.ilike(f"%{normalized_q}%"),
            DiscoveryArtist.canonical_name.ilike(f"%{q}%"),
        )
    ).limit(limit).all()
    
    for artist in db_artists:
        # Get latest computed metrics
        metrics = db.query(DiscoveryComputedMetrics).filter(
            DiscoveryComputedMetrics.artist_id == artist.id
        ).order_by(desc(DiscoveryComputedMetrics.computed_at)).first()
        
        items.append(AutocompleteItem(
            artist_id=str(artist.id),
            display_name=artist.canonical_name,
            avatar_url=artist.image_url,
            sources=["DB"],
            viberate_url=artist.viberate_url,
            spotify_artist_id=artist.spotify_artist_id,
            monthly_listeners=metrics.monthly_listeners if metrics else None,
            genre=artist.genres[0] if artist.genres else None,
            country=artist.country,
            status="ANALYZED" if metrics else "NEW",
            data_quality=artist.data_quality,
            last_enriched_at=artist.last_enriched_at,
            score=metrics.score if metrics else None,
        ))
    
    # 2) Also check legacy ArtistAnalysis table
    if len(items) < limit:
        legacy = db.query(ArtistAnalysis).filter(
            ArtistAnalysis.workspace_id == current_workspace.id,
            ArtistAnalysis.artist_name.ilike(f"%{q}%"),
        ).limit(limit - len(items)).all()
        
        # Avoid duplicates
        existing_names = {normalize_name(i.display_name) for i in items}
        
        for analysis in legacy:
            if normalize_name(analysis.artist_name) not in existing_names:
                items.append(AutocompleteItem(
                    artist_id=None,  # Legacy, not in new system
                    display_name=analysis.artist_name,
                    avatar_url=analysis.image_url,
                    sources=["LEGACY"],
                    monthly_listeners=analysis.spotify_monthly_listeners,
                    genre=analysis.genre,
                    status="ANALYZED",
                    score=int(analysis.ai_score) if analysis.ai_score else None,
                ))
                existing_names.add(normalize_name(analysis.artist_name))
    
    return AutocompleteResponse(
        items=items[:limit],
        query=q,
        cached=False,
    )


@router.post("/search", response_model=SearchResponse)
async def search_artist(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """
    Search/resolve an artist from name or URL.
    Returns existing artist or resolution for analysis.
    """
    input_type = request.input_type
    input_value = request.input_value.strip()
    
    # Parse input
    spotify_artist_id = None
    viberate_url = None
    canonical_name = None
    normalized = None
    
    if input_type == "SPOTIFY_URL":
        spotify_artist_id = extract_spotify_id(input_value)
        if not spotify_artist_id:
            raise HTTPException(status_code=400, detail="Invalid Spotify URL or ID")
        
        # Check if exists in DB
        existing = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.workspace_id == current_workspace.id,
            DiscoveryArtist.spotify_artist_id == spotify_artist_id,
            DiscoveryArtist.is_deleted == False,
        ).first()
        
        if existing:
            return SearchResponse(
                status="FOUND",
                artist_id=str(existing.id),
                can_analyze=True,
            )
        
        return SearchResponse(
            status="RESOLVED",
            resolved={
                "spotify_artist_id": spotify_artist_id,
                "input_type": "SPOTIFY_URL",
            },
            can_analyze=True,
        )
    
    elif input_type == "VIBERATE_URL":
        viberate_url = input_value
        slug = extract_viberate_slug(input_value)
        if not slug:
            raise HTTPException(status_code=400, detail="Invalid Viberate URL")
        
        canonical_name = slug.replace("-", " ").title()
        
        # Check if exists
        existing = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.workspace_id == current_workspace.id,
            DiscoveryArtist.viberate_url == viberate_url,
            DiscoveryArtist.is_deleted == False,
        ).first()
        
        if existing:
            return SearchResponse(
                status="FOUND",
                artist_id=str(existing.id),
                can_analyze=True,
            )
        
        return SearchResponse(
            status="RESOLVED",
            resolved={
                "viberate_url": viberate_url,
                "display_name": canonical_name,
                "input_type": "VIBERATE_URL",
            },
            can_analyze=True,
        )
    
    else:  # NAME
        canonical_name = input_value
        normalized = normalize_name(input_value)
        
        # Search in DB (exact + fuzzy)
        exact = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.workspace_id == current_workspace.id,
            DiscoveryArtist.normalized_name == normalized,
            DiscoveryArtist.is_deleted == False,
        ).first()
        
        if exact:
            return SearchResponse(
                status="FOUND",
                artist_id=str(exact.id),
                can_analyze=True,
            )
        
        # Fuzzy search
        fuzzy = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.workspace_id == current_workspace.id,
            DiscoveryArtist.normalized_name.ilike(f"%{normalized}%"),
            DiscoveryArtist.is_deleted == False,
        ).limit(5).all()
        
        if len(fuzzy) == 1:
            return SearchResponse(
                status="FOUND",
                artist_id=str(fuzzy[0].id),
                can_analyze=True,
            )
        elif len(fuzzy) > 1:
            return SearchResponse(
                status="NEED_SELECTION",
                candidates=[
                    SearchCandidate(
                        display_name=a.canonical_name,
                        viberate_url=a.viberate_url,
                        spotify_artist_id=a.spotify_artist_id,
                        avatar_url=a.image_url,
                        source="DB",
                    )
                    for a in fuzzy
                ],
            )
        
        # Not found in DB - can analyze
        return SearchResponse(
            status="RESOLVED",
            resolved={
                "display_name": canonical_name,
                "input_type": "NAME",
            },
            can_analyze=True,
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_artist(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """
    Create an async analysis job for an artist.
    """
    resolved = request.resolved
    
    # Determine input type and value
    input_type = resolved.get("input_type", "NAME")
    input_value = (
        resolved.get("viberate_url") or 
        resolved.get("spotify_artist_id") or 
        resolved.get("display_name") or
        ""
    )
    
    if not input_value:
        raise HTTPException(status_code=400, detail="No valid input provided")
    
    # Check if there's already a running job for same input
    existing_job = db.query(DiscoveryEnrichmentJob).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
        DiscoveryEnrichmentJob.input_value == input_value,
        DiscoveryEnrichmentJob.status.in_(["QUEUED", "RUNNING"]),
    ).first()
    
    if existing_job:
        return AnalyzeResponse(
            status="ALREADY_RUNNING",
            job_id=str(existing_job.id),
            artist_id=str(existing_job.artist_id) if existing_job.artist_id else None,
            message="Une analyse est déjà en cours pour cet artiste",
        )
    
    # Create job
    job = DiscoveryEnrichmentJob(
        workspace_id=current_workspace.id,
        requested_by=current_user.id,
        input_type=input_type,
        input_value=input_value,
        status="QUEUED",
        progress_pct=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Queue the pipeline task
    run_enrichment_pipeline.delay(str(job.id))
    
    return AnalyzeResponse(
        status="JOB_CREATED",
        job_id=str(job.id),
    )


@router.get("/jobs", response_model=JobQueueResponse)
async def get_jobs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """
    Get recent analysis jobs for job queue panel.
    """
    # Recent jobs
    jobs = db.query(DiscoveryEnrichmentJob).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
    ).order_by(desc(DiscoveryEnrichmentJob.created_at)).limit(limit).all()
    
    # Counts
    running = db.query(func.count(DiscoveryEnrichmentJob.id)).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
        DiscoveryEnrichmentJob.status == "RUNNING",
    ).scalar() or 0
    
    pending = db.query(func.count(DiscoveryEnrichmentJob.id)).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
        DiscoveryEnrichmentJob.status == "QUEUED",
    ).scalar() or 0
    
    completed = db.query(func.count(DiscoveryEnrichmentJob.id)).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
        DiscoveryEnrichmentJob.status.in_(["DONE", "PARTIAL"]),
    ).scalar() or 0
    
    job_items = []
    for job in jobs:
        # Get artist name if linked
        artist_name = None
        if job.artist_id:
            artist = db.query(DiscoveryArtist).filter(
                DiscoveryArtist.id == job.artist_id
            ).first()
            if artist:
                artist_name = artist.canonical_name
        
        job_items.append(JobItem(
            id=str(job.id),
            input_type=job.input_type,
            input_value=job.input_value,
            artist_id=str(job.artist_id) if job.artist_id else None,
            artist_name=artist_name,
            status=job.status,
            current_step=job.current_step,
            progress_pct=job.progress_pct,
            error_code=job.error_code,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        ))
    
    return JobQueueResponse(
        jobs=job_items,
        running_count=running,
        pending_count=pending,
        completed_count=completed,
    )


@router.get("/jobs/{job_id}", response_model=JobItem)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """Get single job status."""
    job = db.query(DiscoveryEnrichmentJob).filter(
        DiscoveryEnrichmentJob.id == job_id,
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    artist_name = None
    if job.artist_id:
        artist = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.id == job.artist_id
        ).first()
        if artist:
            artist_name = artist.canonical_name
    
    return JobItem(
        id=str(job.id),
        input_type=job.input_type,
        input_value=job.input_value,
        artist_id=str(job.artist_id) if job.artist_id else None,
        artist_name=artist_name,
        status=job.status,
        current_step=job.current_step,
        progress_pct=job.progress_pct,
        error_code=job.error_code,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    genre: Optional[str] = None,
    level: Optional[str] = None,  # data_quality or tier
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """
    Get artist history table data.
    Combines DiscoveryArtist + DiscoveryComputedMetrics.
    """
    # Base query
    query = db.query(DiscoveryArtist).filter(
        DiscoveryArtist.workspace_id == current_workspace.id,
        DiscoveryArtist.is_deleted == False,
    )
    
    # Filters
    if search:
        normalized = normalize_name(search)
        query = query.filter(
            or_(
                DiscoveryArtist.normalized_name.ilike(f"%{normalized}%"),
                DiscoveryArtist.canonical_name.ilike(f"%{search}%"),
            )
        )
    
    if genre:
        query = query.filter(DiscoveryArtist.genres.contains([genre]))
    
    if level:
        query = query.filter(DiscoveryArtist.data_quality == level.upper())
    
    # Total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * per_page
    artists = query.order_by(desc(DiscoveryArtist.last_enriched_at)).offset(offset).limit(per_page).all()
    
    # Build items with metrics
    items = []
    for artist in artists:
        metrics = db.query(DiscoveryComputedMetrics).filter(
            DiscoveryComputedMetrics.artist_id == artist.id
        ).order_by(desc(DiscoveryComputedMetrics.computed_at)).first()
        
        items.append(HistoryItem(
            id=str(artist.id),
            artist_name=artist.canonical_name,
            image_url=artist.image_url,
            genre=artist.genres[0] if artist.genres else None,
            score=metrics.score if metrics else None,
            ai_tier=metrics.recommendation if metrics else None,
            growth_trend=metrics.timing_bucket if metrics else None,
            monthly_listeners=metrics.monthly_listeners if metrics else None,
            fee_min=metrics.fee_estimate_min if metrics else None,
            fee_max=metrics.fee_estimate_max if metrics else None,
            data_quality=artist.data_quality,
            last_enriched_at=artist.last_enriched_at,
            created_at=artist.created_at,
        ))
    
    total_pages = (total + per_page - 1) // per_page
    
    return HistoryResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/statistics", response_model=ArtistStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """Get KPI statistics for artist page."""
    # Count from new system
    total_new = db.query(func.count(DiscoveryArtist.id)).filter(
        DiscoveryArtist.workspace_id == current_workspace.id,
        DiscoveryArtist.is_deleted == False,
    ).scalar() or 0
    
    # Count from legacy
    total_legacy = db.query(func.count(func.distinct(ArtistAnalysis.artist_name))).filter(
        ArtistAnalysis.workspace_id == current_workspace.id,
    ).scalar() or 0
    
    total = total_new + total_legacy
    unique = total_new + total_legacy  # Approx, could dedupe
    
    # Budget from new metrics
    budget = db.query(
        func.sum(DiscoveryComputedMetrics.fee_estimate_min),
        func.sum(DiscoveryComputedMetrics.fee_estimate_max),
        func.avg(DiscoveryComputedMetrics.fee_estimate_min),
        func.avg(DiscoveryComputedMetrics.fee_estimate_max),
    ).join(
        DiscoveryArtist,
        DiscoveryComputedMetrics.artist_id == DiscoveryArtist.id
    ).filter(
        DiscoveryArtist.workspace_id == current_workspace.id,
    ).first()
    
    # Avg score
    avg_score = db.query(func.avg(DiscoveryComputedMetrics.score)).join(
        DiscoveryArtist,
        DiscoveryComputedMetrics.artist_id == DiscoveryArtist.id
    ).filter(
        DiscoveryArtist.workspace_id == current_workspace.id,
    ).scalar()
    
    # Most searched (from jobs)
    most_searched = db.query(
        DiscoveryEnrichmentJob.input_value,
        func.count(DiscoveryEnrichmentJob.id).label('cnt')
    ).filter(
        DiscoveryEnrichmentJob.workspace_id == current_workspace.id,
        DiscoveryEnrichmentJob.created_at >= datetime.utcnow() - timedelta(days=30),
    ).group_by(DiscoveryEnrichmentJob.input_value).order_by(desc('cnt')).first()
    
    return ArtistStatistics(
        total_analyses=total,
        unique_artists=unique,
        total_budget_min=int(budget[0] or 0) if budget else 0,
        total_budget_max=int(budget[1] or 0) if budget else 0,
        avg_budget_min=int(budget[2] or 0) if budget else 0,
        avg_budget_max=int(budget[3] or 0) if budget else 0,
        most_searched_artist=most_searched[0] if most_searched else None,
        avg_score=float(avg_score) if avg_score else None,
    )


@router.post("/{artist_id}/refresh", response_model=AnalyzeResponse)
async def refresh_artist(
    artist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """Refresh an artist's data (create new analysis job)."""
    artist = db.query(DiscoveryArtist).filter(
        DiscoveryArtist.id == artist_id,
        DiscoveryArtist.workspace_id == current_workspace.id,
    ).first()
    
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    # Create refresh job
    input_type = "VIBERATE_URL" if artist.viberate_url else "SPOTIFY_URL" if artist.spotify_artist_id else "NAME"
    input_value = artist.viberate_url or f"https://open.spotify.com/artist/{artist.spotify_artist_id}" or artist.canonical_name
    
    job = DiscoveryEnrichmentJob(
        workspace_id=current_workspace.id,
        requested_by=current_user.id,
        input_type=input_type,
        input_value=input_value,
        artist_id=artist.id,
        status="QUEUED",
        progress_pct=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    run_enrichment_pipeline.delay(str(job.id))
    
    return AnalyzeResponse(
        status="JOB_CREATED",
        job_id=str(job.id),
        artist_id=str(artist.id),
    )


@router.get("/{artist_id}")
async def get_artist(
    artist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    """Get full artist details."""
    artist = db.query(DiscoveryArtist).filter(
        DiscoveryArtist.id == artist_id,
        DiscoveryArtist.workspace_id == current_workspace.id,
    ).first()
    
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    
    metrics = db.query(DiscoveryComputedMetrics).filter(
        DiscoveryComputedMetrics.artist_id == artist.id
    ).order_by(desc(DiscoveryComputedMetrics.computed_at)).first()
    
    return {
        "id": str(artist.id),
        "canonical_name": artist.canonical_name,
        "image_url": artist.image_url,
        "viberate_url": artist.viberate_url,
        "spotify_artist_id": artist.spotify_artist_id,
        "genres": artist.genres,
        "country": artist.country,
        "data_quality": artist.data_quality,
        "last_enriched_at": artist.last_enriched_at,
        "created_at": artist.created_at,
        "metrics": {
            "score": metrics.score if metrics else None,
            "timing_bucket": metrics.timing_bucket if metrics else None,
            "recommendation": metrics.recommendation if metrics else None,
            "drivers": metrics.drivers if metrics else [],
            "penalties": metrics.penalties if metrics else [],
            "monthly_listeners": metrics.monthly_listeners if metrics else None,
            "spotify_followers": metrics.spotify_followers if metrics else None,
            "velocity": metrics.velocity if metrics else None,
            "acceleration": metrics.acceleration if metrics else None,
            "fee_estimate_min": metrics.fee_estimate_min if metrics else None,
            "fee_estimate_max": metrics.fee_estimate_max if metrics else None,
            "signals": metrics.signals if metrics else [],
            "patterns": metrics.patterns if metrics else [],
        } if metrics else None,
    }
