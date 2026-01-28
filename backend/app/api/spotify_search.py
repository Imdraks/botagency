"""
Spotify Search API Endpoints
Moteur de recherche Spotify avec queue d'analyses multiples
Similar to Discovery but focused on direct Spotify search results
"""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.api.deps import get_db, get_current_user, get_user_workspace_id
from app.db.models.user import User
from app.db.models.spotify_search import (
    SpotifySearchJob,
    SpotifySearchResult,
    SpotifyJobStatus,
    SpotifyJobStep,
)
from app.workers.spotify_search_pipeline import run_spotify_search_pipeline

router = APIRouter(prefix="/spotify-search", tags=["spotify-search"])


# ============================================================================
# SCHEMAS
# ============================================================================

class SpotifySearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    limit: int = Field(default=10, ge=1, le=50)


class SpotifyArtistResult(BaseModel):
    """Résultat d'artiste Spotify"""
    spotify_id: str
    name: str
    image_url: Optional[str] = None
    followers: int = 0
    popularity: int = 0
    genres: List[str] = []
    monthly_listeners: Optional[int] = None
    monthly_listeners_source: str = "estimated"
    spotify_url: Optional[str] = None
    # Enrichment data (if available)
    label: Optional[str] = None
    management: Optional[str] = None
    social_stats: Optional[dict] = None


class SpotifyJobResponse(BaseModel):
    id: str
    query: str
    status: str
    current_step: str
    progress: int = 0
    results_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SpotifySearchResultsResponse(BaseModel):
    job: SpotifyJobResponse
    results: List[SpotifyArtistResult] = []


class SpotifyQueueResponse(BaseModel):
    jobs: List[SpotifyJobResponse]
    running: int
    pending: int
    completed_24h: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/search", response_model=SpotifyJobResponse)
