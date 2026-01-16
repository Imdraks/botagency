"""
Système d'alertes intelligentes
- Alertes deadline (J-7, J-3, J-1)
- Alertes personnalisées par utilisateur
- Alertes haute opportunité
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models.opportunity import Opportunity, OpportunityStatus
from app.db.models.user import User
from app.workers.notifications import send_discord_notification, send_slack_notification
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types d'alertes"""
    DEADLINE_URGENT = "deadline_urgent"      # J-1
    DEADLINE_SOON = "deadline_soon"          # J-3
    DEADLINE_COMING = "deadline_coming"      # J-7
    HIGH_SCORE = "high_score"                # Score >= 15
    NEW_OPPORTUNITY = "new_opportunity"      # Nouvelle opportunité
    STALE_OPPORTUNITY = "stale_opportunity"  # Opportunité stagnante
    BUDGET_MATCH = "budget_match"            # Budget correspondant


class AlertPriority(str, Enum):
    """Priorité des alertes"""
    CRITICAL = "critical"   # Action immédiate requise
    HIGH = "high"           # Attention dans la journée
    MEDIUM = "medium"       # À traiter cette semaine
    LOW = "low"             # Informatif


@dataclass
class Alert:
    """Représentation d'une alerte"""
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    opportunity_id: Optional[int] = None
    opportunity_title: Optional[str] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "opportunity_id": self.opportunity_id,
            "opportunity_title": self.opportunity_title,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass 
class UserAlertPreferences:
    """Préférences d'alertes d'un utilisateur"""
    user_id: int
    email: str
    
    # Filtres
    min_score: int = 0                    # Score minimum pour alertes
    categories: List[str] = None          # Catégories à suivre
    min_budget: float = None              # Budget minimum
    max_budget: float = None              # Budget maximum
    regions: List[str] = None             # Régions à suivre
    keywords: List[str] = None            # Mots-clés à surveiller
    
    # Canaux
    email_enabled: bool = True
    discord_enabled: bool = True
    slack_enabled: bool = True
    
    # Fréquence deadlines
    deadline_days: List[int] = None       # [1, 3, 7] par défaut
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.regions is None:
            self.regions = []
        if self.keywords is None:
            self.keywords = []
        if self.deadline_days is None:
            self.deadline_days = [1, 3, 7]


