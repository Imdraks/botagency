"""
🚀 Advanced Scoring Engine - Moteur de scoring survitaminé
Pour agences événementielles

Ce moteur analyse les opportunités sur plusieurs axes:
1. URGENCE - Deadline et timing
2. BUDGET - Estimation intelligente du budget
3. FIT MÉTIER - Correspondance avec les services de l'agence
4. QUALITÉ CLIENT - Type d'organisation, historique, secteur
5. POTENTIEL BUSINESS - Volume, récurrence, prestige
6. RISQUE - Pénalités pour signaux négatifs

Score final = 0-100 points
"""
import re
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION AGENCE - À personnaliser selon vos services
# =============================================================================

@dataclass
class AgencyConfig:
    """Configuration des services et préférences de votre agence"""
    
    # Services proposés par l'agence (pondération 1-5)
    services: Dict[str, int] = field(default_factory=lambda: {
        # Production événementielle
        "production_evenement": 5,
        "direction_artistique": 5,
        "scenographie": 5,
        "regie_technique": 5,
        "booking_artistes": 5,
        
        # Communication
        "communication": 4,
        "relations_presse": 4,
        "brand_content": 4,
        "activation_marque": 4,
        
        # Digital
        "digital": 3,
        "reseaux_sociaux": 3,
        "streaming": 3,
        
        # Autres
        "conseil_strategie": 3,
        "formation": 2,
    })
    
    # Secteurs d'activité privilégiés (pondération 1-5)
    preferred_sectors: Dict[str, int] = field(default_factory=lambda: {
        "musique": 5,
        "festival": 5,
        "culture": 5,
        "spectacle_vivant": 5,
        "luxe": 4,
        "mode": 4,
        "gastronomie": 4,
        "sport": 4,
        "corporate": 3,
        "institutionnel": 3,
        "tourisme": 3,
        "immobilier": 2,
        "tech": 3,
        "startup": 2,
    })
    
    # Budget minimum intéressant (EUR)
    min_budget_interest: int = 10_000
    
    # Budget idéal (sweet spot)
    ideal_budget_min: int = 50_000
    ideal_budget_max: int = 500_000
    
    # Mots-clés métier spécifiques (haute valeur)
    high_value_keywords: List[str] = field(default_factory=lambda: [
        "privatisation",
        "soirée privée",
        "lancement produit",
        "inauguration",
        "anniversaire entreprise",
        "convention",
        "séminaire",
        "team building",
        "cocktail",
        "gala",
        "remise de prix",
        "festival",
        "concert",
        "tournée",
        "showcase",
        "release party",
    ])


# Configuration globale (singleton modifiable)
AGENCY_CONFIG = AgencyConfig()


# =============================================================================
# TYPES ET STRUCTURES
# =============================================================================

class ScoreCategory(Enum):
    """Catégories de score"""
    URGENCY = "urgency"
    BUDGET = "budget"
    BUSINESS_FIT = "business_fit"
    CLIENT_QUALITY = "client_quality"
    POTENTIAL = "potential"
    RISK = "risk"


@dataclass
class ScoreBreakdown:
    """Détail du score par catégorie"""
    urgency: float = 0.0          # 0-20 points
    budget: float = 0.0           # 0-20 points
    business_fit: float = 0.0     # 0-25 points
    client_quality: float = 0.0   # 0-20 points
    potential: float = 0.0        # 0-15 points
    risk: float = 0.0             # -20 à 0 points (pénalités)
    
    total: float = 0.0            # 0-100 points
    confidence: float = 0.0       # 0-100% (fiabilité du score)
    
    details: Dict[str, Any] = field(default_factory=dict)
    signals: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# DICTIONNAIRES DE DÉTECTION
# =============================================================================

# Patterns pour détecter les budgets
BUDGET_PATTERNS = [
    # Montants explicites
    (r'budget[:\s]*(?:de\s+)?(\d[\d\s]*(?:\.\d+)?)\s*(?:k|K|000|€|EUR|euros?)', 1000),
    (r'budget[:\s]*(?:de\s+)?(\d[\d\s]*(?:\.\d+)?)\s*(?:M|millions?)', 1000000),
    (r'(\d[\d\s]*(?:\.\d+)?)\s*(?:k|K)\s*€', 1000),
    (r'(\d[\d\s]*)\s*000\s*€', 1000),
    (r'(\d[\d\s]*(?:\.\d+)?)\s*(?:millions?|M)\s*(?:d\')?(?:euros?|€)', 1000000),
    (r'(\d+(?:\s*\d+)*)\s*€', 1),
    
    # Fourchettes
    (r'entre\s+(\d+)\s*(?:et|à)\s*(\d+)\s*(?:k|K|000)', 1000),
    (r'de\s+(\d+)\s*(?:k|K)?\s*à\s*(\d+)\s*(?:k|K)', 1000),
    
    # Montants arrondis courants
    (r'(\d+)\s*(?:k€|k euros?|keur)', 1000),
]

