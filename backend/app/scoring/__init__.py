"""
Scoring module - Artist popularity and fee estimation

Main components:
- ArtistScorer: Calculate SpotifyScore, SocialScore, LiveBonus, FinalScore
- EnrichedArtistScorer: Integration with Viberate enrichment data
- ScoringEngine: Legacy opportunity scoring (existing)
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
]
