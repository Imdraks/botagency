"""
Advanced AI Intelligence API Endpoints
Provides access to AI-powered artist analysis, discovery, and recommendations
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.api.deps import get_current_user
from app.intelligence.artist_intelligence_engine import (
    intelligence_engine,
    ArtistIntelligenceReport,
    GrowthTrend,
    ArtistTier,
)
from app.intelligence.artist_discovery_engine import (
    discovery_engine,
    EmergingArtist,
    PotentialLevel,
)
from app.intelligence.recommendation_engine import (
    recommendation_engine,
    ArtistProfile,
    OpportunityProfile,
    ArtistRecommendation,
    MatchType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


# ============== Request Models ==============

class ArtistAnalysisRequest(BaseModel):
    """Request for full AI analysis"""
    artist_name: str = Field(..., description="Artist name")
    spotify_monthly_listeners: int = Field(0, ge=0)
    spotify_followers: int = Field(0, ge=0)
    youtube_subscribers: int = Field(0, ge=0)
    instagram_followers: int = Field(0, ge=0)
    tiktok_followers: int = Field(0, ge=0)
    genre: str = Field("default", description="Primary genre")
    country: str = Field("FR", description="Primary country")
    historical_data: Optional[List[Dict[str, Any]]] = None


class DiscoveryAnalysisRequest(BaseModel):
    """Request for discovery/potential analysis"""
    artist_name: str
    monthly_listeners: int = Field(0, ge=0)
    spotify_followers: int = Field(0, ge=0)
    social_followers: int = Field(0, ge=0)
    genres: List[str] = Field(default_factory=list)
    spotify_id: Optional[str] = None
    historical_listeners: Optional[List[int]] = None


class ArtistProfileInput(BaseModel):
    """Artist profile for matching"""
    name: str
    genres: List[str]
    tier: str
    monthly_listeners: int
    estimated_fee: int
    trend: str = "stable"
    countries: List[str] = Field(default_factory=lambda: ["FR"])
    event_types: List[str] = Field(default_factory=list)
    availability: float = Field(0.8, ge=0, le=1)
    social_reach: int = 0
    age_demographic: str = "18-34"


class OpportunityInput(BaseModel):
    """Opportunity profile for matching"""
    id: str
    title: str
    event_type: str
    genres_wanted: List[str]
    budget_min: int
    budget_max: int
    location: str = ""
    country: str = "FR"
    date: Optional[datetime] = None
    audience_size: int = 0
    audience_demographic: str = ""
    requirements: List[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    """Request for artist-opportunity matching"""
    artist: ArtistProfileInput
    opportunity: OpportunityInput


class BatchMatchRequest(BaseModel):
    """Batch matching request"""
    artists: List[ArtistProfileInput]
    opportunity: OpportunityInput
    limit: int = Field(10, ge=1, le=50)


class CompareArtistsRequest(BaseModel):
    """Request to compare multiple artists"""
    artists: List[ArtistAnalysisRequest]


# ============== Response Models ==============

class TrendPredictionResponse(BaseModel):
    """Trend prediction response"""
    metric_name: str
    current_value: int
    predicted_30d: int
    predicted_90d: int
    predicted_180d: int
    confidence: float
    growth_rate_monthly: float
    trend: str


class BookingIntelligenceResponse(BaseModel):
    """Booking intelligence response"""
    estimated_fee_min: int
    estimated_fee_max: int
    optimal_fee: int
    negotiation_power: str
    best_booking_window: str
    event_type_fit: Dict[str, float]
    territory_strength: Dict[str, float]
    seasonal_demand: Dict[str, float]


class MarketAnalysisResponse(BaseModel):
    """Market analysis response"""
    tier: str
    position: str
    genre_rank_estimate: int
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class ContentStrategyResponse(BaseModel):
    """Content strategy response"""
    best_platforms: List[str]
    posting_frequency: Dict[str, str]
    engagement_rate: float
    viral_potential: float
    content_recommendations: List[str]
    collaboration_suggestions: List[str]


class IntelligenceReportResponse(BaseModel):
    """Full intelligence report response"""
    artist_name: str
    analysis_date: datetime
    overall_score: float
    confidence_score: float
    tier: str
    
    market_analysis: MarketAnalysisResponse
    listener_prediction: TrendPredictionResponse
    social_prediction: TrendPredictionResponse
    overall_trend: str
    
    booking_intelligence: BookingIntelligenceResponse
    content_strategy: ContentStrategyResponse
    
    risk_score: float
    risk_factors: List[str]
    opportunity_score: float
    key_opportunities: List[str]
    
    ai_summary: str
    recommendations: List[str]


class DiscoveryPatternResponse(BaseModel):
    """Discovery pattern response"""
    pattern_type: str
    confidence: float
    description: str
    impact_score: float


class EmergingArtistResponse(BaseModel):
    """Emerging artist response"""
    name: str
    spotify_id: Optional[str]
    genres: List[str]
    
    monthly_listeners: int
    spotify_followers: int
    total_social_followers: int
    
    growth_velocity: float
    acceleration: float
    
    signals: List[str]
    patterns: List[DiscoveryPatternResponse]
    
    potential_level: str
    potential_score: float
    breakout_probability: float
    
    discovered_at: datetime
    estimated_breakout: Optional[str]
    
    why_watch: List[str]
    booking_advice: str
    estimated_current_fee: int
    estimated_future_fee: int


class MatchScoreResponse(BaseModel):
    """Match score response"""
    overall_score: float
    match_type: str
    
    genre_score: float
    budget_score: float
    audience_score: float
    geographic_score: float
    availability_score: float
    momentum_score: float
    
    reasons: List[str]
    concerns: List[str]
    
    value_rating: str
    negotiation_room: int


class ArtistRecommendationResponse(BaseModel):
    """Artist recommendation response"""
    artist_name: str
    artist_tier: str
    estimated_fee: int
    
    match_score: MatchScoreResponse
    
    why_book: str
    negotiation_tip: str
    alternative_suggestions: List[str]
    
    urgency: str
    best_contact_window: str


class ComparisonResponse(BaseModel):
    """Artist comparison response"""
    artists: List[str]
    scores: Dict[str, float]
    tiers: Dict[str, str]
    trends: Dict[str, str]
    fees: Dict[str, Dict[str, int]]
    best_value: str
    highest_potential: str
    lowest_risk: str


# ============== API Endpoints ==============

@router.post("/analyze", response_model=IntelligenceReportResponse)
async def analyze_artist(
    request: ArtistAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """
    🧠 Full AI Intelligence Analysis
    
    Generates a comprehensive AI-powered report including:
    - Overall scoring and tier classification
    - Growth predictions (30/90/180 days)
    - Market position analysis (SWOT)
    - Booking intelligence (fees, negotiation, timing)
    - Content strategy recommendations
    - Risk and opportunity assessment
    - AI-generated insights and recommendations
    """
    try:
        report = intelligence_engine.analyze_artist(
            artist_name=request.artist_name,
            spotify_monthly_listeners=request.spotify_monthly_listeners,
            spotify_followers=request.spotify_followers,
            youtube_subscribers=request.youtube_subscribers,
            instagram_followers=request.instagram_followers,
            tiktok_followers=request.tiktok_followers,
            genre=request.genre,
            country=request.country,
            historical_data=request.historical_data,
        )
        
        return IntelligenceReportResponse(
            artist_name=report.artist_name,
            analysis_date=report.analysis_date,
            overall_score=report.overall_score,
            confidence_score=report.confidence_score,
            tier=report.tier.value,
            market_analysis=MarketAnalysisResponse(
                tier=report.market_analysis.tier.value,
                position=report.market_analysis.position.value,
                genre_rank_estimate=report.market_analysis.genre_rank_estimate,
                strengths=report.market_analysis.strengths,
                weaknesses=report.market_analysis.weaknesses,
                opportunities=report.market_analysis.opportunities,
                threats=report.market_analysis.threats,
            ),
            listener_prediction=TrendPredictionResponse(
                metric_name=report.listener_prediction.metric_name,
                current_value=report.listener_prediction.current_value,
                predicted_30d=report.listener_prediction.predicted_value_30d,
                predicted_90d=report.listener_prediction.predicted_value_90d,
                predicted_180d=report.listener_prediction.predicted_value_180d,
                confidence=report.listener_prediction.confidence,
                growth_rate_monthly=report.listener_prediction.growth_rate_monthly,
                trend=report.listener_prediction.trend.value,
            ),
            social_prediction=TrendPredictionResponse(
                metric_name=report.social_prediction.metric_name,
                current_value=report.social_prediction.current_value,
                predicted_30d=report.social_prediction.predicted_value_30d,
                predicted_90d=report.social_prediction.predicted_value_90d,
                predicted_180d=report.social_prediction.predicted_value_180d,
                confidence=report.social_prediction.confidence,
                growth_rate_monthly=report.social_prediction.growth_rate_monthly,
                trend=report.social_prediction.trend.value,
            ),
            overall_trend=report.overall_trend.value,
            booking_intelligence=BookingIntelligenceResponse(
                estimated_fee_min=report.booking_intelligence.estimated_fee_min,
                estimated_fee_max=report.booking_intelligence.estimated_fee_max,
                optimal_fee=report.booking_intelligence.optimal_fee,
                negotiation_power=report.booking_intelligence.negotiation_power,
                best_booking_window=report.booking_intelligence.best_booking_window,
                event_type_fit=report.booking_intelligence.event_type_fit,
                territory_strength=report.booking_intelligence.territory_strength,
                seasonal_demand=report.booking_intelligence.seasonal_demand,
            ),
            content_strategy=ContentStrategyResponse(
                best_platforms=report.content_strategy.best_platforms,
                posting_frequency=report.content_strategy.posting_frequency,
                engagement_rate=report.content_strategy.engagement_rate,
                viral_potential=report.content_strategy.viral_potential,
                content_recommendations=report.content_strategy.content_recommendations,
                collaboration_suggestions=report.content_strategy.collaboration_suggestions,
            ),
            risk_score=report.risk_score,
            risk_factors=report.risk_factors,
            opportunity_score=report.opportunity_score,
            key_opportunities=report.key_opportunities,
            ai_summary=report.ai_summary,
            recommendations=report.recommendations,
        )
    except Exception as e:
        logger.error(f"Error analyzing artist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover", response_model=EmergingArtistResponse)
async def discover_potential(
    request: DiscoveryAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """
    🔍 Emerging Artist Discovery
    
    Analyzes an artist for breakout potential:
    - Growth velocity and acceleration
    - Discovery signals (viral, playlist boost, etc.)
    - Pattern detection (hockey stick, acceleration)
    - Breakout probability and timing
    - Current vs future fee estimation
    - Booking advice and watch reasons
    """
    try:
        artist = discovery_engine.analyze_for_potential(
            artist_name=request.artist_name,
            monthly_listeners=request.monthly_listeners,
            spotify_followers=request.spotify_followers,
            social_followers=request.social_followers,
            genres=request.genres,
            spotify_id=request.spotify_id,
            historical_listeners=request.historical_listeners,
        )
        
        return EmergingArtistResponse(
            name=artist.name,
            spotify_id=artist.spotify_id,
            genres=artist.genres,
            monthly_listeners=artist.monthly_listeners,
            spotify_followers=artist.spotify_followers,
            total_social_followers=artist.total_social_followers,
            growth_velocity=artist.growth_velocity,
            acceleration=artist.acceleration,
            signals=[s.value for s in artist.signals],
            patterns=[
                DiscoveryPatternResponse(
                    pattern_type=p.pattern_type,
                    confidence=p.confidence,
                    description=p.description,
                    impact_score=p.impact_score,
                )
                for p in artist.patterns
            ],
            potential_level=artist.potential_level.value,
            potential_score=artist.potential_score,
            breakout_probability=artist.breakout_probability,
            discovered_at=artist.discovered_at,
            estimated_breakout=artist.estimated_breakout,
            why_watch=artist.why_watch,
            booking_advice=artist.booking_advice,
            estimated_current_fee=artist.estimated_current_fee,
            estimated_future_fee=artist.estimated_future_fee,
        )
    except Exception as e:
        logger.error(f"Error in discovery analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match", response_model=MatchScoreResponse)
async def match_artist_opportunity(
    request: MatchRequest,
    current_user = Depends(get_current_user)
):
    """
    🎯 Artist-Opportunity Matching
    
    Calculates compatibility score between artist and opportunity:
    - Genre compatibility
    - Budget fit
    - Audience match
    - Geographic compatibility
    - Momentum and availability
    - Value rating and negotiation room
    """
    try:
        artist = ArtistProfile(
            name=request.artist.name,
            genres=request.artist.genres,
            tier=request.artist.tier,
            monthly_listeners=request.artist.monthly_listeners,
            estimated_fee=request.artist.estimated_fee,
            trend=request.artist.trend,
            countries=request.artist.countries,
            event_types=request.artist.event_types,
            availability=request.artist.availability,
            social_reach=request.artist.social_reach,
            age_demographic=request.artist.age_demographic,
        )
        
        opportunity = OpportunityProfile(
            id=request.opportunity.id,
            title=request.opportunity.title,
            event_type=request.opportunity.event_type,
            genres_wanted=request.opportunity.genres_wanted,
            budget_min=request.opportunity.budget_min,
            budget_max=request.opportunity.budget_max,
            location=request.opportunity.location,
            country=request.opportunity.country,
            date=request.opportunity.date,
            audience_size=request.opportunity.audience_size,
            audience_demographic=request.opportunity.audience_demographic,
            requirements=request.opportunity.requirements,
        )
        
        score = recommendation_engine.match_artist_to_opportunity(artist, opportunity)
        
        return MatchScoreResponse(
            overall_score=score.overall_score,
            match_type=score.match_type.value,
            genre_score=score.genre_score,
            budget_score=score.budget_score,
            audience_score=score.audience_score,
            geographic_score=score.geographic_score,
            availability_score=score.availability_score,
            momentum_score=score.momentum_score,
            reasons=score.reasons,
            concerns=score.concerns,
            value_rating=score.value_rating,
            negotiation_room=score.negotiation_room,
        )
    except Exception as e:
        logger.error(f"Error in matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/artists", response_model=List[ArtistRecommendationResponse])
async def recommend_artists(
    request: BatchMatchRequest,
    current_user = Depends(get_current_user)
):
    """
    🌟 Smart Artist Recommendations
    
    Finds best matching artists for an opportunity:
    - Ranked by match score
    - Includes booking advice
    - Negotiation tips
    - Alternative suggestions
    - Urgency and timing recommendations
    """
    try:
        artists = [
            ArtistProfile(
                name=a.name,
                genres=a.genres,
                tier=a.tier,
                monthly_listeners=a.monthly_listeners,
                estimated_fee=a.estimated_fee,
                trend=a.trend,
                countries=a.countries,
                event_types=a.event_types,
                availability=a.availability,
                social_reach=a.social_reach,
                age_demographic=a.age_demographic,
            )
            for a in request.artists
        ]
        
        opportunity = OpportunityProfile(
            id=request.opportunity.id,
            title=request.opportunity.title,
            event_type=request.opportunity.event_type,
            genres_wanted=request.opportunity.genres_wanted,
            budget_min=request.opportunity.budget_min,
            budget_max=request.opportunity.budget_max,
            location=request.opportunity.location,
            country=request.opportunity.country,
            date=request.opportunity.date,
            audience_size=request.opportunity.audience_size,
            audience_demographic=request.opportunity.audience_demographic,
            requirements=request.opportunity.requirements,
        )
        
        recommendations = recommendation_engine.find_best_artists_for_opportunity(
            opportunity=opportunity,
            artists=artists,
            limit=request.limit
        )
        
        return [
            ArtistRecommendationResponse(
                artist_name=rec.artist.name,
                artist_tier=rec.artist.tier,
                estimated_fee=rec.artist.estimated_fee,
                match_score=MatchScoreResponse(
                    overall_score=rec.match_score.overall_score,
                    match_type=rec.match_score.match_type.value,
                    genre_score=rec.match_score.genre_score,
                    budget_score=rec.match_score.budget_score,
                    audience_score=rec.match_score.audience_score,
                    geographic_score=rec.match_score.geographic_score,
                    availability_score=rec.match_score.availability_score,
                    momentum_score=rec.match_score.momentum_score,
                    reasons=rec.match_score.reasons,
                    concerns=rec.match_score.concerns,
                    value_rating=rec.match_score.value_rating,
                    negotiation_room=rec.match_score.negotiation_room,
                ),
                why_book=rec.why_book,
                negotiation_tip=rec.negotiation_tip,
                alternative_suggestions=rec.alternative_suggestions,
                urgency=rec.urgency,
                best_contact_window=rec.best_contact_window,
            )
            for rec in recommendations
        ]
    except Exception as e:
        logger.error(f"Error in recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ComparisonResponse)
async def compare_artists(
    request: CompareArtistsRequest,
    current_user = Depends(get_current_user)
):
    """
    ⚖️ Compare Multiple Artists
    
    Side-by-side comparison of artists:
    - Overall scores
    - Tier and trend comparison
    - Fee ranges
    - Best value identification
    - Highest potential
    - Lowest risk
    """
    try:
        reports = []
        for artist_req in request.artists:
            report = intelligence_engine.analyze_artist(
                artist_name=artist_req.artist_name,
                spotify_monthly_listeners=artist_req.spotify_monthly_listeners,
                spotify_followers=artist_req.spotify_followers,
                youtube_subscribers=artist_req.youtube_subscribers,
                instagram_followers=artist_req.instagram_followers,
                tiktok_followers=artist_req.tiktok_followers,
                genre=artist_req.genre,
                country=artist_req.country,
                historical_data=artist_req.historical_data,
            )
            reports.append(report)
        
        comparison = intelligence_engine.compare_artists(reports)
        
        return ComparisonResponse(
            artists=comparison["artists"],
            scores=comparison["scores"],
            tiers=comparison["tiers"],
            trends=comparison["trends"],
            fees=comparison["fees"],
            best_value=comparison["best_value"],
            highest_potential=comparison["highest_potential"],
            lowest_risk=comparison["lowest_risk"],
        )
    except Exception as e:
        logger.error(f"Error in comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tiers", response_model=Dict[str, Any])
async def get_tier_definitions(
    current_user = Depends(get_current_user)
):
    """
    📊 Get Artist Tier Definitions
    
    Returns the definitions and thresholds for artist tiers.
    """
    return {
        "tiers": {
            "superstar": {
                "label": "Superstar",
                "min_listeners": 10_000_000,
                "description": "International superstar",
                "fee_range": "150,000€ - 500,000€+"
            },
            "major": {
                "label": "Major",
                "min_listeners": 1_000_000,
                "description": "Major artist with significant reach",
                "fee_range": "30,000€ - 150,000€"
            },
            "established": {
                "label": "Established",
                "min_listeners": 100_000,
                "description": "Established professional artist",
                "fee_range": "8,000€ - 30,000€"
            },
            "rising": {
                "label": "Rising",
                "min_listeners": 10_000,
                "description": "Rising artist gaining momentum",
                "fee_range": "2,000€ - 8,000€"
            },
            "emerging": {
                "label": "Emerging",
                "min_listeners": 1_000,
                "description": "Emerging artist with potential",
                "fee_range": "500€ - 2,000€"
            },
            "underground": {
                "label": "Underground",
                "min_listeners": 0,
                "description": "Underground/local artist",
                "fee_range": "200€ - 500€"
            },
        },
        "trends": {
            "explosive": "🚀 +100%/month",
            "rapid": "📈 +50-100%/month",
            "strong": "💪 +20-50%/month",
            "moderate": "📊 +5-20%/month",
            "stable": "➡️ -5% to +5%/month",
            "declining": "📉 -20% to -5%/month",
            "falling": "⬇️ <-20%/month",
        }
    }
