"""
Profiles API - Fit Score par Profil
CRUD operations for profiles + score recomputation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import time

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.db.models import Profile, OpportunityProfileScore, Opportunity
from app.api.deps import get_current_user, get_current_admin_user
from app.schemas.radar_features import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
    OpportunityFitScore,
    RecomputeRequest,
    RecomputeResponse,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


def compute_fit_score(opportunity: Opportunity, profile: Profile) -> tuple[int, dict]:
    """
    Compute fit score for an opportunity against a profile.
    Returns (score, reasons_dict).
    """
    reasons = {
        "keyword_matches": [],
        "excluded": False,
        "budget_match": False,
        "deadline_soon": False,
        "contact_present": False,
        "location_match": False,
        "score_components": {},
    }
    
    weights = profile.weights or {
        "score_base": 0.4,
        "budget_match": 0.2,
        "deadline_proximity": 0.15,
        "contact_present": 0.15,
        "location_match": 0.1,
    }
    
    # Start with base score component
    base_score = opportunity.score or 0
    score_components = {"base": base_score * weights.get("score_base", 0.4)}
    
    # Check excluded keywords
    text_to_check = f"{opportunity.title or ''} {opportunity.description or ''} {opportunity.organization or ''}".lower()
    
    if profile.keywords_exclude:
        for keyword in profile.keywords_exclude:
            if keyword.lower() in text_to_check:
                reasons["excluded"] = True
                return 0, reasons
    
    # Check included keywords
    if profile.keywords_include:
        for keyword in profile.keywords_include:
            if keyword.lower() in text_to_check:
                reasons["keyword_matches"].append(keyword)
    
    # Budget match
    if profile.budget_min is not None or profile.budget_max is not None:
        if opportunity.budget_amount:
            budget_ok = True
            if profile.budget_min and opportunity.budget_amount < profile.budget_min:
                budget_ok = False
            if profile.budget_max and opportunity.budget_amount > profile.budget_max:
                budget_ok = False
            if budget_ok:
                reasons["budget_match"] = True
                score_components["budget"] = 100 * weights.get("budget_match", 0.2)
    
    # Deadline proximity (bonus if deadline is within 30 days)
    if opportunity.deadline_at:
        days_until = (opportunity.deadline_at - datetime.utcnow()).days
        if 0 < days_until <= 30:
            reasons["deadline_soon"] = True
            # More points for closer deadlines (but not past)
            deadline_score = max(0, min(100, (30 - days_until) / 30 * 100))
            score_components["deadline"] = deadline_score * weights.get("deadline_proximity", 0.15)
    
    # Contact present
    if opportunity.contact_email or opportunity.contact_phone:
        reasons["contact_present"] = True
        score_components["contact"] = 100 * weights.get("contact_present", 0.15)
    
    # Location match
    if profile.regions or profile.cities:
        location_match = False
        if opportunity.location_region and profile.regions:
            if opportunity.location_region.lower() in [r.lower() for r in profile.regions]:
                location_match = True
        if opportunity.location_city and profile.cities:
            if opportunity.location_city.lower() in [c.lower() for c in profile.cities]:
                location_match = True
        if location_match:
            reasons["location_match"] = True
            score_components["location"] = 100 * weights.get("location_match", 0.1)
    
    reasons["score_components"] = score_components
    
    # Calculate final score
    total_score = sum(score_components.values())
    fit_score = min(100, max(0, int(total_score)))
    
    return fit_score, reasons


@router.get("", response_model=ProfileListResponse)
def list_profiles(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List all profiles"""
    query = db.query(Profile)
    
    if is_active is not None:
        query = query.filter(Profile.is_active == is_active)
    
    profiles = query.order_by(Profile.name).all()
    
    return ProfileListResponse(
        profiles=[ProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles)
    )


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Create a new profile (admin only)"""
    # Check if name already exists
    existing = db.query(Profile).filter(Profile.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile with name '{data.name}' already exists"
        )
    
    profile = Profile(
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        keywords_include=data.keywords_include,
        keywords_exclude=data.keywords_exclude,
        regions=data.regions,
        cities=data.cities,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        objectives=data.objectives,
        weights=data.weights.model_dump() if data.weights else {},
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get a profile by ID"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.patch("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: UUID,
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Update a profile (admin only)"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle weights specially
    if "weights" in update_data and update_data["weights"]:
        update_data["weights"] = update_data["weights"].model_dump() if hasattr(update_data["weights"], "model_dump") else update_data["weights"]
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Delete a profile (admin only)"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    db.delete(profile)
    db.commit()


@router.post("/{profile_id}/recompute", response_model=RecomputeResponse)
def recompute_profile_scores(
    profile_id: UUID,
    data: RecomputeRequest = RecomputeRequest(),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Recompute fit scores for all opportunities against this profile"""
    start_time = time.time()
    
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Get opportunities to process
    query = db.query(Opportunity).filter(
        Opportunity.status.notin_(["ARCHIVED", "LOST"])
    )
    
    if data.only_new:
        # Only opportunities without a score for this profile
        existing_ids = db.query(OpportunityProfileScore.opportunity_id).filter(
            OpportunityProfileScore.profile_id == profile_id
        ).subquery()
        query = query.filter(~Opportunity.id.in_(existing_ids))
    
    opportunities = query.order_by(Opportunity.score.desc()).limit(data.limit).all()
    
    processed = 0
    for opp in opportunities:
        fit_score, reasons = compute_fit_score(opp, profile)
        
        # Upsert score
        existing_score = db.query(OpportunityProfileScore).filter(
            OpportunityProfileScore.opportunity_id == opp.id,
            OpportunityProfileScore.profile_id == profile_id
        ).first()
        
        if existing_score:
            existing_score.fit_score = fit_score
            existing_score.reasons = reasons
            existing_score.computed_at = datetime.utcnow()
        else:
            new_score = OpportunityProfileScore(
                opportunity_id=opp.id,
                profile_id=profile_id,
                fit_score=fit_score,
                reasons=reasons,
            )
            db.add(new_score)
        
        processed += 1
    
    db.commit()
    
    duration = time.time() - start_time
    
    return RecomputeResponse(
        profile_id=profile_id,
        opportunities_processed=processed,
        duration_seconds=round(duration, 2)
    )


@router.get("/{profile_id}/scores", response_model=list[OpportunityFitScore])
def get_profile_scores(
    profile_id: UUID,
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get top fit scores for a profile"""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    scores = db.query(OpportunityProfileScore).filter(
        OpportunityProfileScore.profile_id == profile_id,
        OpportunityProfileScore.fit_score >= min_score
    ).order_by(OpportunityProfileScore.fit_score.desc()).limit(limit).all()
    
    return [
        OpportunityFitScore(
            opportunity_id=s.opportunity_id,
            profile_id=s.profile_id,
            profile_name=profile.name,
            fit_score=s.fit_score,
            reasons=s.reasons,
            computed_at=s.computed_at,
        )
        for s in scores
    ]
