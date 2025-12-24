"""
Ingestion endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models.user import User
from app.db.models.ingestion import IngestionRun, IngestionStatus
from app.db.models.source import SourceConfig
from app.schemas.ingestion import IngestionRunResponse, IngestionTriggerRequest
from app.api.deps import get_current_user, require_admin
from app.workers.tasks import run_ingestion_task, run_intelligent_search, analyze_artist_task

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


# Pydantic models for intelligent search
class IntelligentSearchRequest(BaseModel):
    """Request for intelligent search"""
    query: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    region: Optional[str] = None
    city: Optional[str] = None
    source_ids: Optional[List[str]] = None
    

class ArtistAnalysisRequest(BaseModel):
    """Request for artist analysis"""
    artist_name: str
    force_refresh: bool = True  # Toujours mettre à jour les infos de l'artiste


@router.get("/runs", response_model=List[IngestionRunResponse])
def list_ingestion_runs(
    source_id: UUID = None,
    status: IngestionStatus = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List ingestion runs"""
    query = db.query(IngestionRun)
    
    if source_id:
        query = query.filter(IngestionRun.source_config_id == source_id)
    if status:
        query = query.filter(IngestionRun.status == status)
    
    runs = query.order_by(desc(IngestionRun.started_at)).limit(limit).all()
    return runs


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
def get_ingestion_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get ingestion run by ID"""
    run = db.query(IngestionRun).filter(IngestionRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion run not found",
        )
    return run


@router.post("/run")
def trigger_ingestion(
    request: IngestionTriggerRequest = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Trigger ingestion manually with optional search parameters"""
    # Build list of sources to run
    query = db.query(SourceConfig).filter(SourceConfig.is_active == True)
    
    if request and request.source_ids:
        query = query.filter(SourceConfig.id.in_(request.source_ids))
    
    if request and request.source_types:
        query = query.filter(SourceConfig.source_type.in_(request.source_types))
    
    sources = query.all()
    
    if not sources:
        return {
            "message": "No active sources found matching criteria",
            "source_count": 0,
            "task_ids": [],
            "search_params": None,
        }
    
    # Extract search params if provided
    search_params = None
    if request and request.search_params:
        search_params = {
            "keywords": request.search_params.keywords,
            "region": request.search_params.region,
            "city": request.search_params.city,
            "budget_min": request.search_params.budget_min,
            "budget_max": request.search_params.budget_max,
        }
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
    
    # Queue ingestion tasks with search params
    task_ids = []
    for source in sources:
        task = run_ingestion_task.delay(str(source.id), search_params)
        task_ids.append(task.id)
    
    return {
        "message": f"Ingestion triggered for {len(sources)} sources",
        "source_count": len(sources),
        "task_ids": task_ids,
        "search_params": search_params,
    }


@router.post("/run/{source_id}")
def trigger_source_ingestion(
    source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Trigger ingestion for a specific source"""
    source = db.query(SourceConfig).filter(SourceConfig.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    
    task = run_ingestion_task.delay(str(source.id))
    
    return {
        "message": f"Ingestion triggered for source: {source.name}",
        "task_id": task.id,
    }


# ============================================
# INTELLIGENT SEARCH ENDPOINTS
# ============================================

@router.post("/intelligent-search")
def trigger_intelligent_search(
    request: IntelligentSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger an intelligent search using the AI-powered intelligence engine.
    
    This searches across all sources and uses advanced extraction for:
    - Prices and budgets
    - Contacts (email, phone, role)
    - Artist information (fees, events, trends)
    - Opportunity scoring
    """
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters",
        )
    
    # Build search params
    search_params = {}
    if request.budget_min is not None:
        search_params["budget_min"] = request.budget_min
    if request.budget_max is not None:
        search_params["budget_max"] = request.budget_max
    if request.region:
        search_params["region"] = request.region
    if request.city:
        search_params["city"] = request.city
    
    # Trigger the intelligent search task
    task = run_intelligent_search.delay(
        query=request.query.strip(),
        search_params=search_params if search_params else None,
        source_ids=request.source_ids,
    )
    
    return {
        "message": f"Intelligent search started for: {request.query}",
        "task_id": task.id,
        "query": request.query,
        "search_params": search_params,
    }


@router.post("/analyze-artist")
def trigger_artist_analysis(
    request: ArtistAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze an artist to get their estimated fee, recent events, and booking contacts.
    
    This is useful for:
    - Finding out how much an artist typically charges
    - Finding booking contacts
    - Understanding market positioning
    """
    if not request.artist_name or len(request.artist_name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artist name must be at least 2 characters",
        )
    
    task = analyze_artist_task.delay(request.artist_name.strip(), request.force_refresh)
    
    return {
        "message": f"Artist analysis started for: {request.artist_name}",
        "task_id": task.id,
        "artist_name": request.artist_name,
        "force_refresh": request.force_refresh,
    }


@router.get("/task/{task_id}")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the status and result of an async task (intelligent search, artist analysis, etc.)"""
    from app.workers.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        elif result.failed():
            response["error"] = str(result.result)
    
    return response
