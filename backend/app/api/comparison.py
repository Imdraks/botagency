"""
Comparison API Endpoints
Handles shortlists (comparison lists) for artist comparison.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.api.deps import get_db, get_current_user, get_user_workspace_id
from app.db.models.user import User
from app.db.models.discovery import (
    DiscoveryArtist,
    DiscoveryComputedMetrics,
    DiscoveryComparisonList,
    DiscoveryComparisonItem,
)

router = APIRouter(prefix="/comparison", tags=["comparison"])


# ============================================================================
# SCHEMAS
# ============================================================================

class CreateListRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class UpdateListRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class AddArtistRequest(BaseModel):
    artist_id: int


class ComparisonListResponse(BaseModel):
    id: int
    name: str
    artist_count: int
    created_at: datetime
    updated_at: datetime


class ArtistComparisonData(BaseModel):
    """Full artist data for comparison view."""
    id: int
    name: str
    image_url: Optional[str] = None
    
    # Core metrics
    score: int = 0
    timing_bucket: Optional[str] = None
    timing_label: Optional[str] = None
    recommendation: Optional[str] = None
    
    # Audience
    monthly_listeners: Optional[int] = None
    followers: Optional[int] = None
    
    # Growth
    velocity: Optional[float] = None
    acceleration: Optional[float] = None
    
    # Qualitative
    data_quality: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    genres: List[str] = []
    
    # Analysis
    drivers: List[dict] = []
    risks: List[dict] = []
    signals: List[str] = []
    patterns: List[str] = []
    
    # Booking
    booking_range: Optional[dict] = None
    
    # Social (for radar chart)
    spotify_followers: Optional[int] = None
    instagram_followers: Optional[int] = None
    tiktok_followers: Optional[int] = None
    youtube_subscribers: Optional[int] = None
    
    # Status
    has_spotify: bool = False
    has_viberate: bool = False
    last_enriched_at: Optional[datetime] = None


class ComparisonListDetailResponse(BaseModel):
    id: int
    name: str
    artists: List[ArtistComparisonData]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# LIST CRUD
# ============================================================================

@router.get("/lists", response_model=List[ComparisonListResponse])
async def get_comparison_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Get all comparison lists (shortlists) for workspace.
    """
    
    lists = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).order_by(
        desc(DiscoveryComparisonList.updated_at)
    ).all()
    
    return [
        ComparisonListResponse(
            id=lst.id,
            name=lst.name,
            artist_count=len(lst.items) if lst.items else 0,
            created_at=lst.created_at,
            updated_at=lst.updated_at,
        )
        for lst in lists
    ]


