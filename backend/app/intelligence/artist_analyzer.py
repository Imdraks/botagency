"""
Artist Analyzer - Analyse intelligente des artistes et de leur valeur marchande
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ArtistEvent:
    """Un événement passé d'un artiste"""
    name: str
    date: Optional[datetime]
    venue: Optional[str]
    location: Optional[str]
    event_type: str  # concert, festival, showcase, privé
    estimated_fee: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'date': self.date.isoformat() if self.date else None,
            'venue': self.venue,
            'location': self.location,
            'type': self.event_type,
            'estimated_fee': self.estimated_fee,
        }


@dataclass
class ArtistProfile:
    """Profil complet d'un artiste"""
    name: str
    aliases: List[str]
    genre: str
    popularity_score: float  # 0-100
    booking_contact: Optional[str]
    management: Optional[str]
    record_label: Optional[str]
    estimated_fee_range: tuple  # (min, max)
    recent_events: List[ArtistEvent]
    social_metrics: Dict[str, int]
    market_trend: str  # rising, stable, declining
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'aliases': self.aliases,
            'genre': self.genre,
            'popularity_score': self.popularity_score,
            'booking_contact': self.booking_contact,
            'management': self.management,
            'record_label': self.record_label,
            'fee_range': {
                'min': self.estimated_fee_range[0],
                'max': self.estimated_fee_range[1],
            },
            'recent_events': [e.to_dict() for e in self.recent_events],
            'social_metrics': self.social_metrics,
            'market_trend': self.market_trend,
        }