# Indicateurs de budget implicite
BUDGET_INDICATORS = {
    "petit": (5_000, 20_000),
    "moyen": (20_000, 80_000),
    "important": (80_000, 200_000),
    "conséquent": (100_000, 300_000),
    "significatif": (50_000, 150_000),
    "gros": (150_000, 500_000),
    "majeur": (200_000, 1_000_000),
}

# Types d'organisations (avec score de qualité)
ORGANIZATION_SCORES = {
    # Institutions publiques (haute valeur, paiement sûr)
    "ministère": 18,
    "région": 17,
    "département": 16,
    "métropole": 16,
    "mairie": 15,
    "ville de": 15,
    "communauté d'agglomération": 14,
    "conseil": 14,
    "préfecture": 14,
    "ambassade": 15,
    
    # Grandes entreprises
    "groupe": 16,
    "holding": 15,
    "société anonyme": 14,
    "sa ": 13,
    "lvmh": 20,
    "kering": 20,
    "l'oréal": 19,
    "orange": 17,
    "bnp": 17,
    "axa": 17,
    "total": 17,
    "carrefour": 16,
    "accor": 17,
    
    # Culture / Spectacle (cœur de métier)
    "festival": 18,
    "théâtre": 15,
    "opéra": 17,
    "philharmonie": 18,
    "musée": 15,
    "centre culturel": 14,
    "maison de la culture": 14,
    "scène nationale": 16,
    "smac": 15,
    "zenith": 17,
    "olympia": 18,
    "accor arena": 19,
    
    # Fondations / Mécénat
    "fondation": 16,
    "mécénat": 15,
    
    # PME / ETI
    "sarl": 10,
    "sas ": 11,
    "eurl": 8,
    "auto-entrepreneur": 5,
    "association": 8,
}

# Secteurs d'activité détectés par mots-clés
SECTOR_KEYWORDS = {
    "musique": ["concert", "artiste", "musique", "live", "tour", "tournée", "album", "clip", "label", "producteur musical"],
    "festival": ["festival", "édition", "programmation", "festivalier", "pass", "camping"],
    "culture": ["culturel", "culture", "patrimoine", "exposition", "vernissage", "galerie", "art"],
    "spectacle_vivant": ["spectacle", "théâtre", "danse", "cirque", "opéra", "ballet", "comédie"],
    "luxe": ["luxe", "prestige", "premium", "haute", "exclusif", "vip", "privé"],
    "mode": ["mode", "fashion", "défilé", "collection", "créateur", "couture", "mannequin"],
    "gastronomie": ["gastronomie", "chef", "restaurant", "culinaire", "vin", "champagne", "traiteur"],
    "sport": ["sport", "match", "championnat", "athlète", "stade", "compétition", "jeux"],
    "corporate": ["corporate", "entreprise", "b2b", "business", "professionnel", "congrès"],
    "institutionnel": ["institutionnel", "public", "administration", "collectivité", "mairie"],
    "tourisme": ["tourisme", "hôtel", "destination", "voyage", "office de tourisme"],
    "tech": ["tech", "startup", "digital", "numérique", "innovation", "ia", "data"],
}

# Signaux négatifs (pénalités)
NEGATIVE_SIGNALS = {
    "promo_content": {
        "keywords": ["newsletter", "inscrivez-vous", "abonnez-vous", "suivez-nous", "cliquez ici", "offre spéciale"],
        "penalty": -8,
        "message": "Contenu promotionnel/newsletter détecté"
    },
    "very_low_budget": {
        "keywords": ["petit budget", "budget limité", "moyens limités", "bénévole", "gratuit"],
        "penalty": -10,
        "message": "Budget très limité signalé"
    },
    "spam_indicators": {
        "keywords": ["viagra", "bitcoin", "casino", "xxx", "cliquez vite"],
        "penalty": -50,
        "message": "Spam détecté"
    },
    "cancelled": {
        "keywords": ["annulé", "reporté", "suspendu", "fermé"],
        "penalty": -15,
        "message": "Événement annulé ou reporté"
    },
    "old_date": {
        "keywords": ["2023", "2022", "2021", "2020"],
        "penalty": -12,
        "message": "Référence à une date passée"
    },
    "job_offer": {
        "keywords": ["recrutement", "cdi", "cdd", "stage", "alternance", "poste à pourvoir", "nous recrutons"],
        "penalty": -20,
        "message": "Offre d'emploi (pas une opportunité business)"
    },
}

