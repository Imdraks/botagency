"""
Scoring engine - Calculate opportunity scores
"""
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.opportunity import Opportunity, OpportunityCategory
from app.db.models.scoring import ScoringRule, RuleType
from app.core.config import settings


class ScoringEngine:
    """Calculate scores for opportunities"""
    
    # Default rules (used if no rules in DB)
    DEFAULT_RULES = [
        # Urgency
        {
            'type': RuleType.URGENCY,
            'condition': 'deadline_days',
            'value': 7,
            'operator': 'lt',
            'points': 6,
            'label': 'Deadline < 7 jours'
        },
        {
            'type': RuleType.URGENCY,
            'condition': 'deadline_days',
            'value': 14,
            'operator': 'lt',
            'points': 4,
            'label': 'Deadline < 14 jours'
        },
        {
            'type': RuleType.URGENCY,
            'condition': 'deadline_days',
            'value': 30,
            'operator': 'lt',
            'points': 2,
            'label': 'Deadline < 30 jours'
        },
        # Event fit - high
        {
            'type': RuleType.EVENT_FIT,
            'condition': 'keywords',
            'keywords': ['privatisation', 'lieu', 'production événement', 'scénographie', 'technique', 'régie'],
            'points': 3,
            'label': 'Fit événementiel fort'
        },
        {
            'type': RuleType.EVENT_FIT,
            'condition': 'keywords',
            'keywords': ['appel d\'offres', 'consultation', 'marché'],
            'points': 3,
            'label': 'Marché public/consultation'
        },
        {
            'type': RuleType.EVENT_FIT,
            'condition': 'keywords',
            'keywords': ['partenariat', 'sponsor', 'brand content'],
            'points': 2,
            'label': 'Partenariat/Sponsoring'
        },
        # Quality
        {
            'type': RuleType.QUALITY,
            'condition': 'has_field',
            'fields': ['url_primary'],
            'points': 2,
            'label': 'Lien principal présent'
        },
        {
            'type': RuleType.QUALITY,
            'condition': 'has_field',
            'fields': ['contact_email', 'contact_phone'],
            'points': 2,
            'label': 'Contact détecté'
        },
        # Value
        {
            'type': RuleType.VALUE,
            'condition': 'has_field',
            'fields': ['budget_amount'],
            'points': 2,
            'label': 'Budget mentionné'
        },
        {
            'type': RuleType.VALUE,
            'condition': 'organization_type',
            'keywords': ['ministère', 'région', 'département', 'mairie', 'ville de', 'métropole'],
            'points': 2,
            'label': 'Institution/Grande organisation'
        },
        # Penalties
        {
            'type': RuleType.PENALTY,
            'condition': 'missing_fields',
            'fields': ['deadline_at', 'url_primary'],
            'points': -4,
            'label': 'Pas de deadline ni de lien'
        },
        {
            'type': RuleType.PENALTY,
            'condition': 'keywords',
            'keywords': ['newsletter', 'inscrivez-vous', 'abonnez-vous', 'suivez-nous'],
            'points': -2,
            'label': 'Contenu promo/news'
        },
    ]
    
    def __init__(self, db: Session = None):
        self.db = db
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict]:
        """Load scoring rules from DB or use defaults"""
        if self.db:
            db_rules = self.db.query(ScoringRule).filter(
                ScoringRule.is_active == True
            ).order_by(ScoringRule.priority.desc()).all()
            
            if db_rules:
                return [
                    {
                        'type': rule.rule_type,
                        'condition': rule.condition_type,
                        'points': rule.points,
                        'label': rule.label,
                        **rule.condition_value
                    }
                    for rule in db_rules
                ]
        
        return self.DEFAULT_RULES
    
    def _get_text_content(self, opportunity: Opportunity) -> str:
        """Get combined text content for keyword matching"""
        parts = [
            opportunity.title or '',
            opportunity.description or '',
            opportunity.organization or '',
            opportunity.snippet or '',
        ]
        return ' '.join(parts).lower()
    
    def _check_deadline_condition(self, opportunity: Opportunity, 
                                  value: int, operator: str) -> bool:
        """Check deadline-based condition"""
        if not opportunity.deadline_at:
            return False
        
        now = datetime.utcnow()
        if opportunity.deadline_at < now:
            return False  # Past deadline
        
        days_remaining = (opportunity.deadline_at - now).days
        
        if operator == 'lt':
            return days_remaining < value
        elif operator == 'lte':
            return days_remaining <= value
        elif operator == 'gt':
            return days_remaining > value
        elif operator == 'gte':
            return days_remaining >= value
        elif operator == 'eq':
            return days_remaining == value
        
        return False
    
    def _check_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if any keyword matches"""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def _check_has_field(self, opportunity: Opportunity, fields: List[str]) -> bool:
        """Check if opportunity has any of the specified fields"""
        for field in fields:
            value = getattr(opportunity, field, None)
            if value is not None and value != '' and value != []:
                return True
        return False
    
    def _check_missing_fields(self, opportunity: Opportunity, fields: List[str]) -> bool:
        """Check if opportunity is missing ALL specified fields"""
        for field in fields:
            value = getattr(opportunity, field, None)
            if value is not None and value != '' and value != []:
                return False  # At least one field is present
        return True  # All fields are missing
    
    def _evaluate_rule(self, opportunity: Opportunity, rule: Dict) -> Tuple[bool, int, str]:
        """
        Evaluate a single rule against an opportunity.
        Returns (matched, points, label)
        """
        condition = rule.get('condition')
        points = rule.get('points', 0)
        label = rule.get('label', '')
        
        matched = False
        
        if condition == 'deadline_days':
            matched = self._check_deadline_condition(
                opportunity,
                rule.get('value', 0),
                rule.get('operator', 'lt')
            )
        
        elif condition == 'keywords':
            text = self._get_text_content(opportunity)
            matched = self._check_keywords(text, rule.get('keywords', []))
        
        elif condition == 'organization_type':
            org = opportunity.organization or ''
            matched = self._check_keywords(org, rule.get('keywords', []))
        
        elif condition == 'has_field':
            matched = self._check_has_field(opportunity, rule.get('fields', []))
        
        elif condition == 'missing_fields':
            matched = self._check_missing_fields(opportunity, rule.get('fields', []))
        
        elif condition == 'category':
            categories = rule.get('categories', [])
            if isinstance(categories, str):
                categories = [categories]
            matched = opportunity.category.value in categories or opportunity.category in categories
        
        elif condition == 'regex':
            pattern = rule.get('pattern', '')
            field = rule.get('field', 'description')
            text = getattr(opportunity, field, '') or ''
            try:
                matched = bool(re.search(pattern, text, re.IGNORECASE))
            except:
                matched = False
        
        return matched, points, label
    
    def calculate_score(self, opportunity: Opportunity) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate score for an opportunity.
        Returns (total_score, breakdown_dict)
        """
        total_score = 0
        breakdown = {
            'rules_applied': [],
            'by_type': {},
        }
        
        # Track which rule types have been applied to avoid double-counting
        urgency_applied = False
        
        for rule in self.rules:
            matched, points, label = self._evaluate_rule(opportunity, rule)
            
            if matched:
                rule_type = rule.get('type')
                
                # For urgency, only apply the highest matching rule
                if rule_type == RuleType.URGENCY:
                    if urgency_applied:
                        continue
                    urgency_applied = True
                
                total_score += points
                breakdown['rules_applied'].append({
                    'label': label,
                    'points': points,
                    'type': rule_type.value if hasattr(rule_type, 'value') else str(rule_type),
                })
                
                # Track by type
                type_key = rule_type.value if hasattr(rule_type, 'value') else str(rule_type)
                if type_key not in breakdown['by_type']:
                    breakdown['by_type'][type_key] = 0
                breakdown['by_type'][type_key] += points
        
        # Ensure score doesn't go negative
        total_score = max(0, total_score)
        breakdown['total'] = total_score
        
        return total_score, breakdown
    
    def score_opportunity(self, opportunity: Opportunity) -> Opportunity:
        """Calculate and set score on opportunity"""
        score, breakdown = self.calculate_score(opportunity)
        opportunity.score = score
        opportunity.score_breakdown = breakdown
        return opportunity
    
    def rescore_all(self, opportunities: List[Opportunity]) -> int:
        """Rescore all provided opportunities. Returns count of updated."""
        count = 0
        for opp in opportunities:
            old_score = opp.score
            self.score_opportunity(opp)
            if opp.score != old_score:
                count += 1
        return count