@router.post("/lists", response_model=ComparisonListResponse)
async def create_comparison_list(
    request: CreateListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Create a new comparison list (shortlist).
    """
    
    new_list = DiscoveryComparisonList(
        workspace_id=workspace_id,
        name=request.name,
        created_by=current_user.id,
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    
    return ComparisonListResponse(
        id=new_list.id,
        name=new_list.name,
        artist_count=0,
        created_at=new_list.created_at,
        updated_at=new_list.updated_at,
    )


@router.get("/lists/{list_id}", response_model=ComparisonListDetailResponse)
async def get_comparison_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Get a comparison list with all artist data for comparison view.
    """
    
    comparison_list = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.id == list_id,
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).first()
    
    if not comparison_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    
    # Get all artists in the list with their metrics
    artists_data = []
    
    timing_labels = {
        "IMMINENT": "< 1 mois",
        "1_3M": "1-3 mois",
        "3_6M": "3-6 mois",
        "6_12M": "6-12 mois",
        "LONG": "> 12 mois",
    }
    
    for item in comparison_list.items:
        artist = item.artist
        if not artist or artist.is_deleted:
            continue
        
        # Get latest metrics
        metrics = db.query(DiscoveryComputedMetrics).filter(
            DiscoveryComputedMetrics.artist_id == artist.id,
            DiscoveryComputedMetrics.is_latest == True,
        ).first()
        
        artist_data = ArtistComparisonData(
            id=artist.id,
            name=artist.name,
            image_url=artist.image_url,
            
            score=metrics.score if metrics else 0,
            timing_bucket=metrics.timing_bucket if metrics else None,
            timing_label=timing_labels.get(metrics.timing_bucket) if metrics else None,
            recommendation=metrics.recommendation if metrics else None,
            
            monthly_listeners=metrics.monthly_listeners if metrics else None,
            followers=metrics.followers if metrics else None,
            
            velocity=metrics.velocity if metrics else None,
            acceleration=metrics.acceleration if metrics else None,
            
            data_quality=metrics.data_quality if metrics else None,
            country=artist.country,
            city=artist.city,
            genres=artist.genres or [],
            
            drivers=metrics.drivers if metrics else [],
            risks=metrics.risks if metrics else [],
            signals=metrics.signals if metrics else [],
            patterns=metrics.patterns if metrics else [],
            
            booking_range=metrics.booking_range if metrics else None,
            
            # Social metrics from snapshot if available
            spotify_followers=metrics.followers if metrics else None,
            instagram_followers=None,  # From viberate snapshot if available
            tiktok_followers=None,
            youtube_subscribers=None,
            
            has_spotify=artist.spotify_id is not None,
            has_viberate=artist.viberate_id is not None,
            last_enriched_at=artist.last_enriched_at,
        )
        artists_data.append(artist_data)
    
    return ComparisonListDetailResponse(
        id=comparison_list.id,
        name=comparison_list.name,
        artists=artists_data,
        created_at=comparison_list.created_at,
        updated_at=comparison_list.updated_at,
    )


@router.patch("/lists/{list_id}", response_model=ComparisonListResponse)
async def update_comparison_list(
    list_id: int,
    request: UpdateListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Update a comparison list (rename).
    """
    
    comparison_list = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.id == list_id,
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).first()
    
    if not comparison_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    
    if request.name:
        comparison_list.name = request.name
    
    comparison_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comparison_list)
    
    return ComparisonListResponse(
        id=comparison_list.id,
        name=comparison_list.name,
        artist_count=len(comparison_list.items) if comparison_list.items else 0,
        created_at=comparison_list.created_at,
        updated_at=comparison_list.updated_at,
    )


@router.delete("/lists/{list_id}")
async def delete_comparison_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Delete a comparison list.
    """
    
    comparison_list = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.id == list_id,
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).first()
    
    if not comparison_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    
    # Delete items first
    db.query(DiscoveryComparisonItem).filter(
        DiscoveryComparisonItem.list_id == list_id
    ).delete()
    
    # Delete list
    db.delete(comparison_list)
    db.commit()
    
    return {"status": "OK", "message": "Liste supprimée"}


# ============================================================================
# ARTIST MANAGEMENT IN LIST
# ============================================================================

