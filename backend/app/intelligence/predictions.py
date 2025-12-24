"""
AI Predictions Engine for opportunity scoring and analysis.
Uses machine learning patterns to predict opportunity success probability.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import math


@dataclass
class PredictionResult:
    """Result of an AI prediction analysis."""
    opportunity_id: str
    success_probability: float  # 0.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    predicted_outcome: str  # "won", "lost", "undetermined"
    key_factors: List[Dict[str, Any]]
    recommendations: List[str]
    risk_assessment: str  # "low", "medium", "high"
    estimated_decision_date: Optional[datetime]


class PredictionsEngine:
    """AI-powered predictions for opportunity analysis."""
    
    # Weight factors for prediction model
    WEIGHTS = {
        "score": 0.25,
        "budget_fit": 0.15,
        "deadline_timing": 0.15,
        "source_reliability": 0.10,
        "domain_match": 0.20,
        "competition_level": 0.15,
    }
    
    # Historical success rates by source type
    SOURCE_SUCCESS_RATES = {
        "boamp": 0.12,
        "marchespublics": 0.15,
        "api": 0.20,
        "rss": 0.18,
        "email": 0.25,
        "html": 0.16,
    }
    
    # Domain expertise weights (for the agency)
    DOMAIN_EXPERTISE = {
        "concert": 0.95,
        "festival": 0.90,
        "événementiel": 0.85,
        "musique": 0.90,
        "rap": 0.95,
        "hip-hop": 0.95,
        "urban": 0.90,
        "mode": 0.80,
        "fashion": 0.80,
        "streetwear": 0.85,
        "culture": 0.75,
        "sport": 0.60,
        "conférence": 0.50,
        "séminaire": 0.45,
    }
    
    def __init__(self):
        self.prediction_history: List[Dict[str, Any]] = []
    
    async def predict_opportunity(
        self,
        opportunity: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> PredictionResult:
        """
        Predict the success probability of an opportunity.
        
        Args:
            opportunity: The opportunity data to analyze
            historical_data: Optional historical opportunities for context
            
        Returns:
            PredictionResult with prediction details
        """
        factors = {}
        recommendations = []
        
        # 1. Score factor
        score = opportunity.get("score", 0)
        score_factor = min(score / 10, 1.0)
        factors["score"] = {
            "value": score,
            "weight": self.WEIGHTS["score"],
            "impact": score_factor * self.WEIGHTS["score"],
            "description": f"Score de {score}/10"
        }
        
        # 2. Budget fit analysis
        budget = opportunity.get("budget_amount", 0)
        budget_factor = self._analyze_budget_fit(budget)
        factors["budget_fit"] = {
            "value": budget,
            "weight": self.WEIGHTS["budget_fit"],
            "impact": budget_factor * self.WEIGHTS["budget_fit"],
            "description": self._get_budget_description(budget)
        }
        
        # 3. Deadline timing
        deadline = opportunity.get("deadline_at")
        deadline_factor = self._analyze_deadline(deadline)
        factors["deadline_timing"] = {
            "value": deadline,
            "weight": self.WEIGHTS["deadline_timing"],
            "impact": deadline_factor * self.WEIGHTS["deadline_timing"],
            "description": self._get_deadline_description(deadline)
        }
        
        # 4. Source reliability
        source_type = opportunity.get("source_type", "html")
        source_factor = self.SOURCE_SUCCESS_RATES.get(source_type, 0.15)
        factors["source_reliability"] = {
            "value": source_type,
            "weight": self.WEIGHTS["source_reliability"],
            "impact": source_factor * self.WEIGHTS["source_reliability"],
            "description": f"Source de type {source_type}"
        }
        
        # 5. Domain match
        title = opportunity.get("title", "").lower()
        description = opportunity.get("description", "").lower()
        domain_factor = self._analyze_domain_match(title, description)
        factors["domain_match"] = {
            "value": domain_factor,
            "weight": self.WEIGHTS["domain_match"],
            "impact": domain_factor * self.WEIGHTS["domain_match"],
            "description": "Correspondance avec l'expertise de l'agence"
        }
        
        # 6. Competition estimate
        competition_factor = self._estimate_competition(opportunity)
        factors["competition_level"] = {
            "value": 1 - competition_factor,
            "weight": self.WEIGHTS["competition_level"],
            "impact": (1 - competition_factor) * self.WEIGHTS["competition_level"],
            "description": self._get_competition_description(competition_factor)
        }
        
        # Calculate overall probability
        total_impact = sum(f["impact"] for f in factors.values())
        success_probability = min(max(total_impact, 0.05), 0.95)
        
        # Determine confidence level based on data completeness
        confidence = self._calculate_confidence(opportunity, factors)
        
        # Predicted outcome
        if success_probability >= 0.6:
            predicted_outcome = "won"
        elif success_probability <= 0.3:
            predicted_outcome = "lost"
        else:
            predicted_outcome = "undetermined"
        
        # Risk assessment
        risk = self._assess_risk(success_probability, confidence, factors)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(factors, opportunity)
        
        # Estimate decision date
        estimated_date = self._estimate_decision_date(opportunity)
        
        return PredictionResult(
            opportunity_id=str(opportunity.get("id", "")),
            success_probability=round(success_probability, 3),
            confidence_level=round(confidence, 3),
            predicted_outcome=predicted_outcome,
            key_factors=[
                {"name": k, **v} for k, v in sorted(
                    factors.items(), 
                    key=lambda x: x[1]["impact"], 
                    reverse=True
                )
            ],
            recommendations=recommendations,
            risk_assessment=risk,
            estimated_decision_date=estimated_date
        )
    
    async def batch_predict(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[PredictionResult]:
        """Predict success for multiple opportunities."""
        results = []
        for opp in opportunities:
            result = await self.predict_opportunity(opp)
            results.append(result)
        return results
    
    async def get_trend_analysis(
        self,
        opportunities: List[Dict[str, Any]],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze trends in opportunities over time."""
        now = datetime.now()
        period_start = now - timedelta(days=period_days)
        
        # Filter opportunities in period
        recent = [
            o for o in opportunities
            if o.get("created_at") and 
            datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")).replace(tzinfo=None) >= period_start
        ]
        
        if not recent:
            return {
                "period_days": period_days,
                "total_opportunities": 0,
                "trends": {},
                "predictions": {}
            }
        
        # Analyze by status
        status_counts = {}
        for o in recent:
            status = o.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Analyze by score
        scores = [o.get("score", 0) for o in recent]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Predict next period
        growth_rate = len(recent) / period_days
        predicted_next = int(growth_rate * period_days * 1.1)  # 10% growth assumption
        
        return {
            "period_days": period_days,
            "total_opportunities": len(recent),
            "by_status": status_counts,
            "average_score": round(avg_score, 2),
            "score_distribution": {
                "low": len([s for s in scores if s < 4]),
                "medium": len([s for s in scores if 4 <= s < 7]),
                "high": len([s for s in scores if s >= 7]),
            },
            "growth_rate": round(growth_rate, 2),
            "predicted_next_period": predicted_next,
            "recommendations": [
                "Focus sur les opportunités avec score > 7",
                "Augmenter la collecte sur sources les plus performantes",
            ]
        }
    
    def _analyze_budget_fit(self, budget: float) -> float:
        """Analyze if budget fits agency's typical range."""
        if not budget:
            return 0.5  # Unknown budget
        
        # Optimal budget range for the agency: 20k-150k
        if 20000 <= budget <= 150000:
            return 0.9
        elif 10000 <= budget < 20000 or 150000 < budget <= 300000:
            return 0.7
        elif 5000 <= budget < 10000 or 300000 < budget <= 500000:
            return 0.5
        elif budget < 5000:
            return 0.2
        else:
            return 0.4  # Very large budgets might be risky
    
    def _analyze_deadline(self, deadline: Optional[str]) -> float:
        """Analyze deadline timing."""
        if not deadline:
            return 0.5
        
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")).replace(tzinfo=None)
            days_until = (deadline_dt - datetime.now()).days
            
            if days_until < 3:
                return 0.2  # Too tight
            elif days_until < 7:
                return 0.5  # Tight but doable
            elif days_until <= 30:
                return 0.9  # Ideal
            elif days_until <= 60:
                return 0.8  # Good
            else:
                return 0.6  # Far ahead
        except:
            return 0.5
    
    def _analyze_domain_match(self, title: str, description: str) -> float:
        """Analyze how well opportunity matches agency expertise."""
        text = f"{title} {description}"
        
        max_match = 0.3  # Base match
        for domain, expertise in self.DOMAIN_EXPERTISE.items():
            if domain in text:
                max_match = max(max_match, expertise)
        
        return max_match
    
    def _estimate_competition(self, opportunity: Dict[str, Any]) -> float:
        """Estimate competition level (0 = no competition, 1 = high competition)."""
        budget = opportunity.get("budget_amount", 0)
        source_type = opportunity.get("source_type", "")
        
        # Public markets = more competition
        if source_type in ["boamp", "marchespublics"]:
            base_competition = 0.7
        else:
            base_competition = 0.4
        
        # Higher budgets = more competition
        if budget > 100000:
            base_competition += 0.15
        elif budget > 50000:
            base_competition += 0.1
        
        return min(base_competition, 0.95)
    
    def _calculate_confidence(
        self,
        opportunity: Dict[str, Any],
        factors: Dict[str, Any]
    ) -> float:
        """Calculate confidence level based on data completeness."""
        completeness = 0.0
        
        # Check data completeness
        if opportunity.get("budget_amount"):
            completeness += 0.2
        if opportunity.get("deadline_at"):
            completeness += 0.2
        if opportunity.get("description"):
            completeness += 0.2
        if opportunity.get("organization"):
            completeness += 0.15
        if opportunity.get("contact_email"):
            completeness += 0.15
        if opportunity.get("score"):
            completeness += 0.1
        
        return min(completeness, 1.0)
    
    def _assess_risk(
        self,
        probability: float,
        confidence: float,
        factors: Dict[str, Any]
    ) -> str:
        """Assess overall risk level."""
        if confidence < 0.5:
            return "high"  # Low confidence = high risk
        
        if probability >= 0.6 and confidence >= 0.7:
            return "low"
        elif probability >= 0.4 or confidence >= 0.6:
            return "medium"
        else:
            return "high"
    
    def _generate_recommendations(
        self,
        factors: Dict[str, Any],
        opportunity: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Score-based recommendations
        score_impact = factors["score"]["impact"]
        if score_impact < 0.15:
            recommendations.append("Améliorer le ciblage pour cette catégorie d'opportunités")
        
        # Deadline recommendations
        deadline_impact = factors["deadline_timing"]["impact"]
        if deadline_impact < 0.08:
            recommendations.append("Deadline serrée - prioriser cette opportunité")
        
        # Budget recommendations
        budget = opportunity.get("budget_amount", 0)
        if not budget:
            recommendations.append("Investiguer le budget pour mieux évaluer")
        elif budget > 200000:
            recommendations.append("Gros budget - prévoir une proposition détaillée")
        
        # Contact recommendations
        if not opportunity.get("contact_email"):
            recommendations.append("Rechercher les coordonnées du contact")
        
        # Domain recommendations
        domain_impact = factors["domain_match"]["impact"]
        if domain_impact >= 0.15:
            recommendations.append("Excellente correspondance avec l'expertise - fort potentiel")
        
        # Competition recommendations
        competition = factors["competition_level"]
        if competition["value"] < 0.4:
            recommendations.append("Forte concurrence attendue - soigner la différenciation")
        
        return recommendations[:5]  # Max 5 recommendations
    
    def _estimate_decision_date(
        self,
        opportunity: Dict[str, Any]
    ) -> Optional[datetime]:
        """Estimate when a decision might be made."""
        deadline = opportunity.get("deadline_at")
        if not deadline:
            return None
        
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")).replace(tzinfo=None)
            # Typical decision is 2-4 weeks after deadline
            return deadline_dt + timedelta(weeks=3)
        except:
            return None
    
    def _get_budget_description(self, budget: float) -> str:
        if not budget:
            return "Budget non spécifié"
        if budget < 10000:
            return f"Petit budget ({budget:,.0f}€)"
        elif budget < 50000:
            return f"Budget moyen ({budget:,.0f}€)"
        elif budget < 150000:
            return f"Budget important ({budget:,.0f}€)"
        else:
            return f"Gros budget ({budget:,.0f}€)"
    
    def _get_deadline_description(self, deadline: Optional[str]) -> str:
        if not deadline:
            return "Pas de deadline spécifiée"
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")).replace(tzinfo=None)
            days = (deadline_dt - datetime.now()).days
            if days < 0:
                return "Deadline passée"
            elif days == 0:
                return "Deadline aujourd'hui"
            elif days == 1:
                return "Deadline demain"
            elif days < 7:
                return f"Deadline dans {days} jours"
            elif days < 30:
                return f"Deadline dans {days // 7} semaine(s)"
            else:
                return f"Deadline dans {days // 30} mois"
        except:
            return "Date invalide"
    
    def _get_competition_description(self, competition: float) -> str:
        if competition < 0.3:
            return "Faible concurrence attendue"
        elif competition < 0.6:
            return "Concurrence modérée"
        else:
            return "Forte concurrence attendue"


# Singleton instance
predictions_engine = PredictionsEngine()