# Signaux positifs (bonus)
POSITIVE_SIGNALS = {
    "exclusive": {
        "keywords": ["exclusif", "unique", "exceptionnel", "première", "inédit"],
        "bonus": 5,
        "message": "Opportunité exclusive/unique"
    },
    "recurring": {
        "keywords": ["annuel", "édition", "récurrent", "chaque année", "depuis"],
        "bonus": 4,
        "message": "Événement récurrent (fidélisation possible)"
    },
    "growth": {
        "keywords": ["croissance", "développement", "expansion", "nouveau", "lancement"],
        "bonus": 3,
        "message": "Projet en croissance"
    },
    "high_visibility": {
        "keywords": ["médiatique", "presse", "tv", "radio", "influenceur", "celebrity", "star"],
        "bonus": 4,
        "message": "Forte visibilité médiatique"
    },
    "prestigious_venue": {
        "keywords": ["palais", "château", "palace", "grand hôtel", "5 étoiles", "lieu d'exception"],
        "bonus": 5,
        "message": "Lieu prestigieux"
    },
}


# =============================================================================
# MOTEUR DE SCORING AVANCÉ
# =============================================================================

class AdvancedScoringEngine:
    """
    Moteur de scoring avancé pour opportunités événementielles
    
    Score sur 100 points:
    - Urgence: 0-20 pts
    - Budget: 0-20 pts
    - Fit métier: 0-25 pts
    - Qualité client: 0-20 pts
    - Potentiel: 0-15 pts
    - Risques: -20 à 0 pts (pénalités)
    """
    
    def __init__(self, config: AgencyConfig = None):
        self.config = config or AGENCY_CONFIG
    
    def _get_text_content(self, opportunity) -> str:
        """Récupère tout le texte de l'opportunité"""
        parts = [
            getattr(opportunity, 'title', '') or '',
            getattr(opportunity, 'description', '') or '',
            getattr(opportunity, 'organization', '') or '',
            getattr(opportunity, 'snippet', '') or '',
            getattr(opportunity, 'raw_content', '') or '',
        ]
        return ' '.join(parts).lower()
    
    def _extract_budget(self, text: str) -> Tuple[Optional[int], Optional[int], str]:
        """
        Extrait le budget du texte
        Returns: (min_budget, max_budget, source)
        """
        text_lower = text.lower()
        
        # Chercher les patterns explicites
        for pattern, multiplier in BUDGET_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Fourchette
                        min_val = int(re.sub(r'\s', '', match[0])) * multiplier
                        max_val = int(re.sub(r'\s', '', match[1])) * multiplier
                        return min_val, max_val, "explicit_range"
                    else:
                        amount = int(re.sub(r'\s', '', match)) * multiplier
                        # Estimer une fourchette autour du montant
                        return int(amount * 0.8), int(amount * 1.2), "explicit"
                except (ValueError, IndexError):
                    continue
        
        # Chercher les indicateurs implicites
        for indicator, (min_val, max_val) in BUDGET_INDICATORS.items():
            if indicator in text_lower:
                return min_val, max_val, f"implicit:{indicator}"
        
        return None, None, "unknown"
    
    def _score_urgency(self, opportunity, now: datetime = None) -> Tuple[float, Dict]:
        """
        Score d'urgence basé sur la deadline
        
        - Deadline < 7j: 20 pts (URGENT!)
        - Deadline 7-14j: 15 pts
        - Deadline 14-30j: 10 pts
        - Deadline 30-60j: 5 pts
        - Deadline > 60j ou pas de deadline: 0 pts
        """
        now = now or datetime.utcnow()
        details = {}
        
        deadline = getattr(opportunity, 'deadline_at', None)
        if not deadline:
            return 0, {"status": "no_deadline", "days": None}
        
        if deadline < now:
            return 0, {"status": "expired", "days": -1}
        
        days = (deadline - now).days
        details["days"] = days
        
        if days < 7:
            score = 20
            details["status"] = "urgent"
            details["message"] = f"🔴 URGENT - {days} jours restants!"
        elif days < 14:
            score = 15
            details["status"] = "soon"
            details["message"] = f"🟠 Proche - {days} jours"
        elif days < 30:
            score = 10
            details["status"] = "normal"
            details["message"] = f"🟡 Normal - {days} jours"
        elif days < 60:
            score = 5
            details["status"] = "comfortable"
            details["message"] = f"🟢 Confortable - {days} jours"
        else:
            score = 2
            details["status"] = "distant"
            details["message"] = f"⚪ Lointain - {days} jours"
        
        return score, details
    
    def _score_budget(self, opportunity, text: str) -> Tuple[float, Dict]:
        """
        Score basé sur le budget
        
        - Budget idéal (50k-500k): 20 pts
        - Budget intéressant (20k-50k ou 500k-1M): 15 pts
        - Budget acceptable (10k-20k): 10 pts
        - Budget mentionné mais petit (<10k): 5 pts
        - Pas de budget détecté: 2 pts
        """
        details = {}
        
        # D'abord vérifier le champ budget si existe
        budget_amount = getattr(opportunity, 'budget_amount', None)
        if budget_amount:
            min_budget = int(budget_amount * 0.8)
            max_budget = int(budget_amount * 1.2)
            source = "field"
        else:
            min_budget, max_budget, source = self._extract_budget(text)
        
        details["min"] = min_budget
        details["max"] = max_budget
        details["source"] = source
        
        if min_budget is None:
            return 2, {**details, "status": "unknown", "message": "Budget non détecté"}
        
        avg_budget = (min_budget + max_budget) / 2
        details["average"] = avg_budget
        
        # Scoring basé sur le budget moyen
        if self.config.ideal_budget_min <= avg_budget <= self.config.ideal_budget_max:
            score = 20
            details["status"] = "ideal"
            details["message"] = f"💰 Budget idéal: {min_budget//1000}k-{max_budget//1000}k €"
        elif avg_budget >= self.config.ideal_budget_max:
            score = 18  # Très gros budget = légèrement moins car plus compétitif
            details["status"] = "large"
            details["message"] = f"💎 Gros budget: {min_budget//1000}k-{max_budget//1000}k €"
        elif avg_budget >= self.config.min_budget_interest:
            score = 12
            details["status"] = "interesting"
            details["message"] = f"💵 Budget intéressant: {min_budget//1000}k-{max_budget//1000}k €"
        elif avg_budget >= 5000:
            score = 6
            details["status"] = "small"
            details["message"] = f"💸 Petit budget: {min_budget//1000}k €"
        else:
            score = 2
            details["status"] = "tiny"
            details["message"] = f"⚠️ Budget très limité: {min_budget} €"
        
        return score, details
    
    def _score_business_fit(self, text: str) -> Tuple[float, Dict]:
        """
        Score de correspondance avec les services de l'agence
        
        Max 25 points:
        - Services cœur de métier matchés: jusqu'à 15 pts
        - Secteur privilégié: jusqu'à 10 pts
        """
        details = {"services_matched": [], "sectors_matched": [], "keywords_matched": []}
        score = 0
        
        # 1. Détecter les services demandés
        service_score = 0
        for service, weight in self.config.services.items():
            service_keywords = service.replace("_", " ").split()
            for kw in service_keywords:
                if len(kw) > 3 and kw in text:
                    service_score += weight
                    details["services_matched"].append(service)
                    break
        
        # Normaliser sur 15 points
        score += min(15, service_score * 1.5)
        details["service_score"] = min(15, service_score * 1.5)
        
        # 2. Détecter le secteur
        sector_score = 0
        for sector, keywords in SECTOR_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    sector_weight = self.config.preferred_sectors.get(sector, 2)
                    sector_score = max(sector_score, sector_weight * 2)
                    if sector not in details["sectors_matched"]:
                        details["sectors_matched"].append(sector)
        
        score += min(10, sector_score)
        details["sector_score"] = min(10, sector_score)
        
        # 3. Bonus mots-clés haute valeur
        for kw in self.config.high_value_keywords:
            if kw in text:
                details["keywords_matched"].append(kw)
        
        if details["keywords_matched"]:
            bonus = min(5, len(details["keywords_matched"]) * 1.5)
            score += bonus
            details["keyword_bonus"] = bonus
        
        details["total"] = min(25, score)
        return min(25, score), details
    
    def _score_client_quality(self, opportunity, text: str) -> Tuple[float, Dict]:
        """
        Score de qualité du client/organisation
        
        Max 20 points basé sur:
        - Type d'organisation
        - Prestige/réputation
        - Fiabilité de paiement
        """
        details = {"organization": None, "type": "unknown", "signals": []}
        
        org = getattr(opportunity, 'organization', '') or ''
        org_lower = org.lower()
        combined_text = (org + " " + text).lower()
        
        # Chercher le type d'organisation
        best_score = 0
        best_type = "unknown"
        
        for org_type, org_score in ORGANIZATION_SCORES.items():
            if org_type in combined_text:
                if org_score > best_score:
                    best_score = org_score
                    best_type = org_type
        
        details["organization"] = org
        details["type"] = best_type
        details["base_score"] = best_score
        
        # Score minimum si organisation présente
        if org and best_score == 0:
            best_score = 5
        
        # Bonus si contact présent
        if getattr(opportunity, 'contact_email', None) or getattr(opportunity, 'contact_phone', None):
            best_score += 2
            details["signals"].append("contact_present")
        
        return min(20, best_score), details
    
    def _score_potential(self, opportunity, text: str) -> Tuple[float, Dict]:
        """
        Score de potentiel business
        
        Max 15 points:
        - Récurrence/fidélisation possible
        - Visibilité/prestige
        - Développement potentiel
        """
        details = {"signals": []}
        score = 0
        
        # Signaux positifs
        for signal_name, signal_data in POSITIVE_SIGNALS.items():
            for kw in signal_data["keywords"]:
                if kw in text:
                    score += signal_data["bonus"]
                    details["signals"].append({
                        "type": signal_name,
                        "keyword": kw,
                        "bonus": signal_data["bonus"],
                        "message": signal_data["message"]
                    })
                    break  # Un seul bonus par catégorie
        
        # Bonus si URL présente (plus sérieux)
        if getattr(opportunity, 'url_primary', None):
            score += 2
            details["signals"].append({"type": "has_url", "bonus": 2})
        
        return min(15, score), details
    
    def _score_risks(self, text: str) -> Tuple[float, Dict]:
        """
        Score de risque (pénalités)
        
        De -20 à 0 points
        """
        details = {"penalties": []}
        total_penalty = 0
        
        for risk_name, risk_data in NEGATIVE_SIGNALS.items():
            for kw in risk_data["keywords"]:
                if kw in text:
                    total_penalty += risk_data["penalty"]
                    details["penalties"].append({
                        "type": risk_name,
                        "keyword": kw,
                        "penalty": risk_data["penalty"],
                        "message": risk_data["message"]
                    })
                    break  # Une seule pénalité par catégorie
        
        # Limiter les pénalités à -20
        return max(-20, total_penalty), details
    
    def _calculate_confidence(self, details: Dict) -> float:
        """
        Calcule le niveau de confiance du score (0-100%)
        
        Basé sur la quantité d'informations disponibles
        """
        confidence = 30  # Base
        
        # Deadline connue
        if details.get("urgency", {}).get("days") is not None:
            confidence += 15
        
        # Budget détecté
        if details.get("budget", {}).get("source") != "unknown":
            confidence += 20
        
        # Organisation identifiée
        if details.get("client_quality", {}).get("type") != "unknown":
            confidence += 15
        
        # Services/secteurs matchés
        if details.get("business_fit", {}).get("services_matched"):
            confidence += 10
        
        if details.get("business_fit", {}).get("sectors_matched"):
            confidence += 10
        
        return min(100, confidence)
    
    def _generate_recommendations(self, score: float, details: Dict) -> List[str]:
        """Génère des recommandations basées sur le score"""
        recommendations = []
        
        if score >= 70:
            recommendations.append("🎯 Opportunité prioritaire - Contacter rapidement!")
        elif score >= 50:
            recommendations.append("✅ Bonne opportunité - À traiter cette semaine")
        elif score >= 30:
            recommendations.append("📋 Opportunité moyenne - À évaluer si temps disponible")
        else:
            recommendations.append("⏸️ Opportunité secondaire - Basse priorité")
        
        # Recommandations spécifiques
        urgency = details.get("urgency", {})
        if urgency.get("status") == "urgent":
            recommendations.append("⚡ URGENT: Deadline très proche!")
        
        budget = details.get("budget", {})
        if budget.get("status") == "ideal":
            recommendations.append("💰 Budget dans la cible idéale de l'agence")
        elif budget.get("status") == "unknown":
            recommendations.append("❓ Qualifier le budget en priorité")
        
        client = details.get("client_quality", {})
        if client.get("type") in ["ministère", "région", "festival", "lvmh", "kering"]:
            recommendations.append("⭐ Client premium - Soigner la réponse")
        
        return recommendations
    
    def calculate(self, opportunity) -> ScoreBreakdown:
        """
        Calcule le score complet d'une opportunité
        
        Returns:
            ScoreBreakdown avec tous les détails
        """
        result = ScoreBreakdown()
        now = datetime.utcnow()
        
        # Récupérer le texte
        text = self._get_text_content(opportunity)
        
        # 1. Urgence (0-20)
        result.urgency, urgency_details = self._score_urgency(opportunity, now)
        result.details["urgency"] = urgency_details
        
        # 2. Budget (0-20)
        result.budget, budget_details = self._score_budget(opportunity, text)
        result.details["budget"] = budget_details
        
        # 3. Fit métier (0-25)
        result.business_fit, fit_details = self._score_business_fit(text)
        result.details["business_fit"] = fit_details
        
        # 4. Qualité client (0-20)
        result.client_quality, client_details = self._score_client_quality(opportunity, text)
        result.details["client_quality"] = client_details
        
        # 5. Potentiel (0-15)
        result.potential, potential_details = self._score_potential(opportunity, text)
        result.details["potential"] = potential_details
        
        # 6. Risques (-20 à 0)
        result.risk, risk_details = self._score_risks(text)
        result.details["risk"] = risk_details
        
        # Score total (0-100)
        raw_total = (
            result.urgency +
            result.budget +
            result.business_fit +
            result.client_quality +
            result.potential +
            result.risk
        )
        result.total = max(0, min(100, raw_total))
        
        # Confidence
        result.confidence = self._calculate_confidence(result.details)
        
        # Signaux
        for signal in potential_details.get("signals", []):
            if isinstance(signal, dict) and "message" in signal:
                result.signals.append(f"✅ {signal['message']}")
        
        for penalty in risk_details.get("penalties", []):
            result.warnings.append(f"⚠️ {penalty['message']}")
        
        # Recommandations
        result.recommendations = self._generate_recommendations(result.total, result.details)
        
        logger.info(
            f"Advanced score: {result.total:.0f}/100 "
            f"(U:{result.urgency:.0f} B:{result.budget:.0f} F:{result.business_fit:.0f} "
            f"C:{result.client_quality:.0f} P:{result.potential:.0f} R:{result.risk:.0f}) "
            f"Confidence: {result.confidence:.0f}%"
        )
        
        return result
    
    def score_opportunity(self, opportunity) -> Tuple[int, Dict[str, Any]]:
        """
        Interface compatible avec l'ancien scoring engine
        
        Returns:
            (score: int, breakdown: dict)
        """
        result = self.calculate(opportunity)
        
        breakdown = {
            "total": result.total,
            "confidence": result.confidence,
            "by_category": {
                "urgency": result.urgency,
                "budget": result.budget,
                "business_fit": result.business_fit,
                "client_quality": result.client_quality,
                "potential": result.potential,
                "risk": result.risk,
            },
            "details": result.details,
            "signals": result.signals,
            "warnings": result.warnings,
            "recommendations": result.recommendations,
        }
        
        return int(result.total), breakdown


# =============================================================================
# SINGLETON & HELPERS
# =============================================================================

# Instance globale
advanced_scorer = AdvancedScoringEngine()


def score_opportunity_advanced(opportunity) -> Tuple[int, Dict[str, Any]]:
    """Fonction helper pour scorer une opportunité"""
    return advanced_scorer.score_opportunity(opportunity)


def configure_agency(config: AgencyConfig):
    """Configure le scoring pour votre agence"""
    global advanced_scorer
    advanced_scorer = AdvancedScoringEngine(config)


def get_agency_config() -> AgencyConfig:
    """Récupère la configuration actuelle"""
    return advanced_scorer.config