@router.post("/lists/{list_id}/artists", response_model=ComparisonListResponse)
async def add_artist_to_list(
    list_id: int,
    request: AddArtistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Add an artist to a comparison list.
    Maximum 4 artists per list.
    """
    
    comparison_list = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.id == list_id,
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).first()
    
    if not comparison_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    
    # Check max 4 artists
    current_count = db.query(DiscoveryComparisonItem).filter(
        DiscoveryComparisonItem.list_id == list_id
    ).count()
    
    if current_count >= 4:
        raise HTTPException(
            status_code=400,
            detail="Maximum 4 artistes par liste de comparaison"
        )
    
    # Check artist exists
    artist = db.query(DiscoveryArtist).filter(
        DiscoveryArtist.id == request.artist_id,
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
    ).first()
    
    if not artist:
        raise HTTPException(status_code=404, detail="Artiste non trouvé")
    
    # Check if already in list
    existing = db.query(DiscoveryComparisonItem).filter(
        DiscoveryComparisonItem.list_id == list_id,
        DiscoveryComparisonItem.artist_id == request.artist_id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Artiste déjà dans la liste")
    
    # Add to list
    new_item = DiscoveryComparisonItem(
        list_id=list_id,
        artist_id=request.artist_id,
        position=current_count + 1,
    )
    db.add(new_item)
    
    comparison_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comparison_list)
    
    return ComparisonListResponse(
        id=comparison_list.id,
        name=comparison_list.name,
        artist_count=current_count + 1,
        created_at=comparison_list.created_at,
        updated_at=comparison_list.updated_at,
    )


@router.delete("/lists/{list_id}/artists/{artist_id}")
async def remove_artist_from_list(
    list_id: int,
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Remove an artist from a comparison list.
    """
    
    comparison_list = db.query(DiscoveryComparisonList).filter(
        DiscoveryComparisonList.id == list_id,
        DiscoveryComparisonList.workspace_id == workspace_id,
    ).first()
    
    if not comparison_list:
        raise HTTPException(status_code=404, detail="Liste non trouvée")
    
    item = db.query(DiscoveryComparisonItem).filter(
        DiscoveryComparisonItem.list_id == list_id,
        DiscoveryComparisonItem.artist_id == artist_id,
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Artiste non trouvé dans la liste")
    
    db.delete(item)
    comparison_list.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "OK", "message": "Artiste retiré de la liste"}


# ============================================================================
# QUICK COMPARE (without saving list)
# ============================================================================

@router.get("/compare", response_model=List[ArtistComparisonData])
async def compare_artists(
    artist_ids: str = Query(..., description="Comma-separated artist IDs (max 4)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
):
    """
    Quick compare artists by IDs without saving to a list.
    """
    
    # Parse IDs
    try:
        ids = [int(id.strip()) for id in artist_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artist IDs format")
    
    if len(ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 artistes pour la comparaison")
    
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Minimum 2 artistes pour la comparaison")
    
    # Get artists
    artists_data = []
    
    timing_labels = {
        "IMMINENT": "< 1 mois",
        "1_3M": "1-3 mois",
        "3_6M": "3-6 mois",
        "6_12M": "6-12 mois",
        "LONG": "> 12 mois",
    }
    
    for artist_id in ids:
        artist = db.query(DiscoveryArtist).filter(
            DiscoveryArtist.id == artist_id,
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
        ).first()
        
        if not artist:
            continue
        
        metrics = db.query(DiscoveryComputedMetrics).filter(
            DiscoveryComputedMetrics.artist_id == artist.id,
            DiscoveryComputedMetrics.is_latest == True,
        ).first()
        
        artist_data = ArtistComparisonData(
            id=artist.id,
            name=artist.name,
            image_url=artist.image_url,
            
            score=metrics.score if metrics else 0,
            timing_bucket=metrics.timing_bucket if metrics else None,
            timing_label=timing_labels.get(metrics.timing_bucket) if metrics else None,
            recommendation=metrics.recommendation if metrics else None,
            
            monthly_listeners=metrics.monthly_listeners if metrics else None,
            followers=metrics.followers if metrics else None,
            
            velocity=metrics.velocity if metrics else None,
            acceleration=metrics.acceleration if metrics else None,
            
            data_quality=metrics.data_quality if metrics else None,
            country=artist.country,
            city=artist.city,
            genres=artist.genres or [],
            
            drivers=metrics.drivers if metrics else [],
            risks=metrics.risks if metrics else [],
            signals=metrics.signals if metrics else [],
            patterns=metrics.patterns if metrics else [],
            
            booking_range=metrics.booking_range if metrics else None,
            
            has_spotify=artist.spotify_id is not None,
            has_viberate=artist.viberate_id is not None,
            last_enriched_at=artist.last_enriched_at,
        )
        artists_data.append(artist_data)
    
    return artists_data
