"""
Smart Recommendation Engine
AI-powered artist and opportunity matching
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import math

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Type of recommendation match"""
    PERFECT = "perfect"       # 90-100% match
    EXCELLENT = "excellent"   # 80-89% match
    GOOD = "good"             # 70-79% match
    FAIR = "fair"             # 60-69% match
    POSSIBLE = "possible"     # 50-59% match
    WEAK = "weak"             # <50% match


class RecommendationReason(Enum):
    """Reasons for recommendation"""
    GENRE_MATCH = "genre_match"
    BUDGET_FIT = "budget_fit"
    AUDIENCE_MATCH = "audience_match"
    AVAILABILITY = "availability"
    TREND_MOMENTUM = "trend_momentum"
    VALUE_OPPORTUNITY = "value_opportunity"
    STRATEGIC_FIT = "strategic_fit"
    GEOGRAPHIC_MATCH = "geographic_match"


@dataclass
class ArtistProfile:
    """Simplified artist profile for matching"""
    name: str
    genres: List[str]
    tier: str
    monthly_listeners: int
    estimated_fee: int
    trend: str
    countries: List[str]
    event_types: List[str]
    availability: float  # 0-1, how available
    social_reach: int
    age_demographic: str  # "18-24", "25-34", etc.


@dataclass
class OpportunityProfile:
    """Opportunity profile for matching"""
    id: str
    title: str
    event_type: str
    genres_wanted: List[str]
    budget_min: int
    budget_max: int
    location: str
    country: str
    date: Optional[datetime]
    audience_size: int
    audience_demographic: str
    requirements: List[str]


@dataclass
class MatchScore:
    """Detailed match scoring"""
    overall_score: float  # 0-100
    match_type: MatchType
    
    # Component scores
    genre_score: float
    budget_score: float
    audience_score: float
    geographic_score: float
    availability_score: float
    momentum_score: float
    
    # Explanations
    reasons: List[str]
    concerns: List[str]
    
    # Value assessment
    value_rating: str  # "excellent", "good", "fair", "poor"
    negotiation_room: int  # Estimated € below max budget


@dataclass
class ArtistRecommendation:
    """Recommendation for an artist"""
    artist: ArtistProfile
    opportunity: OpportunityProfile
    match_score: MatchScore
    
    # AI insights
    why_book: str
    negotiation_tip: str
    alternative_suggestions: List[str]
    
    # Timing
    urgency: str  # "high", "medium", "low"
    best_contact_window: str


@dataclass
class OpportunityRecommendation:
    """Recommendation for an opportunity (for artist side)"""
    opportunity: OpportunityProfile
    match_score: MatchScore
    
    # Fit analysis
    why_apply: str
    success_probability: float
    expected_fee: int
    
    # Competition
    competition_level: str  # "low", "medium", "high"
    unique_advantage: str