class SmartAlertService:
    """Service d'alertes intelligentes"""
    
    # Configuration par défaut des alertes deadline
    DEADLINE_THRESHOLDS = [
        (1, AlertType.DEADLINE_URGENT, AlertPriority.CRITICAL, "🚨 URGENT"),
        (3, AlertType.DEADLINE_SOON, AlertPriority.HIGH, "⚠️ Bientôt"),
        (7, AlertType.DEADLINE_COMING, AlertPriority.MEDIUM, "📅 À venir"),
    ]
    
    # Seuil de score élevé
    HIGH_SCORE_THRESHOLD = 15
    
    # Jours sans activité = opportunité stagnante
    STALE_DAYS = 14
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_deadline_alerts(self) -> List[Alert]:
        """Vérifie les deadlines et génère des alertes"""
        alerts = []
        now = datetime.utcnow()
        
        for days, alert_type, priority, prefix in self.DEADLINE_THRESHOLDS:
            target_date = now + timedelta(days=days)
            
            # Opportunités avec deadline dans X jours (±12h pour éviter les doublons)
            opportunities = self.db.query(Opportunity).filter(
                and_(
                    Opportunity.deadline_at >= target_date - timedelta(hours=12),
                    Opportunity.deadline_at < target_date + timedelta(hours=12),
                    Opportunity.status.notin_([
                        OpportunityStatus.WON,
                        OpportunityStatus.LOST,
                        OpportunityStatus.ARCHIVED
                    ])
                )
            ).all()
            
            for opp in opportunities:
                alert = Alert(
                    type=alert_type,
                    priority=priority,
                    title=f"{prefix}: {opp.title[:60]}",
                    message=f"Deadline dans {days} jour{'s' if days > 1 else ''} ({opp.deadline_at.strftime('%d/%m/%Y')})",
                    opportunity_id=opp.id,
                    opportunity_title=opp.title,
                    metadata={
                        "deadline": opp.deadline_at.isoformat(),
                        "days_remaining": days,
                        "status": opp.status.value,
                        "score": opp.score
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def check_high_score_alerts(self, since_hours: int = 24) -> List[Alert]:
        """Alerte pour les nouvelles opportunités à score élevé"""
        alerts = []
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
        high_score_opps = self.db.query(Opportunity).filter(
            and_(
                Opportunity.created_at >= since,
                Opportunity.score >= self.HIGH_SCORE_THRESHOLD
            )
        ).all()
        
        for opp in high_score_opps:
            alert = Alert(
                type=AlertType.HIGH_SCORE,
                priority=AlertPriority.HIGH,
                title=f"🌟 Haute opportunité: {opp.title[:50]}",
                message=f"Score {opp.score}/20 - {opp.organization or 'Organisation inconnue'}",
                opportunity_id=opp.id,
                opportunity_title=opp.title,
                metadata={
                    "score": opp.score,
                    "budget": float(opp.budget_amount) if opp.budget_amount else None,
                    "category": opp.category.value,
                    "organization": opp.organization
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def check_stale_opportunities(self) -> List[Alert]:
        """Alerte pour les opportunités sans mise à jour depuis longtemps"""
        alerts = []
        stale_date = datetime.utcnow() - timedelta(days=self.STALE_DAYS)
        
        stale_opps = self.db.query(Opportunity).filter(
            and_(
                Opportunity.updated_at < stale_date,
                Opportunity.status.in_([
                    OpportunityStatus.REVIEW,
                    OpportunityStatus.QUALIFIED,
                    OpportunityStatus.IN_PROGRESS
                ])
            )
        ).limit(20).all()
        
        for opp in stale_opps:
            days_stale = (datetime.utcnow() - opp.updated_at).days
            alert = Alert(
                type=AlertType.STALE_OPPORTUNITY,
                priority=AlertPriority.MEDIUM,
                title=f"💤 Opportunité stagnante: {opp.title[:50]}",
                message=f"Aucune mise à jour depuis {days_stale} jours",
                opportunity_id=opp.id,
                opportunity_title=opp.title,
                metadata={
                    "days_stale": days_stale,
                    "last_update": opp.updated_at.isoformat(),
                    "status": opp.status.value
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def check_user_alerts(
        self,
        preferences: UserAlertPreferences,
        since_hours: int = 24
    ) -> List[Alert]:
        """Vérifie les alertes personnalisées pour un utilisateur"""
        alerts = []
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
        # Base query: nouvelles opportunités
        query = self.db.query(Opportunity).filter(
            Opportunity.created_at >= since
        )
        
        # Filtre score minimum
        if preferences.min_score > 0:
            query = query.filter(Opportunity.score >= preferences.min_score)
        
        # Filtre budget
        if preferences.min_budget:
            query = query.filter(Opportunity.budget_amount >= preferences.min_budget)
        if preferences.max_budget:
            query = query.filter(Opportunity.budget_amount <= preferences.max_budget)
        
        # Filtre régions
        if preferences.regions:
            region_filters = [
                Opportunity.location_region.ilike(f"%{r}%") 
                for r in preferences.regions
            ]
            query = query.filter(or_(*region_filters))
        
        opportunities = query.all()
        
        # Filtre mots-clés (post-query pour flexibilité)
        if preferences.keywords:
            filtered_opps = []
            for opp in opportunities:
                text = f"{opp.title} {opp.description or ''} {opp.organization or ''}".lower()
                if any(kw.lower() in text for kw in preferences.keywords):
                    filtered_opps.append(opp)
            opportunities = filtered_opps
        
        # Créer les alertes
        for opp in opportunities:
            alert = Alert(
                type=AlertType.NEW_OPPORTUNITY,
                priority=AlertPriority.MEDIUM if opp.score < 15 else AlertPriority.HIGH,
                title=f"📌 Nouvelle opportunité: {opp.title[:50]}",
                message=f"Score {opp.score}/20 • {opp.category.value}",
                opportunity_id=opp.id,
                opportunity_title=opp.title,
                metadata={
                    "score": opp.score,
                    "category": opp.category.value,
                    "matched_by": "user_preferences"
                }
            )
            alerts.append(alert)
        
        return alerts
    
    def run_all_checks(self) -> Dict[str, List[Alert]]:
        """Exécute toutes les vérifications d'alertes"""
        return {
            "deadlines": self.check_deadline_alerts(),
            "high_score": self.check_high_score_alerts(),
            "stale": self.check_stale_opportunities()
        }
    
    def send_alerts(self, alerts: List[Alert]) -> Dict[str, int]:
        """Envoie les alertes via les canaux configurés"""
        sent_counts = {"discord": 0, "slack": 0}
        
        if not alerts:
            return sent_counts
        
        # Grouper par priorité pour Discord/Slack
        critical = [a for a in alerts if a.priority == AlertPriority.CRITICAL]
        high = [a for a in alerts if a.priority == AlertPriority.HIGH]
        
        # Envoyer les alertes critiques immédiatement
        if critical:
            self._send_to_discord(critical, "🚨 ALERTES CRITIQUES")
            self._send_to_slack(critical, "🚨 Alertes Critiques")
            sent_counts["discord"] += len(critical)
            sent_counts["slack"] += len(critical)
        
        # Envoyer les alertes haute priorité
        if high:
            self._send_to_discord(high, "⚠️ ALERTES IMPORTANTES")
            self._send_to_slack(high, "⚠️ Alertes Importantes")
            sent_counts["discord"] += len(high)
            sent_counts["slack"] += len(high)
        
        return sent_counts
    
    def _send_to_discord(self, alerts: List[Alert], title: str):
        """Envoie vers Discord webhook"""
        if not settings.discord_webhook_url:
            return
        
        import httpx
        
        embeds = []
        for alert in alerts[:10]:  # Max 10 embeds
            color = {
                AlertPriority.CRITICAL: 0xef4444,
                AlertPriority.HIGH: 0xf59e0b,
                AlertPriority.MEDIUM: 0x6366f1,
                AlertPriority.LOW: 0x6b7280
            }.get(alert.priority, 0x6b7280)
            
            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": color,
                "footer": {"text": f"Type: {alert.type.value}"},
                "timestamp": alert.created_at.isoformat()
            }
            
            if alert.opportunity_id:
                embed["url"] = f"{settings.frontend_url}/opportunities/{alert.opportunity_id}"
            
            embeds.append(embed)
        
        try:
            httpx.post(
                settings.discord_webhook_url,
                json={"username": "Radar Alerts", "embeds": embeds},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Discord alert error: {e}")
    
    def _send_to_slack(self, alerts: List[Alert], title: str):
        """Envoie vers Slack webhook"""
        if not settings.slack_webhook_url:
            return
        
        import httpx
        
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": title}}
        ]
        
        for alert in alerts[:15]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert.title}*\n{alert.message}"
                }
            })
            
            if alert.opportunity_id:
                blocks.append({
                    "type": "actions",
                    "elements": [{
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Voir l'opportunité"},
                        "url": f"{settings.frontend_url}/opportunities/{alert.opportunity_id}"
                    }]
                })
        
        try:
            httpx.post(
                settings.slack_webhook_url,
                json={"blocks": blocks},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Slack alert error: {e}")


# Fonction utilitaire pour les tasks Celery
def run_alert_checks(db: Session) -> Dict[str, Any]:
    """Exécute les vérifications d'alertes (pour Celery)"""
    service = SmartAlertService(db)
    all_alerts = service.run_all_checks()
    
    # Compter
    total = sum(len(alerts) for alerts in all_alerts.values())
    
    # Envoyer les alertes critiques et hautes
    important_alerts = []
    for alerts in all_alerts.values():
        important_alerts.extend([
            a for a in alerts 
            if a.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]
        ])
    
    sent = service.send_alerts(important_alerts)
    
    return {
        "total_alerts": total,
        "by_type": {k: len(v) for k, v in all_alerts.items()},
        "sent": sent,
        "alerts": [a.to_dict() for a in important_alerts[:20]]
    }
