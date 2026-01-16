"""
Scoring module - Artist popularity and fee estimation + Advanced Opportunity Scoring

Main components:
- ArtistScorer: Calculate SpotifyScore, SocialScore, LiveBonus, FinalScore
- EnrichedArtistScorer: Integration with Viberate enrichment data
- ScoringEngine: Legacy opportunity scoring (existing)
- AdvancedScoringEngine: 🚀 Moteur de scoring survitaminé pour opportunités
"""
from .engine import ScoringEngine
from .artist_scorer import (
    ArtistScorer,
    SpotifyData,
    SocialData,
    LiveData,
    ArtistScoreResult,
    Trend,
    Tier,
    artist_scorer
)
from .enriched_scorer import (
    EnrichedArtistScorer,
    enriched_scorer,
    score_artist_quick,
    format_score_report
)
from .advanced_engine import (
    AdvancedScoringEngine,
    advanced_scorer,
    AgencyConfig,
    ScoreBreakdown,
    score_opportunity_advanced,
    configure_agency,
    get_agency_config
)

__all__ = [
    # Legacy
    "ScoringEngine",
    
    # New artist scoring
    "ArtistScorer",
    "SpotifyData",
    "SocialData", 
    "LiveData",
    "ArtistScoreResult",
    "Trend",
    "Tier",
    "artist_scorer",
    
    # Enriched scoring integration
    "EnrichedArtistScorer",
    "enriched_scorer",
    "score_artist_quick",
    "format_score_report",
    
    # 🚀 Advanced opportunity scoring
    "AdvancedScoringEngine",
    "advanced_scorer",
    "AgencyConfig",
    "ScoreBreakdown",
    "score_opportunity_advanced",
    "configure_agency",
    "get_agency_config",
]