class ArtistAnalyzer:
    """
    Analyseur d'artistes qui :
    - Extrait les informations d'artistes depuis du texte web
    - Estime les cachets basés sur les données collectées
    - Analyse les événements passés
    - Évalue la tendance du marché
    """
    
    # Fourchettes de prix par niveau (en euros)
    FEE_TIERS = {
        'emerging': (1000, 5000),       # Artiste émergent
        'developing': (5000, 15000),    # En développement
        'established': (15000, 40000),  # Établi
        'star': (40000, 100000),        # Star nationale
        'superstar': (100000, 500000),  # Superstar
        'legend': (500000, 2000000),    # Légende
    }
    
    # Genres musicaux avec leurs keywords
    GENRES = {
        'rap': ['rap', 'hip-hop', 'hip hop', 'trap', 'drill', 'rnb', 'r&b'],
        'electro': ['electro', 'dj', 'techno', 'house', 'electronic'],
        'pop': ['pop', 'variété', 'chanson'],
        'rock': ['rock', 'metal', 'punk', 'alternatif'],
        'reggae': ['reggae', 'dancehall', 'dub'],
        'jazz': ['jazz', 'blues', 'soul'],
        'classique': ['classique', 'opéra', 'symphonique'],
    }
    
    # Venues connues avec leur capacité
    KNOWN_VENUES = {
        # Paris
        'stade de france': 80000,
        'accor arena': 20000,
        'bercy': 20000,
        'olympia': 2000,
        'zénith': 6000,
        'bataclan': 1500,
        'élysée montmartre': 1500,
        'cigale': 1400,
        'trianon': 1000,
        'alhambra': 800,
        'new morning': 450,
        'café de la danse': 400,
        # Festivals
        'solidays': 200000,
        'rock en seine': 120000,
        'main square': 100000,
        'vieilles charrues': 280000,
        'francofolies': 150000,
        'eurockéennes': 130000,
        'garorock': 140000,
        'hellfest': 180000,
        'lollapalooza': 100000,
    }
    
    def __init__(self):
        self.artist_cache: Dict[str, ArtistProfile] = {}
    
    def analyze_from_text(self, text: str, artist_name: Optional[str] = None) -> Optional[ArtistProfile]:
        """
        Analyse un artiste à partir de contenu web
        """
        if not artist_name:
            artist_name = self._detect_artist_name(text)
            if not artist_name:
                return None
        
        # Extraire les informations
        genre = self._detect_genre(text)
        events = self._extract_events(text, artist_name)
        contacts = self._extract_management_info(text)
        popularity = self._estimate_popularity(text, artist_name, events)
        fee_range = self._estimate_fee_range(popularity, genre, events)
        trend = self._analyze_trend(events, text)
        
        profile = ArtistProfile(
            name=artist_name,
            aliases=self._find_aliases(text, artist_name),
            genre=genre,
            popularity_score=popularity,
            booking_contact=contacts.get('booking'),
            management=contacts.get('management'),
            record_label=contacts.get('label'),
            estimated_fee_range=fee_range,
            recent_events=events,
            social_metrics=self._extract_social_metrics(text),
            market_trend=trend,
        )
        
        # Mettre en cache
        self.artist_cache[artist_name.lower()] = profile
        
        return profile
    
    def _detect_artist_name(self, text: str) -> Optional[str]:
        """Détecte le nom de l'artiste principal dans le texte"""
        # Patterns pour les noms d'artistes
        patterns = [
            r'(?:artiste|rappeur|rappeuse|chanteur|chanteuse|dj|groupe)[:\s]+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)?)',
            r'([A-Z]{2,}(?:\s+[A-Z]{2,})?)\s+(?:en concert|en tournée|au|aux)',
            r'(?:concert|spectacle|show) de ([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _detect_genre(self, text: str) -> str:
        """Détecte le genre musical"""
        text_lower = text.lower()
        
        genre_scores = {}
        for genre, keywords in self.GENRES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                genre_scores[genre] = score
        
        if genre_scores:
            return max(genre_scores, key=genre_scores.get)
        return 'unknown'
    
    def _extract_events(self, text: str, artist_name: str) -> List[ArtistEvent]:
        """Extrait les événements passés/futurs"""
        events = []
        
        # Patterns pour les événements
        event_patterns = [
            r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s*[:-]?\s*([^,\n]+)',
            r'(?:le|the)\s+(\d{1,2}\s+\w+\s+\d{4})\s*[:-]?\s*([^,\n]+)',
            r'(festival|concert|showcase)\s+([^,\n]+)\s+(?:le|on)\s+(\d{1,2}[/.-]\d{1,2})',
        ]
        
        text_lower = text.lower()
        
        # Chercher les venues connues
        for venue, capacity in self.KNOWN_VENUES.items():
            if venue in text_lower:
                # Essayer de trouver une date proche
                venue_idx = text_lower.find(venue)
                context = text[max(0, venue_idx-100):min(len(text), venue_idx+100)]
                
                date = self._extract_date(context)
                event_type = 'festival' if capacity > 10000 else 'concert'
                
                # Estimer le cachet par la capacité
                estimated_fee = self._estimate_fee_by_capacity(capacity)
                
                events.append(ArtistEvent(
                    name=f"Event @ {venue.title()}",
                    date=date,
                    venue=venue.title(),
                    location=self._extract_location(context),
                    event_type=event_type,
                    estimated_fee=estimated_fee,
                ))
        
        return events[:10]  # Max 10 events
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extrait une date d'un texte"""
        patterns = [
            (r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', '%d/%m/%Y'),
            (r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})', '%d/%m/%y'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = '/'.join(match.groups())
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extrait la ville/lieu"""
        cities = [
            'paris', 'lyon', 'marseille', 'bordeaux', 'toulouse',
            'nantes', 'lille', 'strasbourg', 'nice', 'montpellier'
        ]
        
        text_lower = text.lower()
        for city in cities:
            if city in text_lower:
                return city.title()
        return None
    
    def _extract_management_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extrait les infos de management"""
        result = {
            'booking': None,
            'management': None,
            'label': None,
        }
        
        # Patterns
        patterns = {
            'booking': r'(?:booking|tourneur)[:\s]+([^\n,]+)',
            'management': r'(?:management|manager)[:\s]+([^\n,]+)',
            'label': r'(?:label|maison de disques|signé chez)[:\s]+([^\n,]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()
        
        return result
    
    def _estimate_popularity(
        self, 
        text: str, 
        artist_name: str,
        events: List[ArtistEvent]
    ) -> float:
        """Estime la popularité (0-100)"""
        score = 50.0  # Base
        
        # Bonus pour les événements
        for event in events:
            if event.venue:
                venue_lower = event.venue.lower()
                if venue_lower in self.KNOWN_VENUES:
                    capacity = self.KNOWN_VENUES[venue_lower]
                    score += min(20, capacity / 5000)
        
        # Keywords de popularité
        text_lower = text.lower()
        if any(x in text_lower for x in ['disque d\'or', 'platine', 'diamond']):
            score += 20
        if any(x in text_lower for x in ['millions de vues', 'viral', 'buzz']):
            score += 15
        if 'tête d\'affiche' in text_lower or 'headliner' in text_lower:
            score += 15
        if 'victoire de la musique' in text_lower or 'nrj' in text_lower:
            score += 10
        
        return min(100, max(0, score))
    
    def _estimate_fee_range(
        self,
        popularity: float,
        genre: str,
        events: List[ArtistEvent]
    ) -> tuple:
        """Estime la fourchette de cachet"""
        # Déterminer le tier
        if popularity >= 90:
            tier = 'legend'
        elif popularity >= 75:
            tier = 'superstar'
        elif popularity >= 60:
            tier = 'star'
        elif popularity >= 45:
            tier = 'established'
        elif popularity >= 25:
            tier = 'developing'
        else:
            tier = 'emerging'
        
        base_range = self.FEE_TIERS[tier]
        
        # Ajuster par genre (rap et electro souvent plus cher)
        multiplier = 1.0
        if genre == 'rap':
            multiplier = 1.2
        elif genre == 'electro':
            multiplier = 1.1
        
        # Si on a des données d'events avec fees estimés
        if events:
            fees = [e.estimated_fee for e in events if e.estimated_fee]
            if fees:
                avg_fee = sum(fees) / len(fees)
                # Ajuster la range
                return (int(avg_fee * 0.7), int(avg_fee * 1.3))
        
        return (int(base_range[0] * multiplier), int(base_range[1] * multiplier))
    
    def _estimate_fee_by_capacity(self, capacity: int) -> float:
        """Estime le cachet par la capacité de la salle"""
        # Règle approximative: 2-5€ par spectateur pour l'artiste principal
        return capacity * 3.5
    
    def _analyze_trend(self, events: List[ArtistEvent], text: str) -> str:
        """Analyse la tendance du marché pour l'artiste"""
        text_lower = text.lower()
        
        rising_signals = ['montée', 'révélation', 'nouveau', 'buzz', 'percée', 'émergent']
        declining_signals = ['retour', 'comeback', 'ancien', 'légende', 'nostalgie']
        
        rising_score = sum(1 for s in rising_signals if s in text_lower)
        declining_score = sum(1 for s in declining_signals if s in text_lower)
        
        # Analyser les dates des events
        if events:
            recent_events = [e for e in events if e.date and e.date > datetime.now() - timedelta(days=365)]
            if len(recent_events) >= 3:
                rising_score += 2
        
        if rising_score > declining_score:
            return 'rising'
        elif declining_score > rising_score:
            return 'declining'
        return 'stable'
    
    def _find_aliases(self, text: str, main_name: str) -> List[str]:
        """Trouve les alias/noms alternatifs"""
        aliases = []
        
        patterns = [
            rf'{re.escape(main_name)}\s*(?:aka|alias|dit)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)',
            r'(?:aka|alias|dit)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            aliases.extend(matches)
        
        return list(set(aliases))
    
    def _extract_social_metrics(self, text: str) -> Dict[str, int]:
        """Extrait les métriques des réseaux sociaux"""
        metrics = {}
        
        patterns = {
            'instagram': r'(\d+(?:[,.\s]\d+)*)\s*(?:k|m)?\s*(?:followers?|abonnés?)\s*(?:sur|on)?\s*(?:instagram|insta)',
            'spotify': r'(\d+(?:[,.\s]\d+)*)\s*(?:k|m)?\s*(?:auditeurs?|listeners?)\s*(?:mensuels?|monthly)',
            'youtube': r'(\d+(?:[,.\s]\d+)*)\s*(?:k|m)?\s*(?:abonnés?|subscribers?)\s*(?:sur|on)?\s*(?:youtube)',
        }
        
        text_lower = text.lower()
        
        for platform, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                value_str = match.group(1)
                value = self._parse_number(value_str)
                
                # Vérifier le suffixe k/m
                context = text_lower[match.start():match.end()+10]
                if 'm' in context and 'million' not in context:
                    value *= 1000000
                elif 'k' in context:
                    value *= 1000
                
                metrics[platform] = int(value)
        
        return metrics
    
    def _parse_number(self, s: str) -> float:
        """Parse un nombre avec séparateurs"""
        clean = re.sub(r'[\s,]', '', s)
        clean = clean.replace('.', '')
        try:
            return float(clean)
        except ValueError:
            return 0
    
    def get_artist(self, name: str) -> Optional[ArtistProfile]:
        """Récupère un artiste du cache"""
        return self.artist_cache.get(name.lower())
    
    def compare_artists(self, names: List[str]) -> Dict[str, Any]:
        """Compare plusieurs artistes"""
        profiles = [self.artist_cache.get(n.lower()) for n in names]
        profiles = [p for p in profiles if p]
        
        if len(profiles) < 2:
            return {'error': 'Need at least 2 cached artists'}
        
        return {
            'artists': [p.name for p in profiles],
            'fee_comparison': {
                p.name: p.estimated_fee_range for p in profiles
            },
            'popularity_ranking': sorted(
                [(p.name, p.popularity_score) for p in profiles],
                key=lambda x: x[1],
                reverse=True
            ),
            'best_value': min(
                profiles,
                key=lambda p: p.estimated_fee_range[0] / max(1, p.popularity_score)
            ).name,
        }
