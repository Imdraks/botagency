"""
Scoring rules endpoints + Artist scoring API
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db import get_db
from app.db.models.user import User
from app.db.models.scoring import ScoringRule, RuleType
from app.schemas.scoring import (
    ScoringRuleCreate, ScoringRuleUpdate, ScoringRuleResponse
)
from app.api.deps import get_current_user, require_admin
from app.scoring import (
    enriched_scorer,
    SpotifyData,
    SocialData,
    LiveData,
    Trend,
    format_score_report
)

router = APIRouter(prefix="/scoring", tags=["scoring"])


# === Pydantic Models for Artist Scoring ===

class ArtistScoreRequest(BaseModel):
    """Request body for artist scoring"""
    # Spotify data (required)
    popularity: int = Field(..., ge=0, le=100, description="Spotify popularity (0-100)")
    followers: int = Field(..., ge=0, description="Spotify followers count")
    monthly_listeners: Optional[int] = Field(None, ge=0, description="Monthly listeners (from Viberate)")
    monthly_listeners_source: Optional[str] = Field(None, description="Source: viberate, estimated")
    
    # Social data (optional)
    youtube_subscribers: Optional[int] = Field(None, ge=0)
    youtube_total_views: Optional[int] = Field(None, ge=0)
    instagram_followers: Optional[int] = Field(None, ge=0)
    instagram_engagement_rate: Optional[float] = Field(None, ge=0, le=100, description="ER in %")
    tiktok_followers: Optional[int] = Field(None, ge=0)
    tiktok_total_views: Optional[int] = Field(None, ge=0)
    
    # Live data (optional)
    concerts_count: Optional[int] = Field(None, ge=0)
    festivals_count: Optional[int] = Field(None, ge=0)
    large_venues_10k_plus: Optional[int] = Field(None, ge=0)
    medium_venues_5k_10k: Optional[int] = Field(None, ge=0)
    
    # Trend override (optional)
    trend: Optional[str] = Field(None, pattern="^(rising|stable|declining)$")


class ScoreBreakdown(BaseModel):
    """Score breakdown details"""
    spotify_score: float = Field(..., description="0-40")
    social_score: float = Field(..., description="0-40")
    live_bonus: float = Field(..., description="0-20 (raw)")
    live_bonus_effective: float = Field(..., description="0-20 (after anti-double-counting)")
    quality_factor: float = Field(..., description="0.60-1.10")
    popularity_score: float = Field(..., description="0-100 (before live)")
    

class ArtistScoreResponse(BaseModel):
    """Response for artist scoring"""
    # Main scores
    final_score: float = Field(..., description="0-100")
    breakdown: ScoreBreakdown
    
    # Confidence
    confidence: float = Field(..., description="0-100%")
    
    # Tier & Fee
    tier: int = Field(..., ge=1, le=6)
    tier_name: str
    fee_min: int
    fee_max: int
    fee_currency: str = "EUR"
    
    # Trend
    trend: str
    
    # Warnings
    warnings: List[str] = []
    
    # Details (optional)
    spotify_details: dict = {}
    social_details: dict = {}
    confidence_details: dict = {}


# === Artist Scoring Endpoints ===

@router.post("/artist", response_model=ArtistScoreResponse)
def score_artist(
    request: ArtistScoreRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Calculate artist popularity score and estimated fee
    
    **Scores calculated:**
    - SpotifyScore (0-40): Based on popularity, followers, monthly listeners
    - SocialScore (0-40): YouTube + Instagram + TikTok
    - LiveBonus (0-20): Concerts, festivals, venues
    - QualityFactor (0.60-1.10): Anti-vanity adjustment
    
    **Final formula:**
    ```
    PopularityScore = (SpotifyScore + SocialScore) × QualityFactor
    FinalScore = clamp(PopularityScore + LiveBonus, 0, 100)
    ```
    """
    # Build SpotifyData
    spotify_data = SpotifyData(
        popularity=request.popularity,
        followers=request.followers,
        monthly_listeners=request.monthly_listeners,
        monthly_listeners_source=request.monthly_listeners_source
    )
    
    # Build SocialData
    social_data = SocialData(
        youtube_subscribers=request.youtube_subscribers,
        youtube_total_views=request.youtube_total_views,
        instagram_followers=request.instagram_followers,
        instagram_engagement_rate=request.instagram_engagement_rate,
        tiktok_followers=request.tiktok_followers,
        tiktok_total_views=request.tiktok_total_views
    )
    
    # Build LiveData
    live_data = None
    if any([request.concerts_count, request.festivals_count, 
            request.large_venues_10k_plus, request.medium_venues_5k_10k]):
        live_data = LiveData(
            concerts_count=request.concerts_count or 0,
            festivals_count=request.festivals_count or 0,
            large_venues_10k_plus=request.large_venues_10k_plus or 0,
            medium_venues_5k_10k=request.medium_venues_5k_10k or 0
        )
    
    # Parse trend
    trend = None
    if request.trend:
        trend = Trend(request.trend)
    
    # Calculate score
    result = enriched_scorer.scorer.calculate(
        spotify=spotify_data,
        social=social_data,
        live=live_data,
        trend=trend
    )
    
    # Build response
    return ArtistScoreResponse(
        final_score=round(result.final_score, 1),
        breakdown=ScoreBreakdown(
            spotify_score=round(result.spotify_score, 2),
            social_score=round(result.social_score, 2),
            live_bonus=round(result.live_bonus, 2),
            live_bonus_effective=round(result.live_bonus_effective, 2),
            quality_factor=round(result.quality_factor, 3),
            popularity_score=round(result.popularity_score, 2)
        ),
        confidence=round(result.confidence, 1),
        tier=result.tier.value,
        tier_name=result.tier.name,
        fee_min=result.fee_min,
        fee_max=result.fee_max,
        fee_currency=result.fee_currency,
        trend=result.trend.value,
        warnings=result.warnings,
        spotify_details={k: round(v, 4) for k, v in result.spotify_details.items()},
        social_details={k: round(v, 4) for k, v in result.social_details.items()},
        confidence_details=result.confidence_details
    )


