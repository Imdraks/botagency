"""
Scoring Machine Learning - Apprentissage basé sur l'historique WON/LOST
Analyse les patterns des opportunités gagnées pour prédire le succès
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import math
import re

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models.opportunity import Opportunity, OpportunityStatus, OpportunityCategory

logger = logging.getLogger(__name__)


@dataclass
class HistoricalPattern:
    """Pattern identifié dans l'historique"""
    name: str
    description: str
    win_rate: float  # 0-1
    sample_size: int
    confidence: float  # 0-1 basé sur sample size
    impact_score: float  # -20 à +20


@dataclass
class MLScoringResult:
    """Résultat du scoring ML"""
    opportunity_id: int
    base_score: float
    ml_adjustment: float
    final_score: float
    confidence: float
    patterns_matched: List[HistoricalPattern]
    similar_won: List[Dict[str, Any]]
    similar_lost: List[Dict[str, Any]]
    recommendations: List[str]
    win_probability: float


class MLScoringEngine:
    """Moteur de scoring basé sur l'apprentissage historique"""
    
    # Poids minimum pour qu'un pattern soit significatif
    MIN_SAMPLE_SIZE = 5
    MIN_CONFIDENCE = 0.3
    
    def __init__(self, db: Session):
        self.db = db
        self._patterns_cache: Dict[str, HistoricalPattern] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=1)
    
    def _refresh_patterns_if_needed(self):
        """Rafraîchit le cache des patterns si nécessaire"""
        now = datetime.utcnow()
        if self._cache_timestamp and (now - self._cache_timestamp) < self._cache_ttl:
            return
        
        self._patterns_cache = self._compute_patterns()
        self._cache_timestamp = now
    
    def _compute_patterns(self) -> Dict[str, HistoricalPattern]:
        """Calcule les patterns à partir de l'historique"""
        patterns = {}
        
        # Récupérer les opportunités gagnées et perdues
        won = self.db.query(Opportunity).filter(
            Opportunity.status == OpportunityStatus.WON
        ).all()
        
        lost = self.db.query(Opportunity).filter(
            Opportunity.status == OpportunityStatus.LOST
        ).all()
        
        total = len(won) + len(lost)
        if total < self.MIN_SAMPLE_SIZE:
            logger.warning(f"Pas assez de données historiques ({total} opportunités)")
            return patterns
        
        overall_win_rate = len(won) / total if total > 0 else 0.5
        
        # Pattern 1: Par catégorie
        patterns.update(self._analyze_by_category(won, lost, overall_win_rate))
        
        # Pattern 2: Par tranche de budget
        patterns.update(self._analyze_by_budget(won, lost, overall_win_rate))
        
        # Pattern 3: Par source
        patterns.update(self._analyze_by_source(won, lost, overall_win_rate))
        
        # Pattern 4: Par tranche de score initial
        patterns.update(self._analyze_by_score_range(won, lost, overall_win_rate))
        
        # Pattern 5: Par organisation (keywords)
        patterns.update(self._analyze_by_organization_keywords(won, lost, overall_win_rate))
        
        # Pattern 6: Par région
        patterns.update(self._analyze_by_region(won, lost, overall_win_rate))
        
        # Pattern 7: Par mois de deadline
        patterns.update(self._analyze_by_deadline_month(won, lost, overall_win_rate))
        
        logger.info(f"Calculé {len(patterns)} patterns ML à partir de {total} opportunités")
        return patterns
    
    def _calculate_confidence(self, sample_size: int) -> float:
        """Calcule le niveau de confiance basé sur la taille de l'échantillon"""
        # Fonction logarithmique: plus d'échantillons = plus de confiance
        if sample_size < self.MIN_SAMPLE_SIZE:
            return 0.0
        return min(1.0, math.log(sample_size / self.MIN_SAMPLE_SIZE + 1) / math.log(20))
    
    def _calculate_impact(self, win_rate: float, overall_win_rate: float, confidence: float) -> float:
        """Calcule l'impact du pattern sur le score (-20 à +20)"""
        # Différence par rapport à la moyenne, pondérée par la confiance
        diff = win_rate - overall_win_rate
        return diff * 40 * confidence  # Échelle de -20 à +20
    
    def _analyze_by_category(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse les win rates par catégorie"""
        patterns = {}
        
        # Compter par catégorie
        won_by_cat = defaultdict(int)
        lost_by_cat = defaultdict(int)
        
        for opp in won:
            won_by_cat[opp.category.value] += 1
        for opp in lost:
            lost_by_cat[opp.category.value] += 1
        
        all_cats = set(won_by_cat.keys()) | set(lost_by_cat.keys())
        
        for cat in all_cats:
            w = won_by_cat[cat]
            l = lost_by_cat[cat]
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[f"category_{cat}"] = HistoricalPattern(
                    name=f"Catégorie {cat}",
                    description=f"Taux de succès pour la catégorie {cat}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_budget(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse les win rates par tranche de budget"""
        patterns = {}
        
        # Tranches de budget
        ranges = [
            ("budget_0_10k", 0, 10000),
            ("budget_10k_50k", 10000, 50000),
            ("budget_50k_100k", 50000, 100000),
            ("budget_100k_500k", 100000, 500000),
            ("budget_500k_plus", 500000, float('inf')),
        ]
        
        for name, min_b, max_b in ranges:
            w = sum(1 for o in won if o.budget_amount and min_b <= float(o.budget_amount) < max_b)
            l = sum(1 for o in lost if o.budget_amount and min_b <= float(o.budget_amount) < max_b)
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                budget_label = f"{min_b/1000:.0f}k-{max_b/1000:.0f}k€" if max_b != float('inf') else f"{min_b/1000:.0f}k+€"
                patterns[name] = HistoricalPattern(
                    name=f"Budget {budget_label}",
                    description=f"Taux de succès pour les budgets {budget_label}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_source(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse les win rates par source"""
        patterns = {}
        
        won_by_source = defaultdict(int)
        lost_by_source = defaultdict(int)
        
        for opp in won:
            won_by_source[opp.source_name] += 1
        for opp in lost:
            lost_by_source[opp.source_name] += 1
        
        all_sources = set(won_by_source.keys()) | set(lost_by_source.keys())
        
        for source in all_sources:
            w = won_by_source[source]
            l = lost_by_source[source]
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[f"source_{source}"] = HistoricalPattern(
                    name=f"Source {source}",
                    description=f"Taux de succès pour la source {source}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_score_range(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse les win rates par tranche de score"""
        patterns = {}
        
        ranges = [
            ("score_0_5", 0, 5),
            ("score_5_10", 5, 10),
            ("score_10_15", 10, 15),
            ("score_15_20", 15, 20),
        ]
        
        for name, min_s, max_s in ranges:
            w = sum(1 for o in won if o.score and min_s <= o.score < max_s)
            l = sum(1 for o in lost if o.score and min_s <= o.score < max_s)
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[name] = HistoricalPattern(
                    name=f"Score initial {min_s}-{max_s}",
                    description=f"Taux de succès pour les scores initiaux {min_s}-{max_s}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_organization_keywords(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse par mots-clés dans l'organisation"""
        patterns = {}
        
        # Mots-clés indicatifs
        keywords = [
            ("org_mairie", ["mairie", "commune", "ville de"]),
            ("org_departement", ["département", "conseil départemental"]),
            ("org_region", ["région", "conseil régional"]),
            ("org_festival", ["festival", "fest"]),
            ("org_association", ["association", "asso"]),
            ("org_entreprise", ["sarl", "sas", "sa", "eurl", "groupe"]),
        ]
        
        for pattern_name, kws in keywords:
            def matches(org: str, keywords: List[str]) -> bool:
                if not org:
                    return False
                org_lower = org.lower()
                return any(kw in org_lower for kw in keywords)
            
            w = sum(1 for o in won if matches(o.organization, kws))
            l = sum(1 for o in lost if matches(o.organization, kws))
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[pattern_name] = HistoricalPattern(
                    name=f"Organisation: {kws[0]}",
                    description=f"Taux de succès pour les organisations type {kws[0]}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_region(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse par région"""
        patterns = {}
        
        won_by_region = defaultdict(int)
        lost_by_region = defaultdict(int)
        
        for opp in won:
            if opp.location_region:
                won_by_region[opp.location_region] += 1
        for opp in lost:
            if opp.location_region:
                lost_by_region[opp.location_region] += 1
        
        all_regions = set(won_by_region.keys()) | set(lost_by_region.keys())
        
        for region in all_regions:
            w = won_by_region[region]
            l = lost_by_region[region]
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[f"region_{region.lower().replace(' ', '_')}"] = HistoricalPattern(
                    name=f"Région {region}",
                    description=f"Taux de succès pour la région {region}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _analyze_by_deadline_month(
        self,
        won: List[Opportunity],
        lost: List[Opportunity],
        overall_win_rate: float
    ) -> Dict[str, HistoricalPattern]:
        """Analyse par mois de deadline"""
        patterns = {}
        
        won_by_month = defaultdict(int)
        lost_by_month = defaultdict(int)
        
        for opp in won:
            if opp.deadline_at:
                won_by_month[opp.deadline_at.month] += 1
        for opp in lost:
            if opp.deadline_at:
                lost_by_month[opp.deadline_at.month] += 1
        
        month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", 
                       "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        
        for month in range(1, 13):
            w = won_by_month[month]
            l = lost_by_month[month]
            total = w + l
            
            if total >= self.MIN_SAMPLE_SIZE:
                win_rate = w / total
                confidence = self._calculate_confidence(total)
                impact = self._calculate_impact(win_rate, overall_win_rate, confidence)
                
                patterns[f"deadline_month_{month}"] = HistoricalPattern(
                    name=f"Deadline en {month_names[month-1]}",
                    description=f"Taux de succès pour les deadlines en {month_names[month-1]}",
                    win_rate=win_rate,
                    sample_size=total,
                    confidence=confidence,
                    impact_score=impact
                )
        
        return patterns
    
    def _find_similar_opportunities(
        self,
        opportunity: Opportunity,
        status: OpportunityStatus,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Trouve des opportunités similaires dans l'historique"""
        similar = []
        
        query = self.db.query(Opportunity).filter(
            Opportunity.status == status,
            Opportunity.id != opportunity.id
        )
        
        # Filtrer par catégorie si possible
        if opportunity.category:
            query = query.filter(Opportunity.category == opportunity.category)
        
        # Filtrer par source si possible
        if opportunity.source_name:
            query = query.filter(Opportunity.source_name == opportunity.source_name)
        
        results = query.order_by(Opportunity.created_at.desc()).limit(limit * 2).all()
        
        # Calculer la similarité et trier
        scored = []
        for opp in results:
            score = self._calculate_similarity(opportunity, opp)
            scored.append((score, opp))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        for score, opp in scored[:limit]:
            similar.append({
                "id": opp.id,
                "title": opp.title[:60],
                "organization": opp.organization,
                "budget": float(opp.budget_amount) if opp.budget_amount else None,
                "score": opp.score,
                "similarity": round(score * 100, 1)
            })
        
        return similar
    
    def _calculate_similarity(self, opp1: Opportunity, opp2: Opportunity) -> float:
        """Calcule un score de similarité entre deux opportunités"""
        similarity = 0.0
        factors = 0
        
        # Catégorie
        if opp1.category == opp2.category:
            similarity += 1.0
        factors += 1
        
        # Source
        if opp1.source_name == opp2.source_name:
            similarity += 1.0
        factors += 1
        
        # Région
        if opp1.location_region and opp2.location_region:
            if opp1.location_region.lower() == opp2.location_region.lower():
                similarity += 1.0
            factors += 1
        
        # Budget (proche à 50%)
        if opp1.budget_amount and opp2.budget_amount:
            b1, b2 = float(opp1.budget_amount), float(opp2.budget_amount)
            ratio = min(b1, b2) / max(b1, b2) if max(b1, b2) > 0 else 0
            if ratio > 0.5:
                similarity += ratio
            factors += 1
        
        # Score (proche)
        if opp1.score and opp2.score:
            diff = abs(opp1.score - opp2.score)
            if diff <= 3:
                similarity += 1 - (diff / 10)
            factors += 1
        
        return similarity / factors if factors > 0 else 0
    
    def score_opportunity(self, opportunity_id: int) -> Optional[MLScoringResult]:
        """Score une opportunité avec le ML"""
        self._refresh_patterns_if_needed()
        
        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            return None
        
        base_score = opportunity.score or 0
        patterns_matched = []
        total_adjustment = 0.0
        total_confidence = 0.0
        
        # Vérifier chaque pattern
        for pattern_key, pattern in self._patterns_cache.items():
            if self._opportunity_matches_pattern(opportunity, pattern_key):
                patterns_matched.append(pattern)
                total_adjustment += pattern.impact_score * pattern.confidence
                total_confidence += pattern.confidence
        
        # Normaliser l'ajustement
        if patterns_matched:
            avg_confidence = total_confidence / len(patterns_matched)
            # Limiter l'ajustement à ±10 points
            ml_adjustment = max(-10, min(10, total_adjustment / len(patterns_matched)))
        else:
            avg_confidence = 0.0
            ml_adjustment = 0.0
        
        final_score = max(0, min(20, base_score + ml_adjustment))
        
        # Calculer la probabilité de victoire
        matched_win_rates = [p.win_rate for p in patterns_matched if p.confidence >= self.MIN_CONFIDENCE]
        if matched_win_rates:
            win_probability = sum(matched_win_rates) / len(matched_win_rates)
        else:
            # Utiliser le score comme proxy
            win_probability = final_score / 20
        
        # Trouver des opportunités similaires
        similar_won = self._find_similar_opportunities(opportunity, OpportunityStatus.WON)
        similar_lost = self._find_similar_opportunities(opportunity, OpportunityStatus.LOST)
        
        # Générer des recommandations
        recommendations = self._generate_recommendations(
            opportunity, patterns_matched, win_probability
        )
        
        return MLScoringResult(
            opportunity_id=opportunity_id,
            base_score=base_score,
            ml_adjustment=round(ml_adjustment, 2),
            final_score=round(final_score, 1),
            confidence=round(avg_confidence, 2),
            patterns_matched=patterns_matched,
            similar_won=similar_won,
            similar_lost=similar_lost,
            recommendations=recommendations,
            win_probability=round(win_probability, 3)
        )
    
    def _opportunity_matches_pattern(self, opp: Opportunity, pattern_key: str) -> bool:
        """Vérifie si une opportunité correspond à un pattern"""
        
        # Catégorie
        if pattern_key.startswith("category_"):
            cat = pattern_key.replace("category_", "")
            return opp.category and opp.category.value == cat
        
        # Budget
        if pattern_key.startswith("budget_"):
            if not opp.budget_amount:
                return False
            budget = float(opp.budget_amount)
            ranges = {
                "budget_0_10k": (0, 10000),
                "budget_10k_50k": (10000, 50000),
                "budget_50k_100k": (50000, 100000),
                "budget_100k_500k": (100000, 500000),
                "budget_500k_plus": (500000, float('inf')),
            }
            if pattern_key in ranges:
                min_b, max_b = ranges[pattern_key]
                return min_b <= budget < max_b
        
        # Source
        if pattern_key.startswith("source_"):
            source = pattern_key.replace("source_", "")
            return opp.source_name == source
        
        # Score
        if pattern_key.startswith("score_"):
            if not opp.score:
                return False
            ranges = {
                "score_0_5": (0, 5),
                "score_5_10": (5, 10),
                "score_10_15": (10, 15),
                "score_15_20": (15, 20),
            }
            if pattern_key in ranges:
                min_s, max_s = ranges[pattern_key]
                return min_s <= opp.score < max_s
        
        # Organisation
        if pattern_key.startswith("org_"):
            if not opp.organization:
                return False
            org_lower = opp.organization.lower()
            keywords_map = {
                "org_mairie": ["mairie", "commune", "ville de"],
                "org_departement": ["département", "conseil départemental"],
                "org_region": ["région", "conseil régional"],
                "org_festival": ["festival", "fest"],
                "org_association": ["association", "asso"],
                "org_entreprise": ["sarl", "sas", "sa", "eurl", "groupe"],
            }
            if pattern_key in keywords_map:
                return any(kw in org_lower for kw in keywords_map[pattern_key])
        
        # Région
        if pattern_key.startswith("region_"):
            region = pattern_key.replace("region_", "").replace("_", " ")
            return opp.location_region and opp.location_region.lower() == region
        
        # Mois deadline
        if pattern_key.startswith("deadline_month_"):
            if not opp.deadline_at:
                return False
            month = int(pattern_key.replace("deadline_month_", ""))
            return opp.deadline_at.month == month
        
        return False
    
    def _generate_recommendations(
        self,
        opportunity: Opportunity,
        patterns: List[HistoricalPattern],
        win_probability: float
    ) -> List[str]:
        """Génère des recommandations basées sur l'analyse"""
        recommendations = []
        
        # Patterns négatifs
        negative_patterns = [p for p in patterns if p.impact_score < -2]
        positive_patterns = [p for p in patterns if p.impact_score > 2]
        
        if negative_patterns:
            worst = min(negative_patterns, key=lambda p: p.impact_score)
            recommendations.append(
                f"⚠️ Attention: {worst.name} a un taux de succès historique bas ({worst.win_rate*100:.0f}%)"
            )
        
        if positive_patterns:
            best = max(positive_patterns, key=lambda p: p.impact_score)
            recommendations.append(
                f"✅ Point fort: {best.name} a un bon taux de succès ({best.win_rate*100:.0f}%)"
            )
        
        # Probabilité de victoire
        if win_probability >= 0.7:
            recommendations.append("🎯 Forte probabilité de succès - Priorité haute")
        elif win_probability >= 0.5:
            recommendations.append("📊 Probabilité moyenne - À qualifier")
        elif win_probability >= 0.3:
            recommendations.append("⚡ Probabilité faible - Analyser les risques")
        else:
            recommendations.append("❌ Probabilité très faible - Reconsidérer")
        
        # Recommandations spécifiques
        if not opportunity.budget_amount:
            recommendations.append("💰 Budget non renseigné - À clarifier avec le client")
        
        if not opportunity.deadline_at:
            recommendations.append("📅 Pas de deadline - Vérifier les délais")
        
        return recommendations
    
    def get_patterns_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des patterns appris"""
        self._refresh_patterns_if_needed()
        
        return {
            "total_patterns": len(self._patterns_cache),
            "patterns": {
                k: {
                    "name": v.name,
                    "win_rate": round(v.win_rate * 100, 1),
                    "sample_size": v.sample_size,
                    "confidence": round(v.confidence * 100, 1),
                    "impact": round(v.impact_score, 2)
                }
                for k, v in sorted(
                    self._patterns_cache.items(),
                    key=lambda x: abs(x[1].impact_score),
                    reverse=True
                )[:20]
            },
            "cache_age_minutes": (
                (datetime.utcnow() - self._cache_timestamp).total_seconds() / 60
                if self._cache_timestamp else None
            )
        }
