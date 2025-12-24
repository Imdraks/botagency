"""
Intégration du scoring avec les données enrichies (Viberate + Spotify)
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.scoring.artist_scorer import (
    ArtistScorer,
    SpotifyData,
    SocialData,
    LiveData,
    ArtistScoreResult,
    Trend,
    artist_scorer
)
from app.enrichment.models import EnrichedArtistData, SocialStatsData

logger = logging.getLogger(__name__)


class EnrichedArtistScorer:
    """
    Wrapper pour scorer un artiste à partir des données enrichies
    
    Utilise les données de:
    - Viberate (monthly listeners, social stats)
    - Spotify API (popularity, followers, genres)
    - Wikidata (management)
    - Live data (si disponible)
    """
    
    def __init__(self, scorer: Optional[ArtistScorer] = None):
        self.scorer = scorer or artist_scorer
    
    def score_from_enriched(
        self,
        enriched: EnrichedArtistData,
        live_data: Optional[LiveData] = None,
        trend: Optional[Trend] = None
    ) -> ArtistScoreResult:
        """
        Calcule le score à partir des données enrichies
        
        Args:
            enriched: Données enrichies depuis Viberate/Spotify/Wikidata
            live_data: Données live optionnelles
            trend: Tendance manuelle optionnelle
        
        Returns:
            ArtistScoreResult complet
        """
        # Construire SpotifyData
        spotify_data = SpotifyData(
            popularity=enriched.spotify.popularity or 0,
            followers=enriched.spotify.followers_total or 0,
            monthly_listeners=enriched.monthly_listeners.value,
            monthly_listeners_source=enriched.monthly_listeners.provider.split(":")[0] if enriched.monthly_listeners.provider else None,
            monthly_listeners_date=enriched.monthly_listeners.retrieved_at
        )
        
        # Construire SocialData depuis Viberate
        social_data = SocialData(
            youtube_subscribers=enriched.social_stats.youtube_subscribers if enriched.social_stats else None,
            instagram_followers=enriched.social_stats.instagram_followers if enriched.social_stats else None,
            tiktok_followers=enriched.social_stats.tiktok_followers if enriched.social_stats else None,
            data_date=enriched.social_stats.retrieved_at if enriched.social_stats else None
        )
        
        # Calculer le score
        result = self.scorer.calculate(
            spotify=spotify_data,
            social=social_data,
            live=live_data,
            trend=trend
        )
        
        logger.info(
            f"Scored enriched artist {enriched.artist.name}: "
            f"{result.final_score:.1f}/100, Tier {result.tier.value}, "
            f"Fee {result.fee_min:,}-{result.fee_max:,} EUR"
        )
        
        return result
    
    def score_from_dict(
        self,
        artist_data: Dict[str, Any],
        live_data: Optional[Dict[str, Any]] = None
    ) -> ArtistScoreResult:
        """
        Calcule le score à partir d'un dict (ex: retour de spotify_client.search_artist)
        
        Args:
            artist_data: Dict avec les clés:
                - popularity, followers (Spotify API)
                - monthly_listeners, monthly_listeners_source (Viberate)
                - social_stats: {youtube_subscribers, instagram_followers, tiktok_followers}
            live_data: Dict optionnel avec concerts_count, festivals_count, etc.
        
        Returns:
            ArtistScoreResult complet
        """
        # Construire SpotifyData
        spotify_data = SpotifyData(
            popularity=artist_data.get('popularity', 0),
            followers=artist_data.get('followers', 0),
            monthly_listeners=artist_data.get('monthly_listeners'),
            monthly_listeners_source=artist_data.get('monthly_listeners_source')
        )
        
        # Construire SocialData
        social_stats = artist_data.get('social_stats', {})
        social_data = SocialData(
            youtube_subscribers=social_stats.get('youtube_subscribers'),
            instagram_followers=social_stats.get('instagram_followers'),
            tiktok_followers=social_stats.get('tiktok_followers')
        )
        
        # Construire LiveData
        live = None
        if live_data:
            live = LiveData(
                concerts_count=live_data.get('concerts_count', 0),
                festivals_count=live_data.get('festivals_count', 0),
                large_venues_10k_plus=live_data.get('large_venues_10k_plus', 0),
                medium_venues_5k_10k=live_data.get('medium_venues_5k_10k', 0),
                data_source=live_data.get('data_source')
            )
        
        # Calculer le score
        result = self.scorer.calculate(
            spotify=spotify_data,
            social=social_data,
            live=live
        )
        
        return result
    
    def quick_score(
        self,
        popularity: int,
        followers: int,
        monthly_listeners: Optional[int] = None,
        youtube_subs: Optional[int] = None,
        instagram_followers: Optional[int] = None,
        tiktok_followers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calcul rapide pour tests/debug
        
        Returns:
            Dict simplifié avec score et cachet
        """
        result = self.scorer.calculate(
            spotify=SpotifyData(
                popularity=popularity,
                followers=followers,
                monthly_listeners=monthly_listeners
            ),
            social=SocialData(
                youtube_subscribers=youtube_subs,
                instagram_followers=instagram_followers,
                tiktok_followers=tiktok_followers
            )
        )
        
        return {
            "final_score": round(result.final_score, 1),
            "spotify_score": round(result.spotify_score, 1),
            "social_score": round(result.social_score, 1),
            "quality_factor": round(result.quality_factor, 2),
            "confidence": round(result.confidence, 1),
            "tier": result.tier.value,
            "fee_range": f"{result.fee_min:,}-{result.fee_max:,} EUR",
            "warnings": result.warnings
        }