@router.post("/artist/quick")
def quick_score_artist(
    popularity: int,
    followers: int,
    monthly_listeners: Optional[int] = None,
    youtube_subs: Optional[int] = None,
    instagram_followers: Optional[int] = None,
    tiktok_followers: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Quick artist scoring (query params only)
    
    Simplified version for quick lookups.
    """
    return enriched_scorer.quick_score(
        popularity=popularity,
        followers=followers,
        monthly_listeners=monthly_listeners,
        youtube_subs=youtube_subs,
        instagram_followers=instagram_followers,
        tiktok_followers=tiktok_followers
    )


@router.get("/tiers")
def get_fee_tiers():
    """
    Get fee tier definitions
    
    Returns the score ranges and fee ranges for each tier.
    """
    from app.scoring.artist_scorer import ArtistScorer
    
    return {
        "tiers": [
            {"tier": 1, "name": "TIER_1", "score_range": "0-24", "fee_min": 1500, "fee_max": 5000},
            {"tier": 2, "name": "TIER_2", "score_range": "25-39", "fee_min": 5000, "fee_max": 15000},
            {"tier": 3, "name": "TIER_3", "score_range": "40-54", "fee_min": 15000, "fee_max": 40000},
            {"tier": 4, "name": "TIER_4", "score_range": "55-69", "fee_min": 40000, "fee_max": 100000},
            {"tier": 5, "name": "TIER_5", "score_range": "70-89", "fee_min": 100000, "fee_max": 300000},
            {"tier": 6, "name": "TIER_6", "score_range": "90-100", "fee_min": 300000, "fee_max": 1000000},
        ],
        "score_weights": {
            "spotify_max": 40,
            "social_max": 40,
            "live_bonus_max": 20,
            "quality_factor_range": "0.60-1.10"
        },
        "notes": [
            "SpotifyScore = 40 × (0.70 × popularity/100 + 0.30 × log_norm(followers))",
            "SocialScore = YouTube(0-20) + Instagram(0-12) + TikTok(0-8)",
            "LiveBonus = DatesBonus(0-8) + FestivalsBonus(0-6) + VenueBonus(0-6)",
            "FinalScore = clamp((SpotifyScore + SocialScore) × QualityFactor + LiveBonus, 0, 100)"
        ]
    }


# === Existing Scoring Rules Endpoints ===


@router.get("/rules", response_model=List[ScoringRuleResponse])
def list_scoring_rules(
    rule_type: RuleType = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all scoring rules"""
    query = db.query(ScoringRule)
    
    if rule_type:
        query = query.filter(ScoringRule.rule_type == rule_type)
    if is_active is not None:
        query = query.filter(ScoringRule.is_active == is_active)
    
    return query.order_by(ScoringRule.priority.desc(), ScoringRule.name).all()


@router.get("/rules/{rule_id}", response_model=ScoringRuleResponse)
def get_scoring_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get scoring rule by ID"""
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found",
        )
    return rule


@router.post("/rules", response_model=ScoringRuleResponse)
def create_scoring_rule(
    rule_data: ScoringRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new scoring rule"""
    existing = db.query(ScoringRule).filter(
        ScoringRule.name == rule_data.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rule with this name already exists",
        )
    
    rule = ScoringRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=ScoringRuleResponse)
def update_scoring_rule(
    rule_id: UUID,
    update_data: ScoringRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update scoring rule"""
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found",
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_scoring_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete scoring rule"""
    rule = db.query(ScoringRule).filter(ScoringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring rule not found",
        )
    
    db.delete(rule)
    db.commit()
    return {"message": "Scoring rule deleted successfully"}
