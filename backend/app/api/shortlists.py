"""
Shortlists API - Daily Picks / Auto-Shortlist
"""
from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.db.models import Profile, DailyShortlist, Opportunity, OpportunityProfileScore
from app.api.deps import get_current_user
from app.schemas.radar_features import (
    DailyShortlistResponse,
    ShortlistListResponse,
    ShortlistItem,
)

router = APIRouter(prefix="/shortlists", tags=["shortlists"])


def get_profile_name(db: Session, profile_id: UUID) -> str:
    """Get profile name by ID"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    return profile.name if profile else "Unknown"


@router.get("/today", response_model=Optional[DailyShortlistResponse])
def get_today_shortlist(
    profile_id: UUID = Query(..., description="Profile ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get today's shortlist for a profile"""
    today = date.today()
    
    shortlist = db.query(DailyShortlist).filter(
        DailyShortlist.date == today,
        DailyShortlist.profile_id == profile_id
    ).first()
    
    if not shortlist:
        # Try yesterday if today not generated yet
        yesterday = today - timedelta(days=1)
        shortlist = db.query(DailyShortlist).filter(
            DailyShortlist.date == yesterday,
            DailyShortlist.profile_id == profile_id
        ).first()
    
    if not shortlist:
        return None
    
    profile_name = get_profile_name(db, profile_id)
    
    return DailyShortlistResponse(
        id=shortlist.id,
        date=shortlist.date,
        profile_id=shortlist.profile_id,
        profile_name=profile_name,
        items=[ShortlistItem(**item) for item in (shortlist.items or [])],
        total_candidates=shortlist.total_candidates,
        items_count=shortlist.items_count,
        created_at=shortlist.created_at,
    )


@router.get("", response_model=ShortlistListResponse)
def list_shortlists(
    profile_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List shortlists with optional filters"""
    query = db.query(DailyShortlist)
    
    if profile_id:
        query = query.filter(DailyShortlist.profile_id == profile_id)
    
    if date_from:
        query = query.filter(DailyShortlist.date >= date_from)
    
    if date_to:
        query = query.filter(DailyShortlist.date <= date_to)
    
    shortlists = query.order_by(DailyShortlist.date.desc()).limit(limit).all()
    
    # Get profile names
    profile_ids = list(set(s.profile_id for s in shortlists))
    profiles = {p.id: p.name for p in db.query(Profile).filter(Profile.id.in_(profile_ids)).all()}
    
    return ShortlistListResponse(
        shortlists=[
            DailyShortlistResponse(
                id=s.id,
                date=s.date,
                profile_id=s.profile_id,
                profile_name=profiles.get(s.profile_id, "Unknown"),
                items=[ShortlistItem(**item) for item in (s.items or [])],
                total_candidates=s.total_candidates,
                items_count=s.items_count,
                created_at=s.created_at,
            )
            for s in shortlists
        ],
        total=len(shortlists)
    )


@router.get("/{shortlist_id}", response_model=DailyShortlistResponse)
def get_shortlist(
    shortlist_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get a specific shortlist by ID"""
    shortlist = db.query(DailyShortlist).filter(DailyShortlist.id == shortlist_id).first()
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    profile_name = get_profile_name(db, shortlist.profile_id)
    
    return DailyShortlistResponse(
        id=shortlist.id,
        date=shortlist.date,
        profile_id=shortlist.profile_id,
        profile_name=profile_name,
        items=[ShortlistItem(**item) for item in (shortlist.items or [])],
        total_candidates=shortlist.total_candidates,
        items_count=shortlist.items_count,
        created_at=shortlist.created_at,
    )


@router.post("/generate", response_model=DailyShortlistResponse)
def generate_shortlist(
    profile_id: UUID = Query(..., description="Profile ID"),
    target_date: Optional[date] = None,
    limit: int = Query(default=20, ge=5, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Manually generate a shortlist for a profile"""
    from app.api.profiles import compute_fit_score
    
    target_date = target_date or date.today()
    
    # Check if profile exists
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Delete existing shortlist for this date/profile
    existing = db.query(DailyShortlist).filter(
        DailyShortlist.date == target_date,
        DailyShortlist.profile_id == profile_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    
    # Get candidate opportunities (active, not archived)
    candidates = db.query(Opportunity).filter(
        Opportunity.status.notin_(["ARCHIVED", "LOST", "WON"]),
    ).order_by(Opportunity.score.desc()).limit(500).all()
    
    # Compute fit scores and build shortlist
    scored_items = []
    for opp in candidates:
        fit_score, reasons = compute_fit_score(opp, profile)
        
        if fit_score > 0:  # Skip excluded opportunities
            scored_items.append({
                "opportunity": opp,
                "fit_score": fit_score,
                "reasons": reasons,
            })
    
    # Sort by fit_score descending
    scored_items.sort(key=lambda x: x["fit_score"], reverse=True)
    
    # Build shortlist items
    shortlist_items = []
    for item in scored_items[:limit]:
        opp = item["opportunity"]
        reasons_list = []
        r = item["reasons"]
        
        if r.get("budget_match"):
            reasons_list.append("budget_match")
        if r.get("deadline_soon"):
            reasons_list.append("deadline_soon")
        if r.get("contact_present"):
            reasons_list.append("contact_present")
        if r.get("location_match"):
            reasons_list.append("location_match")
        if r.get("keyword_matches"):
            reasons_list.append("keyword_match")
        if opp.score and opp.score >= 70:
            reasons_list.append("score_high")
        
        shortlist_items.append({
            "opportunity_id": str(opp.id),
            "title": opp.title,
            "organization": opp.organization,
            "score": opp.score or 0,
            "fit_score": item["fit_score"],
            "reasons": reasons_list,
            "deadline_at": opp.deadline_at.isoformat() if opp.deadline_at else None,
            "url": opp.url_primary,
            "category": opp.category.value if opp.category else None,
        })
    
    # Create shortlist
    shortlist = DailyShortlist(
        date=target_date,
        profile_id=profile_id,
        items=shortlist_items,
        total_candidates=len(candidates),
        items_count=len(shortlist_items),
    )
    
    db.add(shortlist)
    db.commit()
    db.refresh(shortlist)
    
    return DailyShortlistResponse(
        id=shortlist.id,
        date=shortlist.date,
        profile_id=shortlist.profile_id,
        profile_name=profile.name,
        items=[ShortlistItem(**item) for item in shortlist_items],
        total_candidates=shortlist.total_candidates,
        items_count=shortlist.items_count,
        created_at=shortlist.created_at,
    )
