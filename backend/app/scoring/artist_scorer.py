"""
Artist Scoring System
Calcule le score de popularité et le cachet estimé d'un artiste

Scores calculés:
- SpotifyScore (0-40): Basé sur popularity, followers, monthly listeners
- SocialScore (0-40): YouTube + Instagram + TikTok
- LiveBonus (0-20): Concerts, festivals, salles
- Confidence (0-100%): Fiabilité des données

FinalScore (0-100) = clamp((SpotifyScore + SocialScore) × QualityFactor + LiveBonus, 0, 100)
"""
import math
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def log_normalize(value: int, max_reference: int) -> float:
    """
    Normalise une valeur avec log10
    log_normalize(1M, 10M) → ~0.857
    log_normalize(100k, 10M) → ~0.714
    """
    if value <= 0:
        return 0.0
    return clamp(math.log10(value + 1) / math.log10(max_reference), 0, 1)


class Trend(Enum):
    """Tendance de l'artiste"""
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


class Tier(Enum):
    """Tier de cachet"""
    TIER_1 = 1  # 1.5k - 5k
    TIER_2 = 2  # 5k - 15k
    TIER_3 = 3  # 15k - 40k
    TIER_4 = 4  # 40k - 100k
    TIER_5 = 5  # 100k - 300k
    TIER_6 = 6  # 300k - 1M+


@dataclass
class SpotifyData:
    """Données Spotify de l'artiste"""
    popularity: int = 0  # 0-100 (API officielle)
    followers: int = 0  # Nombre de followers
    monthly_listeners: Optional[int] = None  # Optionnel (Viberate)
    monthly_listeners_source: Optional[str] = None  # "viberate", "estimated"
    monthly_listeners_date: Optional[datetime] = None


@dataclass
class SocialData:
    """Données réseaux sociaux"""
    youtube_subscribers: Optional[int] = None
    youtube_total_views: Optional[int] = None
    instagram_followers: Optional[int] = None
    instagram_engagement_rate: Optional[float] = None  # 0-100%
    tiktok_followers: Optional[int] = None
    tiktok_total_views: Optional[int] = None
    data_date: Optional[datetime] = None


@dataclass
class LiveData:
    """Données live/concerts"""
    concerts_count: int = 0  # Nombre de dates sur 12 mois
    festivals_count: int = 0  # Nombre de festivals
    large_venues_10k_plus: int = 0  # Salles >10k
    medium_venues_5k_10k: int = 0  # Salles 5k-10k
    data_source: Optional[str] = None
    data_date: Optional[datetime] = None


@dataclass
class ArtistScoreResult:
    """Résultat complet du scoring"""
    # Scores individuels
    spotify_score: float = 0.0  # 0-40
    social_score: float = 0.0  # 0-40
    live_bonus: float = 0.0  # 0-20
    live_bonus_effective: float = 0.0  # Après anti-double-comptage
    quality_factor: float = 1.0  # 0.60-1.10
    
    # Détails
    spotify_details: Dict[str, float] = field(default_factory=dict)
    social_details: Dict[str, float] = field(default_factory=dict)
    live_details: Dict[str, float] = field(default_factory=dict)
    quality_details: Dict[str, float] = field(default_factory=dict)
    
    # Scores finaux
    popularity_score: float = 0.0  # 0-100 (avant live)
    final_score: float = 0.0  # 0-100
    
    # Confidence
    confidence: float = 0.0  # 0-100%
    confidence_details: Dict[str, float] = field(default_factory=dict)
    
    # Trend & Tier
    trend: Trend = Trend.STABLE
    tier: Tier = Tier.TIER_1
    
    # Cachet estimé
    fee_min: int = 0
    fee_max: int = 0
    fee_currency: str = "EUR"
    
    # Métadonnées
    calculated_at: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)


