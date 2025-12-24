"""
Artist Discovery Engine
Automatic detection of emerging artists with high potential
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DiscoverySignal(Enum):
    """Types of discovery signals"""
    VIRAL_GROWTH = "viral_growth"           # Sudden spike in metrics
    PLAYLIST_BOOST = "playlist_boost"       # Major playlist placement
    MEDIA_BUZZ = "media_buzz"               # Press/media mentions
    SOCIAL_SURGE = "social_surge"           # Social media viral moment
    COLLAB_BOOST = "collab_boost"           # Featured on major track
    AWARD_NOMINATION = "award_nomination"   # Industry recognition
    LABEL_SIGNING = "label_signing"         # Major label deal


class PotentialLevel(Enum):
    """Artist potential classification"""
    EXPLOSIVE = "explosive"     # Very high potential (90-100%)
    HIGH = "high"               # High potential (70-89%)
    PROMISING = "promising"     # Promising (50-69%)
    MODERATE = "moderate"       # Moderate potential (30-49%)
    LOW = "low"                 # Low potential (<30%)


@dataclass
class DiscoveryPattern:
    """Pattern detected in artist growth"""
    pattern_type: str
    confidence: float
    description: str
    impact_score: float  # 0-1
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EmergingArtist:
    """Emerging artist profile"""
    name: str
    spotify_id: Optional[str]
    genres: List[str]
    
    # Current metrics
    monthly_listeners: int
    spotify_followers: int
    total_social_followers: int
    
    # Growth metrics
    growth_velocity: float  # Monthly growth rate
    acceleration: float     # Rate of growth change
    
    # Discovery signals
    signals: List[DiscoverySignal]
    patterns: List[DiscoveryPattern]
    
    # Potential assessment
    potential_level: PotentialLevel
    potential_score: float  # 0-100
    breakout_probability: float  # 0-1
    
    # Timing
    discovered_at: datetime
    estimated_breakout: Optional[str]  # "3-6 months", etc.
    
    # Recommendations
    why_watch: List[str]
    booking_advice: str
    estimated_current_fee: int
    estimated_future_fee: int


@dataclass
class DiscoveryReport:
    """Full discovery report"""
    generated_at: datetime
    total_analyzed: int
    emerging_artists: List[EmergingArtist]
    top_picks: List[str]
    market_trends: Dict[str, Any]
    genre_hotspots: Dict[str, float]


class ArtistDiscoveryEngine:
    """
    AI-powered engine to discover emerging artists with high potential.
    Analyzes growth patterns, detects signals, and predicts breakouts.
    """
    
    # Growth thresholds
    VIRAL_GROWTH_THRESHOLD = 0.5      # 50% monthly = viral
    RAPID_GROWTH_THRESHOLD = 0.25     # 25% monthly = rapid
    PROMISING_GROWTH_THRESHOLD = 0.10  # 10% monthly = promising
    
    # Listener thresholds for "emerging"
    MIN_LISTENERS = 1000
    MAX_LISTENERS = 500000  # Above this = already established
    
    def __init__(self):
        self.discovery_cache: Dict[str, EmergingArtist] = {}
        self.analysis_history: List[DiscoveryReport] = []
    
    def analyze_for_potential(
        self,
        artist_name: str,
        monthly_listeners: int,
        spotify_followers: int = 0,
        social_followers: int = 0,
        genres: List[str] = None,
        spotify_id: str = None,
        historical_listeners: List[int] = None,
        recent_events: List[Dict] = None,
    ) -> EmergingArtist:
        """
        Analyze an artist for emerging potential.
        Returns EmergingArtist profile with potential assessment.
        """
        genres = genres or []
        historical_listeners = historical_listeners or []
        recent_events = recent_events or []
        
        # Calculate growth metrics
        growth_velocity, acceleration = self._calculate_growth_metrics(
            monthly_listeners, historical_listeners
        )
        
        # Detect signals
        signals = self._detect_signals(
            growth_velocity, acceleration, recent_events
        )
        
        # Detect patterns
        patterns = self._detect_patterns(
            historical_listeners, growth_velocity, acceleration
        )
        
        # Calculate potential
        potential_score, potential_level = self._assess_potential(
            monthly_listeners, growth_velocity, acceleration,
            signals, patterns
        )
        
        # Calculate breakout probability
        breakout_prob = self._calculate_breakout_probability(
            potential_score, signals, patterns, growth_velocity
        )
        
        # Estimate breakout timing
        estimated_breakout = self._estimate_breakout_timing(
            monthly_listeners, growth_velocity, breakout_prob
        )
        
        # Generate recommendations
        why_watch = self._generate_watch_reasons(
            signals, patterns, growth_velocity, potential_level
        )
        
        booking_advice = self._generate_booking_advice(
            potential_level, growth_velocity, breakout_prob
        )
        
        # Estimate fees
        current_fee = self._estimate_current_fee(
            monthly_listeners, social_followers, growth_velocity
        )
        future_fee = self._estimate_future_fee(
            current_fee, growth_velocity, breakout_prob
        )
        
        artist = EmergingArtist(
            name=artist_name,
            spotify_id=spotify_id,
            genres=genres,
            monthly_listeners=monthly_listeners,
            spotify_followers=spotify_followers,
            total_social_followers=social_followers,
            growth_velocity=growth_velocity,
            acceleration=acceleration,
            signals=signals,
            patterns=patterns,
            potential_level=potential_level,
            potential_score=potential_score,
            breakout_probability=breakout_prob,
            discovered_at=datetime.utcnow(),
            estimated_breakout=estimated_breakout,
            why_watch=why_watch,
            booking_advice=booking_advice,
            estimated_current_fee=current_fee,
            estimated_future_fee=future_fee,
        )
        
        # Cache the discovery
        self.discovery_cache[artist_name.lower()] = artist
        
        return artist
    
    def _calculate_growth_metrics(
        self,
        current_listeners: int,
        historical: List[int]
    ) -> Tuple[float, float]:
        """Calculate growth velocity and acceleration"""
        
        if not historical or len(historical) < 2:
            # No history - assume moderate growth potential
            return 0.05, 0.0
        
        # Growth velocity: average monthly growth rate
        growth_rates = []
        for i in range(1, len(historical)):
            if historical[i-1] > 0:
                rate = (historical[i] - historical[i-1]) / historical[i-1]
                growth_rates.append(rate)
        
        if not growth_rates:
            return 0.0, 0.0
        
        velocity = sum(growth_rates) / len(growth_rates)
        
        # Acceleration: is growth speeding up or slowing down?
        if len(growth_rates) >= 2:
            recent_growth = sum(growth_rates[-2:]) / 2
            older_growth = sum(growth_rates[:-2]) / max(1, len(growth_rates) - 2) if len(growth_rates) > 2 else growth_rates[0]
            acceleration = recent_growth - older_growth
        else:
            acceleration = 0.0
        
        return velocity, acceleration
    
    def _detect_signals(
        self,
        growth_velocity: float,
        acceleration: float,
        recent_events: List[Dict]
    ) -> List[DiscoverySignal]:
        """Detect discovery signals"""
        
        signals = []
        
        # Viral growth detection
        if growth_velocity >= self.VIRAL_GROWTH_THRESHOLD:
            signals.append(DiscoverySignal.VIRAL_GROWTH)
        
        # Social surge (if acceleration is very high)
        if acceleration > 0.2:
            signals.append(DiscoverySignal.SOCIAL_SURGE)
        
        # Check recent events for signals
        for event in recent_events:
            event_type = event.get("type", "").lower()
            if "playlist" in event_type:
                signals.append(DiscoverySignal.PLAYLIST_BOOST)
            elif "collab" in event_type or "feat" in event_type:
                signals.append(DiscoverySignal.COLLAB_BOOST)
            elif "award" in event_type:
                signals.append(DiscoverySignal.AWARD_NOMINATION)
            elif "label" in event_type or "signed" in event_type:
                signals.append(DiscoverySignal.LABEL_SIGNING)
            elif "press" in event_type or "media" in event_type:
                signals.append(DiscoverySignal.MEDIA_BUZZ)
        
        return list(set(signals))  # Remove duplicates
    
    def _detect_patterns(
        self,
        historical: List[int],
        velocity: float,
        acceleration: float
    ) -> List[DiscoveryPattern]:
        """Detect growth patterns"""
        
        patterns = []
        
        if not historical:
            return patterns
        
        # Hockey stick pattern (slow then rapid)
        if len(historical) >= 4:
            first_half = historical[:len(historical)//2]
            second_half = historical[len(historical)//2:]
            
            if first_half and second_half:
                first_growth = (first_half[-1] - first_half[0]) / max(first_half[0], 1)
                second_growth = (second_half[-1] - second_half[0]) / max(second_half[0], 1)
                
                if second_growth > first_growth * 3 and second_growth > 0.3:
                    patterns.append(DiscoveryPattern(
                        pattern_type="hockey_stick",
                        confidence=0.85,
                        description="Croissance en bâton de hockey - décollage récent",
                        impact_score=0.9
                    ))
        
        # Steady climb pattern
        if velocity > 0.1 and acceleration >= 0:
            consecutive_growth = all(
                historical[i] >= historical[i-1] 
                for i in range(1, len(historical))
            ) if len(historical) > 1 else False
            
            if consecutive_growth:
                patterns.append(DiscoveryPattern(
                    pattern_type="steady_climb",
                    confidence=0.8,
                    description="Croissance régulière et constante",
                    impact_score=0.7
                ))
        
        # Spike pattern (sudden jump)
        if len(historical) >= 3:
            for i in range(1, len(historical)):
                if historical[i-1] > 0:
                    jump = (historical[i] - historical[i-1]) / historical[i-1]
                    if jump > 1.0:  # Doubled
                        patterns.append(DiscoveryPattern(
                            pattern_type="spike",
                            confidence=0.9,
                            description=f"Spike majeur détecté (+{int(jump*100)}%)",
                            impact_score=0.85
                        ))
                        break
        
        # Accelerating pattern
        if acceleration > 0.1:
            patterns.append(DiscoveryPattern(
                pattern_type="accelerating",
                confidence=0.75,
                description="Croissance en accélération",
                impact_score=0.8
            ))
        
        return patterns
    
    def _assess_potential(
        self,
        listeners: int,
        velocity: float,
        acceleration: float,
        signals: List[DiscoverySignal],
        patterns: List[DiscoveryPattern]
    ) -> Tuple[float, PotentialLevel]:
        """Assess overall potential score and level"""
        
        score = 30  # Base score
        
        # Velocity contribution (max 30 points)
        velocity_score = min(30, velocity * 100)
        score += velocity_score
        
        # Acceleration contribution (max 15 points)
        if acceleration > 0:
            accel_score = min(15, acceleration * 50)
            score += accel_score
        
        # Signal contribution (max 15 points)
        signal_weights = {
            DiscoverySignal.VIRAL_GROWTH: 5,
            DiscoverySignal.PLAYLIST_BOOST: 4,
            DiscoverySignal.COLLAB_BOOST: 4,
            DiscoverySignal.LABEL_SIGNING: 5,
            DiscoverySignal.MEDIA_BUZZ: 3,
            DiscoverySignal.SOCIAL_SURGE: 4,
            DiscoverySignal.AWARD_NOMINATION: 4,
        }
        signal_score = sum(signal_weights.get(s, 2) for s in signals)
        score += min(15, signal_score)
        
        # Pattern contribution (max 10 points)
        pattern_score = sum(p.impact_score * 5 for p in patterns)
        score += min(10, pattern_score)
        
        # Sweet spot bonus: not too small, not too big
        if 10000 <= listeners <= 100000:
            score += 5  # Ideal emerging range
        elif listeners > self.MAX_LISTENERS:
            score -= 10  # Already established
        
        score = max(0, min(100, score))
        
        # Determine level
        if score >= 90:
            level = PotentialLevel.EXPLOSIVE
        elif score >= 70:
            level = PotentialLevel.HIGH
        elif score >= 50:
            level = PotentialLevel.PROMISING
        elif score >= 30:
            level = PotentialLevel.MODERATE
        else:
            level = PotentialLevel.LOW
        
        return score, level
    
    def _calculate_breakout_probability(
        self,
        potential_score: float,
        signals: List[DiscoverySignal],
        patterns: List[DiscoveryPattern],
        velocity: float
    ) -> float:
        """Calculate probability of artist breakout"""
        
        prob = potential_score / 200  # Base from score (0-0.5)
        
        # Boost from strong signals
        if DiscoverySignal.VIRAL_GROWTH in signals:
            prob += 0.2
        if DiscoverySignal.PLAYLIST_BOOST in signals:
            prob += 0.15
        if DiscoverySignal.LABEL_SIGNING in signals:
            prob += 0.15
        
        # Boost from patterns
        for pattern in patterns:
            if pattern.pattern_type == "hockey_stick":
                prob += 0.2
            elif pattern.pattern_type == "accelerating":
                prob += 0.1
        
        return min(0.95, prob)
    
    def _estimate_breakout_timing(
        self,
        listeners: int,
        velocity: float,
        breakout_prob: float
    ) -> Optional[str]:
        """Estimate when artist might break out"""
        
        if breakout_prob < 0.3:
            return None
        
        # Calculate months to reach "established" (100K listeners)
        target = 100000
        if listeners >= target:
            return "Déjà établi"
        
        if velocity <= 0:
            return "Incertain"
        
        # Simple compound growth estimation
        months = 0
        current = listeners
        while current < target and months < 36:
            current *= (1 + velocity)
            months += 1
        
        if months <= 3:
            return "1-3 mois"
        elif months <= 6:
            return "3-6 mois"
        elif months <= 12:
            return "6-12 mois"
        elif months <= 24:
            return "1-2 ans"
        else:
            return "Long terme (2+ ans)"
    
    def _generate_watch_reasons(
        self,
        signals: List[DiscoverySignal],
        patterns: List[DiscoveryPattern],
        velocity: float,
        level: PotentialLevel
    ) -> List[str]:
        """Generate reasons to watch this artist"""
        
        reasons = []
        
        if level == PotentialLevel.EXPLOSIVE:
            reasons.append("🚀 Potentiel explosif - opportunité rare")
        elif level == PotentialLevel.HIGH:
            reasons.append("⭐ Fort potentiel de croissance")
        
        if DiscoverySignal.VIRAL_GROWTH in signals:
            reasons.append("📈 Croissance virale en cours")
        if DiscoverySignal.PLAYLIST_BOOST in signals:
            reasons.append("🎵 Boost playlist majeur détecté")
        if DiscoverySignal.COLLAB_BOOST in signals:
            reasons.append("🤝 Collaboration récente impactante")
        if DiscoverySignal.LABEL_SIGNING in signals:
            reasons.append("📝 Signature label récente")
        
        for pattern in patterns:
            if pattern.pattern_type == "hockey_stick":
                reasons.append("📊 Pattern 'hockey stick' - décollage imminent")
            elif pattern.pattern_type == "accelerating":
                reasons.append("⚡ Croissance en accélération")
        
        if velocity >= 0.5:
            reasons.append(f"💹 +{int(velocity*100)}% croissance mensuelle")
        
        if not reasons:
            reasons.append("📌 À surveiller pour évolution")
        
        return reasons[:5]  # Max 5 reasons
    
    def _generate_booking_advice(
        self,
        level: PotentialLevel,
        velocity: float,
        breakout_prob: float
    ) -> str:
        """Generate booking advice"""
        
        if level == PotentialLevel.EXPLOSIVE:
            return "🔥 BOOK MAINTENANT - Tarifs vont exploser. Fenêtre d'opportunité très courte."
        elif level == PotentialLevel.HIGH:
            return "⚡ Book rapidement - Prix avantageux actuellement. Prévoir hausse dans 3-6 mois."
        elif level == PotentialLevel.PROMISING:
            return "👀 Bon timing pour négocier. Surveiller évolution sur 2-3 mois."
        elif level == PotentialLevel.MODERATE:
            return "🤔 Potentiel à confirmer. Attendre signaux supplémentaires."
        else:
            return "⏳ Pas prioritaire - Focus sur artistes plus établis."
    
    def _estimate_current_fee(
        self,
        listeners: int,
        social: int,
        velocity: float
    ) -> int:
        """Estimate current booking fee"""
        
        # Base fee from listeners
        if listeners < 5000:
            base = 300
        elif listeners < 20000:
            base = 800
        elif listeners < 50000:
            base = 2000
        elif listeners < 100000:
            base = 4000
        elif listeners < 250000:
            base = 8000
        elif listeners < 500000:
            base = 15000
        else:
            base = 25000
        
        # Velocity multiplier
        if velocity >= 0.5:
            base *= 1.5
        elif velocity >= 0.25:
            base *= 1.25
        
        # Social bonus
        if social > listeners * 2:
            base *= 1.2
        
        return int(base)
    
    def _estimate_future_fee(
        self,
        current_fee: int,
        velocity: float,
        breakout_prob: float
    ) -> int:
        """Estimate fee in 6-12 months"""
        
        if velocity <= 0:
            return current_fee
        
        # Project 6 months forward
        multiplier = (1 + velocity) ** 6
        
        # Add breakout bonus
        if breakout_prob > 0.7:
            multiplier *= 2  # Could double if breaks out
        elif breakout_prob > 0.5:
            multiplier *= 1.5
        
        return int(current_fee * multiplier)
    
    def get_top_discoveries(
        self,
        limit: int = 10
    ) -> List[EmergingArtist]:
        """Get top discoveries from cache"""
        
        artists = list(self.discovery_cache.values())
        return sorted(
            artists,
            key=lambda a: a.potential_score,
            reverse=True
        )[:limit]
    
    def generate_discovery_report(
        self,
        artists: List[EmergingArtist]
    ) -> DiscoveryReport:
        """Generate comprehensive discovery report"""
        
        # Analyze market trends
        if artists:
            avg_velocity = sum(a.growth_velocity for a in artists) / len(artists)
            avg_potential = sum(a.potential_score for a in artists) / len(artists)
        else:
            avg_velocity = 0
            avg_potential = 0
        
        market_trends = {
            "average_growth_velocity": avg_velocity,
            "average_potential_score": avg_potential,
            "high_potential_count": len([a for a in artists if a.potential_level in [PotentialLevel.HIGH, PotentialLevel.EXPLOSIVE]]),
            "total_analyzed": len(artists),
        }
        
        # Genre hotspots
        genre_counts: Dict[str, List[float]] = {}
        for artist in artists:
            for genre in artist.genres:
                if genre not in genre_counts:
                    genre_counts[genre] = []
                genre_counts[genre].append(artist.potential_score)
        
        genre_hotspots = {
            genre: sum(scores) / len(scores)
            for genre, scores in genre_counts.items()
        }
        
        # Sort emerging artists by potential
        sorted_artists = sorted(
            artists,
            key=lambda a: a.potential_score,
            reverse=True
        )
        
        # Top picks
        top_picks = [a.name for a in sorted_artists[:5]]
        
        report = DiscoveryReport(
            generated_at=datetime.utcnow(),
            total_analyzed=len(artists),
            emerging_artists=sorted_artists,
            top_picks=top_picks,
            market_trends=market_trends,
            genre_hotspots=genre_hotspots,
        )
        
        self.analysis_history.append(report)
        
        return report


# Singleton instance
discovery_engine = ArtistDiscoveryEngine()
