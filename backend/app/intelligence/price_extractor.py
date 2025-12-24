"""
Price Extractor - Extraction intelligente des prix et conditions tarifaires
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PriceType(str, Enum):
    CACHET = "cachet"  # Cachet artiste
    BUDGET = "budget"  # Budget total
    LOCATION = "location"  # Location de lieu
    PRESTATION = "prestation"  # Prestation événementielle
    SPONSORING = "sponsoring"  # Partenariat / sponsoring
    UNKNOWN = "unknown"


@dataclass
class ExtractedPrice:
    value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    currency: str
    price_type: PriceType
    context: str  # Texte autour du prix
    confidence: float  # Score de confiance 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'currency': self.currency,
            'type': self.price_type.value,
            'context': self.context,
            'confidence': self.confidence,
        }


class PriceExtractor:
    """
    Extracteur intelligent de prix qui :
    - Détecte différents formats de prix (€, euros, K€, etc.)
    - Identifie le type de prix (cachet, budget, location, etc.)
    - Extrait les fourchettes de prix
    - Évalue la confiance de l'extraction
    """
    
    def __init__(self):
        # Patterns de prix
        self.price_patterns = [
            # Prix simple: "10 000 €"
            (r'(\d{1,3}(?:[\s\u00a0.,]?\d{3})*)\s*(?:€|euros?|EUR)', 'simple'),
            # Prix en K: "50K€" ou "50 k euros"
            (r'(\d+(?:[.,]\d+)?)\s*[kK]\s*(?:€|euros?|EUR)?', 'kilo'),
            # Prix en M: "1.5M€"
            (r'(\d+(?:[.,]\d+)?)\s*[mM]\s*(?:€|euros?|EUR)?', 'million'),
            # Fourchette: "entre 5000 et 10000€"
            (r'entre\s+(\d{1,3}(?:[\s\u00a0.,]?\d{3})*)\s*(?:et|à|-)\s*(\d{1,3}(?:[\s\u00a0.,]?\d{3})*)\s*(?:€|euros?)', 'range'),
            # À partir de: "à partir de 5000€"
            (r'(?:à partir de|from|depuis|dès)\s+(\d{1,3}(?:[\s\u00a0.,]?\d{3})*)\s*(?:€|euros?)', 'from'),
            # Jusqu'à: "jusqu'à 50000€"
            (r"(?:jusqu'à|up to|max(?:imum)?)\s+(\d{1,3}(?:[\s\u00a0.,]?\d{3})*)\s*(?:€|euros?)", 'upto'),
        ]
        
        # Mots-clés pour identifier le type de prix
        self.type_keywords = {
            PriceType.CACHET: [
                'cachet', 'artiste', 'performer', 'musicien', 'groupe', 'band',
                'dj', 'rappeur', 'chanteur', 'booking', 'prestation artistique'
            ],
            PriceType.BUDGET: [
                'budget', 'enveloppe', 'montant', 'marché', 'appel d\'offres',
                'consultation', 'estimation', 'coût total', 'investissement'
            ],
            PriceType.LOCATION: [
                'location', 'privatisation', 'lieu', 'salle', 'espace',
                'louer', 'réservation', 'tarif journée', 'tarif soirée'
            ],
            PriceType.PRESTATION: [
                'prestation', 'service', 'technique', 'régie', 'son', 'lumière',
                'scénographie', 'décor', 'traiteur', 'restauration'
            ],
            PriceType.SPONSORING: [
                'sponsoring', 'sponsor', 'partenariat', 'partenaire', 'naming',
                'visibilité', 'contrepartie', 'pack'
            ],
        }
    
    def extract_prices(self, text: str) -> List[ExtractedPrice]:
        """
        Extrait tous les prix d'un texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            Liste de prix extraits avec leur contexte
        """
        prices = []
        
        for pattern, pattern_type in self.price_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Extraire le contexte (50 caractères avant et après)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # Parser la valeur
                price = self._parse_match(match, pattern_type)
                if price is None:
                    continue
                
                # Déterminer le type de prix
                price_type = self._determine_price_type(context)
                
                # Calculer la confiance
                confidence = self._calculate_confidence(context, price, price_type)
                
                extracted = ExtractedPrice(
                    value=price.get('value'),
                    min_value=price.get('min'),
                    max_value=price.get('max'),
                    currency='EUR',
                    price_type=price_type,
                    context=context.strip(),
                    confidence=confidence,
                )
                
                prices.append(extracted)
        
        # Dédupliquer et trier par confiance
        prices = self._deduplicate(prices)
        prices.sort(key=lambda p: p.confidence, reverse=True)
        
        return prices
    
    def _parse_match(self, match: re.Match, pattern_type: str) -> Optional[Dict[str, float]]:
        """Parse une correspondance regex en valeur numérique"""
        try:
            if pattern_type == 'simple':
                value = self._parse_number(match.group(1))
                return {'value': value}
            
            elif pattern_type == 'kilo':
                value = self._parse_number(match.group(1)) * 1000
                return {'value': value}
            
            elif pattern_type == 'million':
                value = self._parse_number(match.group(1)) * 1000000
                return {'value': value}
            
            elif pattern_type == 'range':
                min_val = self._parse_number(match.group(1))
                max_val = self._parse_number(match.group(2))
                return {'min': min_val, 'max': max_val, 'value': (min_val + max_val) / 2}
            
            elif pattern_type == 'from':
                min_val = self._parse_number(match.group(1))
                return {'min': min_val, 'value': min_val}
            
            elif pattern_type == 'upto':
                max_val = self._parse_number(match.group(1))
                return {'max': max_val, 'value': max_val}
            
        except (ValueError, IndexError):
            return None
        
        return None
    
    def _parse_number(self, text: str) -> float:
        """Parse une chaîne en nombre"""
        # Nettoyer les espaces et séparateurs
        cleaned = re.sub(r'[\s\u00a0]', '', text)
        # Remplacer la virgule par un point
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    
    def _determine_price_type(self, context: str) -> PriceType:
        """Détermine le type de prix basé sur le contexte"""
        context_lower = context.lower()
        
        for price_type, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    return price_type
        
        return PriceType.UNKNOWN
    
    def _calculate_confidence(
        self, 
        context: str, 
        price: Dict[str, float],
        price_type: PriceType
    ) -> float:
        """Calcule un score de confiance pour l'extraction"""
        confidence = 0.5  # Base
        
        context_lower = context.lower()
        
        # Bonus si le type est identifié
        if price_type != PriceType.UNKNOWN:
            confidence += 0.2
        
        # Bonus si c'est une fourchette (plus précis)
        if price.get('min') and price.get('max'):
            confidence += 0.1
        
        # Bonus pour certains mots-clés de certitude
        certainty_keywords = ['tarif', 'prix', 'coût', 'budget', 'cachet', 'montant']
        for kw in certainty_keywords:
            if kw in context_lower:
                confidence += 0.05
        
        # Malus pour incertitude
        uncertainty_keywords = ['environ', 'approximativement', 'estimé', 'peut-être']
        for kw in uncertainty_keywords:
            if kw in context_lower:
                confidence -= 0.1
        
        # Valeur raisonnable? (entre 100€ et 10M€)
        value = price.get('value', 0)
        if value and 100 <= value <= 10000000:
            confidence += 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _deduplicate(self, prices: List[ExtractedPrice]) -> List[ExtractedPrice]:
        """Supprime les prix en double"""
        seen = set()
        unique = []
        
        for price in prices:
            key = (price.value, price.min_value, price.max_value, price.price_type)
            if key not in seen:
                seen.add(key)
                unique.append(price)
        
        return unique
    
    def get_best_price(self, prices: List[ExtractedPrice], price_type: PriceType = None) -> Optional[ExtractedPrice]:
        """Retourne le prix le plus pertinent"""
        if not prices:
            return None
        
        filtered = prices
        if price_type:
            filtered = [p for p in prices if p.price_type == price_type]
        
        if not filtered:
            filtered = prices
        
        # Retourner celui avec la plus haute confiance
        return max(filtered, key=lambda p: p.confidence)
    
    def extract_artist_fee(self, text: str) -> Optional[ExtractedPrice]:
        """Extrait spécifiquement le cachet d'un artiste"""
        prices = self.extract_prices(text)
        return self.get_best_price(prices, PriceType.CACHET)
    
    def extract_budget(self, text: str) -> Optional[ExtractedPrice]:
        """Extrait spécifiquement le budget total"""
        prices = self.extract_prices(text)
        return self.get_best_price(prices, PriceType.BUDGET)