class ArtistScorer:
    """
    Système de scoring pour artistes
    
    Usage:
        scorer = ArtistScorer()
        result = scorer.calculate(
            spotify=SpotifyData(popularity=75, followers=1_000_000),
            social=SocialData(youtube_subscribers=500_000, instagram_followers=300_000),
            live=LiveData(concerts_count=25, festivals_count=3)
        )
        print(f"Score final: {result.final_score}/100")
        print(f"Cachet: {result.fee_min}-{result.fee_max} {result.fee_currency}")
    """
    
    # Constantes de référence pour normalisation
    SPOTIFY_FOLLOWERS_REF = 10_000_000  # 10M followers = max
    SPOTIFY_MONTHLY_REF = 10_000_000  # 10M monthly = max
    SOCIAL_REF = 5_000_000  # 5M = max pour YouTube/Instagram/TikTok
    
    # Pondérations
    SPOTIFY_POPULARITY_WEIGHT = 0.70
    SPOTIFY_FOLLOWERS_WEIGHT = 0.30
    SPOTIFY_MONTHLY_ADJUSTMENT = 6  # ±6 points max
    
    YOUTUBE_MAX = 20
    INSTAGRAM_MAX = 12
    TIKTOK_MAX = 8
    
    # Tiers de cachet (min, max en EUR)
    FEE_TIERS = {
        Tier.TIER_1: (1_500, 5_000),
        Tier.TIER_2: (5_000, 15_000),
        Tier.TIER_3: (15_000, 40_000),
        Tier.TIER_4: (40_000, 100_000),
        Tier.TIER_5: (100_000, 300_000),
        Tier.TIER_6: (300_000, 1_000_000),
    }
    
    def calculate(
        self,
        spotify: SpotifyData,
        social: Optional[SocialData] = None,
        live: Optional[LiveData] = None,
        trend: Optional[Trend] = None
    ) -> ArtistScoreResult:
        """
        Calcule le score complet d'un artiste
        
        Args:
            spotify: Données Spotify (obligatoire)
            social: Données réseaux sociaux (optionnel)
            live: Données live/concerts (optionnel)
            trend: Tendance manuelle (optionnel, sinon calculée)
        
        Returns:
            ArtistScoreResult avec tous les scores et le cachet estimé
        """
        result = ArtistScoreResult()
        social = social or SocialData()
        live = live or LiveData()
        
        # 1. SpotifyScore (0-40)
        result.spotify_score, result.spotify_details = self._calculate_spotify_score(spotify)
        
        # 2. SocialScore (0-40)
        result.social_score, result.social_details = self._calculate_social_score(social)
        
        # 3. QualityFactor (0.60-1.10)
        result.quality_factor, result.quality_details = self._calculate_quality_factor(spotify, social)
        
        # 4. LiveBonus (0-20)
        result.live_bonus, result.live_details = self._calculate_live_bonus(live)
        
        # 5. LiveBonus effectif (anti double-comptage)
        result.live_bonus_effective = self._calculate_live_bonus_effective(
            result.live_bonus, 
            result.spotify_score
        )
        
        # 6. PopularityScore & FinalScore
        result.popularity_score = clamp(
            (result.spotify_score + result.social_score) * result.quality_factor,
            0, 100
        )
        result.final_score = clamp(
            result.popularity_score + result.live_bonus_effective,
            0, 100
        )
        
        # 7. Confidence (0-100%)
        result.confidence, result.confidence_details = self._calculate_confidence(
            spotify, social, live
        )
        
        # 8. Trend
        result.trend = trend if trend else self._estimate_trend(spotify, social)
        
        # 9. Tier & Cachet
        result.tier = self._determine_tier(result.final_score, live)
        result.fee_min, result.fee_max = self._calculate_fee(
            result.tier,
            result.confidence,
            result.trend
        )
        
        # Warnings
        result.warnings = self._generate_warnings(spotify, social, live, result)
        
        logger.info(
            f"Artist score calculated: {result.final_score:.1f}/100 "
            f"(Spotify:{result.spotify_score:.1f}, Social:{result.social_score:.1f}, "
            f"Live:{result.live_bonus_effective:.1f}, QF:{result.quality_factor:.2f})"
        )
        
        return result
    
    def _calculate_spotify_score(self, spotify: SpotifyData) -> tuple[float, Dict[str, float]]:
        """
        Calcule le SpotifyScore (0-40)
        
        Formule:
            S_pop = 0.70 * (popularity / 100)
            S_fol = 0.30 * log_norm(followers)
            SpotifyScore_base = 40 * (S_pop + S_fol)
            
            Si monthly_listeners disponible:
                ML_norm = log_norm(monthly_listeners)
                SpotifyScore = SpotifyScore_base + 6 * (ML_norm - 0.5)
        """
        details = {}
        
        # Composante popularity (70%)
        s_pop = self.SPOTIFY_POPULARITY_WEIGHT * (spotify.popularity / 100)
        details['popularity_normalized'] = spotify.popularity / 100
        details['popularity_contribution'] = s_pop
        
        # Composante followers (30%)
        fol_norm = log_normalize(spotify.followers, self.SPOTIFY_FOLLOWERS_REF)
        s_fol = self.SPOTIFY_FOLLOWERS_WEIGHT * fol_norm
        details['followers_normalized'] = fol_norm
        details['followers_contribution'] = s_fol
        
        # Score de base
        score_base = 40 * (s_pop + s_fol)
        details['score_base'] = score_base
        
        # Ajustement monthly listeners (optionnel)
        ml_adjustment = 0.0
        if spotify.monthly_listeners is not None and spotify.monthly_listeners > 0:
            ml_norm = log_normalize(spotify.monthly_listeners, self.SPOTIFY_MONTHLY_REF)
            ml_adjustment = self.SPOTIFY_MONTHLY_ADJUSTMENT * (ml_norm - 0.5)
            details['monthly_listeners_normalized'] = ml_norm
            details['monthly_listeners_adjustment'] = ml_adjustment
        
        # Score final
        score = clamp(score_base + ml_adjustment, 0, 40)
        details['final'] = score
        
        return score, details
    
    def _calculate_social_score(self, social: SocialData) -> tuple[float, Dict[str, float]]:
        """
        Calcule le SocialScore (0-40)
        
        YouTube (0-20) + Instagram (0-12) + TikTok (0-8)
        """
        details = {}
        
        # YouTube (0-20)
        yt_score = 0.0
        if social.youtube_subscribers is not None and social.youtube_subscribers > 0:
            yt_norm = log_normalize(social.youtube_subscribers, self.SOCIAL_REF)
            yt_score = self.YOUTUBE_MAX * yt_norm
            details['youtube_normalized'] = yt_norm
        details['youtube_score'] = yt_score
        
        # Instagram (0-12)
        ig_score = 0.0
        if social.instagram_followers is not None and social.instagram_followers > 0:
            ig_norm = log_normalize(social.instagram_followers, self.SOCIAL_REF)
            ig_score = self.INSTAGRAM_MAX * ig_norm
            details['instagram_normalized'] = ig_norm
        details['instagram_score'] = ig_score
        
        # TikTok (0-8)
        tt_score = 0.0
        if social.tiktok_followers is not None and social.tiktok_followers > 0:
            tt_norm = log_normalize(social.tiktok_followers, self.SOCIAL_REF)
            tt_score = self.TIKTOK_MAX * tt_norm
            details['tiktok_normalized'] = tt_norm
        details['tiktok_score'] = tt_score
        
        # Total
        score = yt_score + ig_score + tt_score
        details['final'] = score
        
        return score, details
    
    def _calculate_quality_factor(
        self, 
        spotify: SpotifyData, 
        social: SocialData
    ) -> tuple[float, Dict[str, float]]:
        """
        Calcule le QualityFactor (0.60-1.10)
        
        Anti-vanity metrics: pénalise les métriques gonflées
        """
        details = {}
        qf = 1.0
        
        # Instagram engagement rate
        if social.instagram_engagement_rate is not None:
            er = social.instagram_engagement_rate
            if er < 0.3:
                qf -= 0.15
                details['instagram_er_penalty'] = -0.15
            elif er < 0.8:
                qf -= 0.08
                details['instagram_er_penalty'] = -0.08
            elif er >= 2.0:
                qf += 0.05
                details['instagram_er_bonus'] = 0.05
        
        # YouTube views/subs ratio (si données disponibles)
        if (social.youtube_subscribers is not None and 
            social.youtube_total_views is not None and
            social.youtube_subscribers > 10000):
            
            views_per_sub = social.youtube_total_views / social.youtube_subscribers
            if views_per_sub < 10:  # Moins de 10 vues par sub = suspect
                qf -= 0.08
                details['youtube_ratio_penalty'] = -0.08
        
        # TikTok views/followers ratio
        if (social.tiktok_followers is not None and 
            social.tiktok_total_views is not None and
            social.tiktok_followers > 10000):
            
            views_per_fol = social.tiktok_total_views / social.tiktok_followers
            if views_per_fol < 5:  # Moins de 5 vues par follower = suspect
                qf -= 0.08
                details['tiktok_ratio_penalty'] = -0.08
        
        # Incohérence Spotify vs Social
        if spotify.followers > 0 and social.instagram_followers is not None:
            ratio = social.instagram_followers / spotify.followers
            if ratio > 50:  # IG 50x plus grand que Spotify = suspect
                qf -= 0.10
                details['ig_spotify_ratio_penalty'] = -0.10
            elif ratio < 0.01:  # IG 100x plus petit = bizarre
                qf -= 0.05
                details['ig_spotify_ratio_penalty'] = -0.05
        
        # Clamp final
        qf = clamp(qf, 0.60, 1.10)
        details['final'] = qf
        
        return qf, details
    
    def _calculate_live_bonus(self, live: LiveData) -> tuple[float, Dict[str, float]]:
        """
        Calcule le LiveBonus brut (0-20)
        
        DatesBonus (0-8) + FestBonus (0-6) + VenueBonus (0-6)
        """
        details = {}
        
        # Bonus dates (0-8)
        if live.concerts_count >= 20:
            dates_bonus = 8
        elif live.concerts_count >= 10:
            dates_bonus = 6
        elif live.concerts_count >= 5:
            dates_bonus = 3
        else:
            dates_bonus = 0
        details['dates_bonus'] = dates_bonus
        
        # Bonus festivals (0-6)
        fest_bonus = min(6, live.festivals_count * 2)
        details['festivals_bonus'] = fest_bonus
        
        # Bonus salles (0-6)
        venue_bonus = min(6, live.large_venues_10k_plus * 2 + live.medium_venues_5k_10k * 1)
        details['venue_bonus'] = venue_bonus
        
        # Total brut
        score = min(20, dates_bonus + fest_bonus + venue_bonus)
        details['final'] = score
        
        return score, details
    
    def _calculate_live_bonus_effective(
        self, 
        live_bonus: float, 
        spotify_score: float
    ) -> float:
        """
        Calcule le LiveBonus effectif (anti double-comptage)
        
        Si Spotify très fort → live compte moins (déjà reflété dans popularity)
        LiveBonusEffective = LiveBonus × (0.7 + 0.3 × (1 - SpotifyScore/40))
        """
        spotify_factor = 1 - (spotify_score / 40)
        multiplier = 0.7 + 0.3 * spotify_factor
        return live_bonus * multiplier
    
    def _calculate_confidence(
        self,
        spotify: SpotifyData,
        social: SocialData,
        live: LiveData
    ) -> tuple[float, Dict[str, float]]:
        """
        Calcule la Confidence (0-100%)
        
        Coverage (0-40) + Consistency (0-40) + Freshness (0-20)
        """
        details = {}
        
        # === Coverage (0-40) ===
        coverage = 0
        
        # Spotify API ok (+20)
        if spotify.popularity > 0 or spotify.followers > 0:
            coverage += 20
            details['spotify_api'] = 20
        
        # Monthly listeners sourcé (+15)
        if (spotify.monthly_listeners is not None and 
            spotify.monthly_listeners_source == "viberate"):
            coverage += 15
            details['monthly_listeners_sourced'] = 15
        
        # Live data sourcée (+5)
        if live.data_source is not None:
            coverage += 5
            details['live_data_sourced'] = 5
        
        details['coverage'] = coverage
        
        # === Consistency (0-40) ===
        consistency = 40
        
        # Vérifier cohérence Spotify vs Social
        if spotify.followers > 100000 and social.instagram_followers is not None:
            ratio = social.instagram_followers / spotify.followers
            if ratio > 20 or ratio < 0.05:
                consistency -= 10
                details['consistency_spotify_social_mismatch'] = -10
        
        # Vérifier cohérence followers vs popularity
        if spotify.followers > 0:
            expected_pop_min = min(100, 10 * math.log10(spotify.followers + 1) - 30)
            if spotify.popularity < expected_pop_min - 20:
                consistency -= 8
                details['consistency_followers_popularity_mismatch'] = -8
        
        details['consistency'] = consistency
        
        # === Freshness (0-20) ===
        freshness = 5  # Défaut si pas de date
        
        dates_to_check = [
            spotify.monthly_listeners_date,
            social.data_date,
            live.data_date
        ]
        most_recent = None
        for d in dates_to_check:
            if d is not None:
                if most_recent is None or d > most_recent:
                    most_recent = d
        
        if most_recent is not None:
            days_old = (datetime.now() - most_recent).days
            if days_old < 30:
                freshness = 20
            elif days_old < 90:
                freshness = 12
            else:
                freshness = 5
        
        details['freshness'] = freshness
        
        # Total
        confidence = coverage + consistency + freshness
        details['final'] = confidence
        
        return confidence, details
    
    def _estimate_trend(
        self, 
        spotify: SpotifyData, 
        social: SocialData
    ) -> Trend:
        """
        Estime la tendance (Rising/Stable/Declining)
        
        Basé sur les signaux disponibles
        """
        # Par défaut stable
        # TODO: Implémenter avec données historiques
        return Trend.STABLE
    
    def _determine_tier(
        self, 
        final_score: float, 
        live: LiveData
    ) -> Tier:
        """
        Détermine le tier de cachet basé sur le score
        
        Si live data disponible:
            tier basé à 70% sur Live + 30% Popularity
        Sinon:
            tier basé sur FinalScore
        """
        # Si live data significative, ajuster
        effective_score = final_score
        
        if live.concerts_count > 0 or live.festivals_count > 0:
            # Live représente une preuve de marché
            live_score = min(100, (
                live.concerts_count * 2 +
                live.festivals_count * 5 +
                live.large_venues_10k_plus * 10 +
                live.medium_venues_5k_10k * 5
            ))
            # 70% live + 30% popularity
            effective_score = 0.7 * live_score + 0.3 * final_score
        
        # Déterminer tier
        if effective_score < 25:
            return Tier.TIER_1
        elif effective_score < 40:
            return Tier.TIER_2
        elif effective_score < 55:
            return Tier.TIER_3
        elif effective_score < 70:
            return Tier.TIER_4
        elif effective_score < 90:
            return Tier.TIER_5
        else:
            return Tier.TIER_6
    
    def _calculate_fee(
        self,
        tier: Tier,
        confidence: float,
        trend: Trend
    ) -> tuple[int, int]:
        """
        Calcule le cachet estimé
        
        Ajustements:
        - Confidence < 40%: fourchette × 1.35
        - Confidence >= 75%: fourchette × 0.85
        - Trend Rising: +10%
        - Trend Declining: -15%
        """
        base_min, base_max = self.FEE_TIERS[tier]
        
        # Ajustement selon confidence
        if confidence < 40:
            # Fourchette élargie
            range_expansion = 1.35
            fee_min = int(base_min / range_expansion)
            fee_max = int(base_max * range_expansion)
        elif confidence >= 75:
            # Fourchette resserrée
            range_factor = 0.85
            mid = (base_min + base_max) / 2
            half_range = (base_max - base_min) / 2 * range_factor
            fee_min = int(mid - half_range)
            fee_max = int(mid + half_range)
        else:
            fee_min = base_min
            fee_max = base_max
        
        # Ajustement selon trend
        if trend == Trend.RISING:
            fee_min = int(fee_min * 1.10)
            fee_max = int(fee_max * 1.10)
        elif trend == Trend.DECLINING:
            fee_min = int(fee_min * 0.85)
            fee_max = int(fee_max * 0.85)
        
        return fee_min, fee_max
    
    def _generate_warnings(
        self,
        spotify: SpotifyData,
        social: SocialData,
        live: LiveData,
        result: ArtistScoreResult
    ) -> List[str]:
        """Génère des warnings pour les données suspectes ou manquantes"""
        warnings = []
        
        # Données manquantes
        if spotify.monthly_listeners is None:
            warnings.append("Monthly listeners non disponible - estimation moins précise")
        
        if social.youtube_subscribers is None and social.instagram_followers is None:
            warnings.append("Aucune donnée sociale - SocialScore à 0")
        
        if live.concerts_count == 0 and live.festivals_count == 0:
            warnings.append("Aucune donnée live - LiveBonus à 0")
        
        # Confidence faible
        if result.confidence < 40:
            warnings.append("⚠️ Confidence < 40% - données à vérifier manuellement")
        
        # QualityFactor bas
        if result.quality_factor < 0.75:
            warnings.append("⚠️ QualityFactor bas - métriques potentiellement gonflées")
        
        # Incohérences
        if result.quality_details.get('ig_spotify_ratio_penalty'):
            warnings.append("Ratio Instagram/Spotify anormal")
        
        return warnings


# === Singleton pour usage global ===
artist_scorer = ArtistScorer()