async def create_spotify_search(
    request: SpotifySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Lance une recherche Spotify avec enrichissement en background.
    Retourne immédiatement un job_id pour suivre le progress.
    """
    
    # Check for existing running job with same query
    running_job = db.query(SpotifySearchJob).filter(
        SpotifySearchJob.workspace_id == workspace_id,
        SpotifySearchJob.query == request.query,
        SpotifySearchJob.status.in_(["QUEUED", "RUNNING"]),
    ).first()
    
    if running_job:
        return SpotifyJobResponse(
            id=str(running_job.id),
            query=running_job.query,
            status=running_job.status,
            current_step=running_job.current_step,
            progress=running_job.progress_pct,
            results_count=running_job.results_count or 0,
            started_at=running_job.started_at,
        )
    
    # Create new search job
    job = SpotifySearchJob(
        workspace_id=workspace_id,
        query=request.query,
        limit=request.limit,
        status=SpotifyJobStatus.QUEUED.value,
        current_step=SpotifyJobStep.SEARCH.value,
        progress_pct=0,
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger async pipeline
    run_spotify_search_pipeline.delay(str(job.id))
    
    return SpotifyJobResponse(
        id=str(job.id),
        query=job.query,
        status=job.status,
        current_step=job.current_step,
        progress=0,
        results_count=0,
        started_at=job.started_at,
    )


@router.get("/job/{job_id}", response_model=SpotifySearchResultsResponse)
async def get_spotify_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Récupère le statut et les résultats d'un job de recherche Spotify.
    """
    
    job = db.query(SpotifySearchJob).filter(
        SpotifySearchJob.id == job_id,
        SpotifySearchJob.workspace_id == workspace_id,
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    # Get results if available
    results = []
    if job.status in ["DONE", "PARTIAL"]:
        db_results = db.query(SpotifySearchResult).filter(
            SpotifySearchResult.job_id == job.id
        ).order_by(SpotifySearchResult.rank).all()
        
        results = [
            SpotifyArtistResult(
                spotify_id=r.spotify_id,
                name=r.name,
                image_url=r.image_url,
                followers=r.followers or 0,
                popularity=r.popularity or 0,
                genres=r.genres or [],
                monthly_listeners=r.monthly_listeners,
                monthly_listeners_source=r.monthly_listeners_source or "estimated",
                spotify_url=r.spotify_url,
                label=r.label,
                management=r.management,
                social_stats=r.social_stats,
            )
            for r in db_results
        ]
    
    return SpotifySearchResultsResponse(
        job=SpotifyJobResponse(
            id=str(job.id),
            query=job.query,
            status=job.status,
            current_step=job.current_step,
            progress=job.progress_pct,
            results_count=len(results),
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        ),
        results=results,
    )


@router.get("/queue", response_model=SpotifyQueueResponse)
async def get_spotify_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Récupère la queue de recherches Spotify.
    """
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    jobs = db.query(SpotifySearchJob).filter(
        SpotifySearchJob.workspace_id == workspace_id,
        (SpotifySearchJob.status.in_(["QUEUED", "RUNNING"])) | 
        (SpotifySearchJob.started_at >= cutoff),
    ).order_by(desc(SpotifySearchJob.started_at)).limit(50).all()
    
    running = sum(1 for j in jobs if j.status == "RUNNING")
    pending = sum(1 for j in jobs if j.status == "QUEUED")
    completed = sum(1 for j in jobs if j.status in ["DONE", "PARTIAL"])
    
    return SpotifyQueueResponse(
        jobs=[
            SpotifyJobResponse(
                id=str(j.id),
                query=j.query,
                status=j.status,
                current_step=j.current_step,
                progress=j.progress_pct,
                results_count=j.results_count or 0,
                started_at=j.started_at,
                completed_at=j.completed_at,
                error_message=j.error_message,
            )
            for j in jobs
        ],
        running=running,
        pending=pending,
        completed_24h=completed,
    )


@router.delete("/job/{job_id}")
async def cancel_spotify_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Annule un job de recherche en attente.
    """
    
    job = db.query(SpotifySearchJob).filter(
        SpotifySearchJob.id == job_id,
        SpotifySearchJob.workspace_id == workspace_id,
        SpotifySearchJob.status == "QUEUED",
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé ou déjà en cours")
    
    job.status = SpotifyJobStatus.FAILED.value
    job.error_message = "Annulé par l'utilisateur"
    job.completed_at = datetime.utcnow()
    db.commit()
    
    return {"status": "cancelled", "job_id": job_id}


@router.post("/batch-search", response_model=List[SpotifyJobResponse])
async def batch_spotify_search(
    queries: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Lance plusieurs recherches Spotify en parallèle (batch).
    Maximum 20 recherches simultanées.
    """
    
    if len(queries) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 recherches simultanées")
    
    jobs = []
    for query in queries:
        if len(query.strip()) < 2:
            continue
        
        # Check existing
        existing = db.query(SpotifySearchJob).filter(
            SpotifySearchJob.workspace_id == workspace_id,
            SpotifySearchJob.query == query.strip(),
            SpotifySearchJob.status.in_(["QUEUED", "RUNNING"]),
        ).first()
        
        if existing:
            jobs.append(SpotifyJobResponse(
                id=str(existing.id),
                query=existing.query,
                status=existing.status,
                current_step=existing.current_step,
                progress=existing.progress_pct,
                results_count=existing.results_count or 0,
                started_at=existing.started_at,
            ))
            continue
        
        # Create new job
        job = SpotifySearchJob(
            workspace_id=workspace_id,
            query=query.strip(),
            limit=10,
            status=SpotifyJobStatus.QUEUED.value,
            current_step=SpotifyJobStep.SEARCH.value,
            progress_pct=0,
            started_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Trigger pipeline
        run_spotify_search_pipeline.delay(str(job.id))
        
        jobs.append(SpotifyJobResponse(
            id=str(job.id),
            query=job.query,
            status=job.status,
            current_step=job.current_step,
            progress=0,
            results_count=0,
            started_at=job.started_at,
        ))
    
    return jobs