class SmartRecommendationEngine:
    """
    AI-powered recommendation engine for matching artists to opportunities.
    Uses multi-factor scoring and intelligent filtering.
    """
    
    # Genre compatibility matrix (simplified)
    GENRE_COMPATIBILITY = {
        "pop": {"pop": 1.0, "dance": 0.8, "r&b": 0.7, "hip-hop": 0.6, "indie": 0.5},
        "hip-hop": {"hip-hop": 1.0, "rap": 0.95, "r&b": 0.8, "pop": 0.6, "dance": 0.5},
        "rap": {"rap": 1.0, "hip-hop": 0.95, "r&b": 0.7, "pop": 0.5},
        "electronic": {"electronic": 1.0, "dance": 0.9, "house": 0.9, "techno": 0.85, "pop": 0.5},
        "dance": {"dance": 1.0, "electronic": 0.9, "house": 0.85, "pop": 0.7},
        "rock": {"rock": 1.0, "indie": 0.7, "metal": 0.6, "pop": 0.4},
        "indie": {"indie": 1.0, "rock": 0.7, "folk": 0.6, "pop": 0.5},
        "r&b": {"r&b": 1.0, "hip-hop": 0.8, "pop": 0.7, "jazz": 0.5},
        "jazz": {"jazz": 1.0, "r&b": 0.5, "soul": 0.7},
        "latin": {"latin": 1.0, "reggaeton": 0.9, "pop": 0.6},
        "reggaeton": {"reggaeton": 1.0, "latin": 0.9, "hip-hop": 0.6, "dance": 0.6},
    }
    
    # Country proximity (for geographic matching)
    COUNTRY_PROXIMITY = {
        "FR": {"FR": 1.0, "BE": 0.9, "CH": 0.85, "LU": 0.85, "DE": 0.7, "ES": 0.7, "IT": 0.7, "UK": 0.6},
        "BE": {"BE": 1.0, "FR": 0.9, "NL": 0.85, "LU": 0.9, "DE": 0.75},
        "CH": {"CH": 1.0, "FR": 0.85, "DE": 0.85, "IT": 0.8, "AT": 0.75},
    }
    
    def __init__(self):
        self.recommendation_cache: Dict[str, List[ArtistRecommendation]] = {}
    
    def match_artist_to_opportunity(
        self,
        artist: ArtistProfile,
        opportunity: OpportunityProfile
    ) -> MatchScore:
        """Calculate detailed match score between artist and opportunity"""
        
        # Genre matching
        genre_score = self._calculate_genre_score(
            artist.genres, opportunity.genres_wanted
        )
        
        # Budget matching
        budget_score, negotiation_room = self._calculate_budget_score(
            artist.estimated_fee,
            opportunity.budget_min,
            opportunity.budget_max
        )
        
        # Audience matching
        audience_score = self._calculate_audience_score(
            artist.monthly_listeners,
            artist.social_reach,
            artist.age_demographic,
            opportunity.audience_size,
            opportunity.audience_demographic
        )
        
        # Geographic matching
        geographic_score = self._calculate_geographic_score(
            artist.countries,
            opportunity.country
        )
        
        # Availability score
        availability_score = artist.availability * 100
        
        # Momentum score (based on trend)
        momentum_score = self._calculate_momentum_score(artist.trend)
        
        # Calculate overall score (weighted average)
        overall_score = (
            genre_score * 0.25 +
            budget_score * 0.25 +
            audience_score * 0.15 +
            geographic_score * 0.15 +
            availability_score * 0.10 +
            momentum_score * 0.10
        )
        
        # Determine match type
        match_type = self._get_match_type(overall_score)
        
        # Generate reasons and concerns
        reasons, concerns = self._generate_match_analysis(
            genre_score, budget_score, audience_score,
            geographic_score, availability_score, momentum_score,
            artist, opportunity
        )
        
        # Value rating
        value_rating = self._calculate_value_rating(
            artist.estimated_fee,
            artist.monthly_listeners,
            opportunity.budget_max
        )
        
        return MatchScore(
            overall_score=overall_score,
            match_type=match_type,
            genre_score=genre_score,
            budget_score=budget_score,
            audience_score=audience_score,
            geographic_score=geographic_score,
            availability_score=availability_score,
            momentum_score=momentum_score,
            reasons=reasons,
            concerns=concerns,
            value_rating=value_rating,
            negotiation_room=negotiation_room
        )
    
    def _calculate_genre_score(
        self,
        artist_genres: List[str],
        wanted_genres: List[str]
    ) -> float:
        """Calculate genre compatibility score"""
        
        if not wanted_genres or not artist_genres:
            return 50.0  # Neutral score
        
        best_match = 0.0
        for artist_genre in artist_genres:
            artist_genre_lower = artist_genre.lower()
            for wanted_genre in wanted_genres:
                wanted_genre_lower = wanted_genre.lower()
                
                # Direct match
                if artist_genre_lower == wanted_genre_lower:
                    best_match = max(best_match, 1.0)
                else:
                    # Check compatibility matrix
                    genre_compat = self.GENRE_COMPATIBILITY.get(artist_genre_lower, {})
                    compat = genre_compat.get(wanted_genre_lower, 0.3)
                    best_match = max(best_match, compat)
        
        return best_match * 100
    
    def _calculate_budget_score(
        self,
        artist_fee: int,
        budget_min: int,
        budget_max: int
    ) -> Tuple[float, int]:
        """Calculate budget fit score and negotiation room"""
        
        if artist_fee <= budget_min:
            # Well under budget - great value!
            score = 100.0
            room = budget_max - artist_fee
        elif artist_fee <= budget_max:
            # Within budget
            position = (artist_fee - budget_min) / max(budget_max - budget_min, 1)
            score = 100 - (position * 30)  # 70-100 range
            room = budget_max - artist_fee
        else:
            # Over budget
            overage = (artist_fee - budget_max) / budget_max
            score = max(0, 50 - overage * 100)
            room = 0
        
        return score, room
    
    def _calculate_audience_score(
        self,
        listeners: int,
        social_reach: int,
        artist_demo: str,
        event_audience: int,
        event_demo: str
    ) -> float:
        """Calculate audience compatibility score"""
        
        # Size matching (is artist appropriate for event size?)
        if event_audience > 0:
            ratio = listeners / event_audience
            if 0.5 <= ratio <= 10:
                size_score = 100 - abs(1 - min(ratio, 2)) * 25
            elif ratio > 10:
                size_score = 60  # Overqualified but ok
            else:
                size_score = 40  # Might be too small
        else:
            size_score = 70  # Unknown event size
        
        # Demographic matching
        if artist_demo and event_demo:
            demo_score = 100 if artist_demo == event_demo else 60
        else:
            demo_score = 70
        
        return (size_score * 0.6 + demo_score * 0.4)
    
    def _calculate_geographic_score(
        self,
        artist_countries: List[str],
        event_country: str
    ) -> float:
        """Calculate geographic compatibility"""
        
        if not artist_countries or not event_country:
            return 70.0
        
        best_proximity = 0.0
        for country in artist_countries:
            country_prox = self.COUNTRY_PROXIMITY.get(country, {})
            proximity = country_prox.get(event_country, 0.3)
            best_proximity = max(best_proximity, proximity)
        
        return best_proximity * 100
    
    def _calculate_momentum_score(self, trend: str) -> float:
        """Calculate momentum score from trend"""
        
        trend_scores = {
            "explosive": 100,
            "rapid": 90,
            "strong": 80,
            "moderate": 70,
            "stable": 60,
            "declining": 40,
            "falling": 20,
        }
        return trend_scores.get(trend.lower(), 60)
    
    def _get_match_type(self, score: float) -> MatchType:
        """Determine match type from score"""
        
        if score >= 90:
            return MatchType.PERFECT
        elif score >= 80:
            return MatchType.EXCELLENT
        elif score >= 70:
            return MatchType.GOOD
        elif score >= 60:
            return MatchType.FAIR
        elif score >= 50:
            return MatchType.POSSIBLE
        else:
            return MatchType.WEAK
    
    def _generate_match_analysis(
        self,
        genre: float,
        budget: float,
        audience: float,
        geo: float,
        avail: float,
        momentum: float,
        artist: ArtistProfile,
        opportunity: OpportunityProfile
    ) -> Tuple[List[str], List[str]]:
        """Generate reasons and concerns for the match"""
        
        reasons = []
        concerns = []
        
        # Genre
        if genre >= 80:
            reasons.append(f"✅ Excellent match musical ({artist.genres[0] if artist.genres else 'genre'})")
        elif genre < 50:
            concerns.append(f"⚠️ Style musical différent des attentes")
        
        # Budget
        if budget >= 90:
            reasons.append(f"💰 Excellent rapport qualité/prix ({artist.estimated_fee:,}€)")
        elif budget >= 70:
            reasons.append(f"💵 Dans le budget ({artist.estimated_fee:,}€)")
        elif budget < 50:
            concerns.append(f"💸 Au-dessus du budget ({artist.estimated_fee:,}€ vs max {opportunity.budget_max:,}€)")
        
        # Audience
        if audience >= 80:
            reasons.append(f"👥 Audience parfaitement adaptée ({artist.monthly_listeners:,} listeners)")
        elif audience < 50:
            concerns.append(f"👥 Taille d'audience potentiellement inadaptée")
        
        # Geographic
        if geo >= 90:
            reasons.append(f"📍 Artiste local/régional - base de fans présente")
        elif geo < 50:
            concerns.append(f"📍 Artiste géographiquement éloigné")
        
        # Availability
        if avail < 50:
            concerns.append(f"📅 Disponibilité limitée")
        
        # Momentum
        if momentum >= 80:
            reasons.append(f"📈 En forte croissance - timing parfait")
        elif momentum < 40:
            concerns.append(f"📉 Tendance à la baisse")
        
        return reasons, concerns
    
    def _calculate_value_rating(
        self,
        fee: int,
        listeners: int,
        max_budget: int
    ) -> str:
        """Calculate value for money rating"""
        
        # Cost per thousand listeners
        cptl = (fee / max(listeners, 1)) * 1000
        
        # Compare to budget utilization
        budget_util = fee / max(max_budget, 1)
        
        if cptl < 50 and budget_util < 0.7:
            return "excellent"
        elif cptl < 100 and budget_util < 0.9:
            return "good"
        elif budget_util <= 1.0:
            return "fair"
        else:
            return "poor"
    
    def find_best_artists_for_opportunity(
        self,
        opportunity: OpportunityProfile,
        artists: List[ArtistProfile],
        limit: int = 10
    ) -> List[ArtistRecommendation]:
        """Find best matching artists for an opportunity"""
        
        recommendations = []
        
        for artist in artists:
            match_score = self.match_artist_to_opportunity(artist, opportunity)
            
            # Generate recommendation
            recommendation = ArtistRecommendation(
                artist=artist,
                opportunity=opportunity,
                match_score=match_score,
                why_book=self._generate_why_book(artist, match_score),
                negotiation_tip=self._generate_negotiation_tip(artist, match_score),
                alternative_suggestions=[],
                urgency=self._calculate_urgency(artist, match_score),
                best_contact_window=self._suggest_contact_window(artist)
            )
            recommendations.append(recommendation)
        
        # Sort by match score
        recommendations.sort(key=lambda r: r.match_score.overall_score, reverse=True)
        
        # Add alternative suggestions
        for i, rec in enumerate(recommendations[:limit]):
            alternatives = [r.artist.name for r in recommendations[i+1:i+4] if r.match_score.overall_score >= 60]
            rec.alternative_suggestions = alternatives
        
        return recommendations[:limit]
    
    def find_best_opportunities_for_artist(
        self,
        artist: ArtistProfile,
        opportunities: List[OpportunityProfile],
        limit: int = 10
    ) -> List[OpportunityRecommendation]:
        """Find best matching opportunities for an artist"""
        
        recommendations = []
        
        for opportunity in opportunities:
            match_score = self.match_artist_to_opportunity(artist, opportunity)
            
            recommendation = OpportunityRecommendation(
                opportunity=opportunity,
                match_score=match_score,
                why_apply=self._generate_why_apply(opportunity, match_score),
                success_probability=self._estimate_success_probability(match_score),
                expected_fee=self._estimate_expected_fee(artist, opportunity, match_score),
                competition_level=self._estimate_competition(opportunity),
                unique_advantage=self._find_unique_advantage(artist, opportunity)
            )
            recommendations.append(recommendation)
        
        # Sort by match score
        recommendations.sort(key=lambda r: r.match_score.overall_score, reverse=True)
        
        return recommendations[:limit]
    
    def _generate_why_book(self, artist: ArtistProfile, match: MatchScore) -> str:
        """Generate why to book explanation"""
        
        if match.match_type == MatchType.PERFECT:
            return f"🎯 Match parfait! {artist.name} coche toutes les cases avec un excellent rapport qualité/prix."
        elif match.match_type == MatchType.EXCELLENT:
            return f"⭐ Excellent choix! {artist.name} offre un très bon fit pour cette opportunité."
        elif match.match_type == MatchType.GOOD:
            return f"✅ Bon match. {artist.name} répond bien aux critères principaux."
        elif match.match_type == MatchType.FAIR:
            return f"🤔 Match correct. {artist.name} pourrait convenir avec quelques ajustements."
        else:
            return f"⚠️ Match partiel. Considérer d'autres options en priorité."
    
    def _generate_negotiation_tip(self, artist: ArtistProfile, match: MatchScore) -> str:
        """Generate negotiation advice"""
        
        if match.negotiation_room > 5000:
            return f"💪 Forte marge de négociation. L'artiste est bien en-dessous du budget max. Viser {artist.estimated_fee:,}€."
        elif match.negotiation_room > 1000:
            return f"📊 Marge de négociation: ~{match.negotiation_room:,}€. Proposer le prix demandé."
        elif match.budget_score >= 70:
            return f"💵 Budget serré mais réalisable. Peu de marge de négociation."
        else:
            return f"⚠️ Au-dessus du budget. Négociation difficile - envisager alternatives."
    
    def _calculate_urgency(self, artist: ArtistProfile, match: MatchScore) -> str:
        """Calculate booking urgency"""
        
        if artist.trend in ["explosive", "rapid"] and match.overall_score >= 70:
            return "high"
        elif artist.availability < 0.5:
            return "high"
        elif match.overall_score >= 80:
            return "medium"
        else:
            return "low"
    
    def _suggest_contact_window(self, artist: ArtistProfile) -> str:
        """Suggest best time to contact"""
        
        if artist.tier in ["superstar", "major"]:
            return "Contact agent 6-12 mois à l'avance"
        elif artist.tier == "established":
            return "Contact agent/management 3-6 mois à l'avance"
        else:
            return "Contact direct possible, 1-3 mois à l'avance"
    
    def _generate_why_apply(self, opportunity: OpportunityProfile, match: MatchScore) -> str:
        """Generate why to apply explanation"""
        
        if match.overall_score >= 80:
            return f"🎯 Opportunité idéale pour votre profil! Fort taux de succès attendu."
        elif match.overall_score >= 60:
            return f"✅ Bonne correspondance. Candidature recommandée."
        else:
            return f"🤔 Match partiel. Considérer avant de postuler."
    
    def _estimate_success_probability(self, match: MatchScore) -> float:
        """Estimate probability of successful booking"""
        
        # Base from match score
        base = match.overall_score / 100
        
        # Adjust for budget fit
        if match.budget_score < 50:
            base *= 0.5
        
        return min(0.95, base)
    
    def _estimate_expected_fee(
        self,
        artist: ArtistProfile,
        opportunity: OpportunityProfile,
        match: MatchScore
    ) -> int:
        """Estimate expected fee for this opportunity"""
        
        if match.budget_score >= 90:
            # Ask for more, still within budget
            return min(artist.estimated_fee + 1000, opportunity.budget_max)
        elif match.budget_score >= 70:
            return artist.estimated_fee
        else:
            # May need to negotiate down
            return min(artist.estimated_fee, opportunity.budget_max)
    
    def _estimate_competition(self, opportunity: OpportunityProfile) -> str:
        """Estimate competition level for opportunity"""
        
        # Simplified - would need real data
        if opportunity.budget_max > 20000:
            return "high"  # High-paying = high competition
        elif opportunity.budget_max > 5000:
            return "medium"
        else:
            return "low"
    
    def _find_unique_advantage(
        self,
        artist: ArtistProfile,
        opportunity: OpportunityProfile
    ) -> str:
        """Find artist's unique advantage for this opportunity"""
        
        advantages = []
        
        if opportunity.country in artist.countries:
            advantages.append("Base de fans locale")
        
        if artist.trend in ["explosive", "rapid"]:
            advantages.append("Artiste en pleine croissance")
        
        if artist.availability > 0.8:
            advantages.append("Haute disponibilité")
        
        if advantages:
            return advantages[0]
        else:
            return "Profil adapté aux critères"


# Singleton instance
recommendation_engine = SmartRecommendationEngine()
