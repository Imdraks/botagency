"""
Celery tasks pour les fonctionnalités avancées
- Rapport hebdomadaire automatique
- Vérification des alertes
- Nettoyage des logs
"""
from datetime import datetime, timedelta
import logging

from celery import shared_task
from celery.schedules import crontab

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    """Get database session"""
    return SessionLocal()


@celery_app.task(bind=True)
def send_weekly_report_task(self):
    """
    Envoie le rapport hebdomadaire aux admins.
    Planifié pour lundi matin à 8h.
    """
    from app.services.weekly_report_service import WeeklyReportService
    
    logger.info("Starting weekly report generation...")
    db = get_db()
    
    try:
        service = WeeklyReportService(db)
        result = service.generate_and_send()
        
        logger.info(f"Weekly report sent to {len(result.get('recipients', []))} recipients")
        return {
            "status": "success",
            "recipients": result.get("recipients"),
            "stats": result.get("stats")
        }
        
    except Exception as e:
        logger.error(f"Error sending weekly report: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True)
def check_and_send_alerts_task(self):
    """
    Vérifie et envoie les alertes importantes.
    Planifié toutes les heures.
    """
    from app.services.smart_alerts import run_alert_checks
    
    logger.info("Checking alerts...")
    db = get_db()
    
    try:
        result = run_alert_checks(db)
        
        logger.info(
            f"Alert check complete: {result['total_alerts']} alerts, "
            f"sent: {result['sent']}"
        )
        return result
        
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True)
def check_deadline_alerts_task(self):
    """
    Vérifie spécifiquement les alertes deadline.
    Planifié chaque matin à 7h.
    """
    from app.services.smart_alerts import SmartAlertService, AlertPriority
    
    logger.info("Checking deadline alerts...")
    db = get_db()
    
    try:
        service = SmartAlertService(db)
        alerts = service.check_deadline_alerts()
        
        # Filtrer les alertes urgentes (J-1, J-3)
        urgent = [a for a in alerts if a.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]]
        
        if urgent:
            service.send_alerts(urgent)
            logger.info(f"Sent {len(urgent)} urgent deadline alerts")
        
        return {
            "total_deadline_alerts": len(alerts),
            "urgent_sent": len(urgent)
        }
        
    except Exception as e:
        logger.error(f"Error checking deadline alerts: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_old_audit_logs_task(self, days_to_keep: int = 90):
    """
    Nettoie les vieux logs d'audit.
    Garde les X derniers jours.
    """
    from sqlalchemy import delete
    from app.services.audit_log import AuditLog
    
    logger.info(f"Cleaning audit logs older than {days_to_keep} days...")
    db = get_db()
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = db.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        db.commit()
        
        deleted = result.rowcount
        logger.info(f"Deleted {deleted} old audit log entries")
        
        return {"deleted": deleted, "cutoff_date": cutoff.isoformat()}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning audit logs: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True)
def refresh_ml_patterns_task(self):
    """
    Rafraîchit le cache des patterns ML.
    Planifié toutes les 6 heures.
    """
    from app.scoring.ml_scoring import MLScoringEngine
    
    logger.info("Refreshing ML patterns cache...")
    db = get_db()
    
    try:
        engine = MLScoringEngine(db)
        # Force le rafraîchissement
        engine._cache_timestamp = None
        engine._refresh_patterns_if_needed()
        
        summary = engine.get_patterns_summary()
        logger.info(f"ML patterns refreshed: {summary['total_patterns']} patterns")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error refreshing ML patterns: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True)
def check_stale_opportunities_task(self):
    """
    Vérifie les opportunités stagnantes et envoie des alertes.
    Planifié chaque jour à 10h.
    """
    from app.services.smart_alerts import SmartAlertService
    
    logger.info("Checking stale opportunities...")
    db = get_db()
    
    try:
        service = SmartAlertService(db)
        alerts = service.check_stale_opportunities()
        
        if alerts:
            service.send_alerts(alerts)
            logger.info(f"Sent {len(alerts)} stale opportunity alerts")
        
        return {
            "stale_opportunities": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error checking stale opportunities: {e}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


# ============================================================================
# CONFIGURATION DES SCHEDULES CELERY BEAT
# ============================================================================
# À ajouter dans celery_app.py ou dans la config

CELERY_BEAT_SCHEDULE_ADVANCED = {
    # Rapport hebdomadaire - Lundi 8h00
    'weekly-report-monday-8am': {
        'task': 'app.workers.advanced_tasks.send_weekly_report_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
    
    # Vérification des alertes - Toutes les heures
    'check-alerts-hourly': {
        'task': 'app.workers.advanced_tasks.check_and_send_alerts_task',
        'schedule': crontab(minute=0),  # Chaque heure pile
    },
    
    # Alertes deadline - Chaque matin 7h00
    'deadline-alerts-daily-7am': {
        'task': 'app.workers.advanced_tasks.check_deadline_alerts_task',
        'schedule': crontab(hour=7, minute=0),
    },
    
    # Opportunités stagnantes - Chaque jour 10h00
    'stale-check-daily-10am': {
        'task': 'app.workers.advanced_tasks.check_stale_opportunities_task',
        'schedule': crontab(hour=10, minute=0),
    },
    
    # Refresh ML patterns - Toutes les 6 heures
    'ml-patterns-refresh': {
        'task': 'app.workers.advanced_tasks.refresh_ml_patterns_task',
        'schedule': crontab(hour='*/6', minute=30),
    },
    
    # Nettoyage audit logs - Dimanche 3h00
    'cleanup-audit-logs-weekly': {
        'task': 'app.workers.advanced_tasks.cleanup_old_audit_logs_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'kwargs': {'days_to_keep': 90}
    },
}