# === Singleton ===
enriched_scorer = EnrichedArtistScorer()


# === Fonctions utilitaires ===

def score_artist_quick(
    popularity: int,
    followers: int,
    monthly_listeners: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour scoring rapide
    
    Usage:
        result = score_artist_quick(
            popularity=75,
            followers=1_000_000,
            monthly_listeners=5_000_000,
            youtube_subs=500_000,
            instagram_followers=300_000
        )
    """
    return enriched_scorer.quick_score(
        popularity=popularity,
        followers=followers,
        monthly_listeners=monthly_listeners,
        youtube_subs=kwargs.get('youtube_subs'),
        instagram_followers=kwargs.get('instagram_followers'),
        tiktok_followers=kwargs.get('tiktok_followers')
    )


def format_score_report(result: ArtistScoreResult, artist_name: str = "Artist") -> str:
    """
    Formate un rapport de score lisible
    """
    lines = [
        f"═══════════════════════════════════════════════════════════════",
        f"🎤 SCORE REPORT: {artist_name}",
        f"═══════════════════════════════════════════════════════════════",
        f"",
        f"📊 SCORES",
        f"   ├─ Spotify Score:    {result.spotify_score:5.1f} / 40",
        f"   ├─ Social Score:     {result.social_score:5.1f} / 40",
        f"   ├─ Quality Factor:   {result.quality_factor:5.2f}",
        f"   ├─ Live Bonus:       {result.live_bonus_effective:5.1f} / 20",
        f"   └─ FINAL SCORE:      {result.final_score:5.1f} / 100",
        f"",
        f"💰 CACHET ESTIMÉ",
        f"   ├─ Tier:             {result.tier.value} ({result.tier.name})",
        f"   ├─ Fourchette:       {result.fee_min:,} - {result.fee_max:,} {result.fee_currency}",
        f"   └─ Tendance:         {result.trend.value.upper()}",
        f"",
        f"📈 DÉTAILS SPOTIFY",
    ]
    
    for key, value in result.spotify_details.items():
        lines.append(f"   ├─ {key}: {value:.3f}")
    
    lines.append(f"")
    lines.append(f"📱 DÉTAILS SOCIAL")
    for key, value in result.social_details.items():
        lines.append(f"   ├─ {key}: {value:.2f}")
    
    lines.append(f"")
    lines.append(f"🎯 CONFIDENCE: {result.confidence:.1f}%")
    for key, value in result.confidence_details.items():
        lines.append(f"   ├─ {key}: {value}")
    
    if result.warnings:
        lines.append(f"")
        lines.append(f"⚠️  WARNINGS")
        for warning in result.warnings:
            lines.append(f"   • {warning}")
    
    lines.append(f"═══════════════════════════════════════════════════════════════")
    
    return "\n".join(lines)
