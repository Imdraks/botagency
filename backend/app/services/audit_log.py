"""
Système d'audit log - Historique de toutes les actions
Traçabilité complète des modifications sur les opportunités
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Session, relationship

from app.db.base import Base

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Types d'actions auditées"""
    # Opportunités
    OPPORTUNITY_CREATED = "opportunity.created"
    OPPORTUNITY_UPDATED = "opportunity.updated"
    OPPORTUNITY_STATUS_CHANGED = "opportunity.status_changed"
    OPPORTUNITY_ASSIGNED = "opportunity.assigned"
    OPPORTUNITY_SCORED = "opportunity.scored"
    OPPORTUNITY_DELETED = "opportunity.deleted"
    
    # Notes
    NOTE_ADDED = "note.added"
    NOTE_UPDATED = "note.updated"
    NOTE_DELETED = "note.deleted"
    
    # Tâches
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_UPDATED = "task.updated"
    
    # Sources
    SOURCE_CREATED = "source.created"
    SOURCE_UPDATED = "source.updated"
    SOURCE_DELETED = "source.deleted"
    
    # Ingestion
    INGESTION_STARTED = "ingestion.started"
    INGESTION_COMPLETED = "ingestion.completed"
    INGESTION_FAILED = "ingestion.failed"
    
    # Export
    EXPORT_GENERATED = "export.generated"
    REPORT_SENT = "report.sent"
    
    # Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"


class AuditLog(Base):
    """Table d'audit log"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Qui
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)  # Dénormalisé pour historique
    
    # Quoi
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # opportunity, source, user, etc.
    entity_id = Column(String(255), nullable=True, index=True)
    
    # Détails
    description = Column(Text, nullable=True)
    old_value = Column(JSON, nullable=True)  # État avant modification
    new_value = Column(JSON, nullable=True)  # État après modification
    metadata = Column(JSON, nullable=True)   # Données additionnelles
    
    # Quand
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # IP / User Agent pour sécurité
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Index composites pour requêtes fréquentes
    __table_args__ = (
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_date_action', 'created_at', 'action'),
    )


class AuditService:
    """Service de gestion des audit logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        description: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Enregistre une action dans l'audit log"""
        
        log_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action.value,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            description=description,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        logger.debug(f"Audit: {action.value} on {entity_type}/{entity_id} by user {user_id}")
        
        return log_entry
    
    def log_opportunity_status_change(
        self,
        opportunity_id: int,
        old_status: str,
        new_status: str,
        user_id: int,
        user_email: str,
        reason: Optional[str] = None
    ):
        """Log spécifique pour changement de status"""
        return self.log(
            action=AuditAction.OPPORTUNITY_STATUS_CHANGED,
            entity_type="opportunity",
            entity_id=opportunity_id,
            user_id=user_id,
            user_email=user_email,
            description=f"Status changé de {old_status} à {new_status}",
            old_value={"status": old_status},
            new_value={"status": new_status},
            metadata={"reason": reason} if reason else None
        )
    
    def log_opportunity_update(
        self,
        opportunity_id: int,
        changes: Dict[str, Any],
        user_id: int,
        user_email: str
    ):
        """Log pour modification d'opportunité"""
        return self.log(
            action=AuditAction.OPPORTUNITY_UPDATED,
            entity_type="opportunity",
            entity_id=opportunity_id,
            user_id=user_id,
            user_email=user_email,
            description=f"Champs modifiés: {', '.join(changes.keys())}",
            new_value=changes
        )
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Récupère l'historique d'une entité"""
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == str(entity_id)
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_user_activity(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """Récupère l'activité d'un utilisateur"""
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_recent_activity(
        self,
        hours: int = 24,
        actions: Optional[List[AuditAction]] = None,
        limit: int = 200
    ) -> List[AuditLog]:
        """Récupère l'activité récente"""
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.created_at >= since
        )
        
        if actions:
            query = query.filter(
                AuditLog.action.in_([a.value for a in actions])
            )
        
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_status_changes_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Statistiques des changements de status"""
        from sqlalchemy import func
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Nombre de changements par status
        changes = self.db.query(
            AuditLog.new_value['status'].astext,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.action == AuditAction.OPPORTUNITY_STATUS_CHANGED.value,
            AuditLog.created_at >= since
        ).group_by(AuditLog.new_value['status'].astext).all()
        
        # Utilisateurs les plus actifs
        top_users = self.db.query(
            AuditLog.user_email,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.created_at >= since,
            AuditLog.user_email.isnot(None)
        ).group_by(AuditLog.user_email).order_by(
            func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        return {
            "status_changes": {status: count for status, count in changes},
            "top_users": [{"email": email, "actions": count} for email, count in top_users],
            "period_days": days
        }


def audit_log_to_dict(log: AuditLog) -> Dict[str, Any]:
    """Convertit un AuditLog en dictionnaire"""
    return {
        "id": log.id,
        "user_id": log.user_id,
        "user_email": log.user_email,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "description": log.description,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "metadata": log.metadata,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "ip_address": log.ip_address
    }
