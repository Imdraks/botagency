"""
Agency Automations - Celery tasks for automatic relances and deadline alerts
"""
import logging
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.agency import (
    Deal, Project, Deliverable, AgencyTask,
    DealStatus, ProjectStatus, DeliverableStatus, TaskStatus, TaskPriority
)

logger = logging.getLogger(__name__)


# ============================================================================
# AUTO RELANCE - Deals
# ============================================================================

@shared_task(name="app.workers.agency_automations.auto_followup_deals")
def auto_followup_deals():
    """
    Create automatic followup tasks for deals that need attention.
    
    Rules:
    - Deal.status = QUOTE_SENT and last_contact_at > 3 days → Create followup task
    - Deal.status = CONTACTED and last_contact_at > 5 days → Create followup task
    - Deal.next_action_date is past → Create reminder task
    
    Runs daily at 08:00
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tasks_created = 0
        
        # ====================================================================
        # 1. Quote sent > 3 days without response
        # ====================================================================
        three_days_ago = now - timedelta(days=3)
        
        quote_sent_deals = db.query(Deal).filter(
            Deal.status == DealStatus.QUOTE_SENT,
            Deal.last_contact_at < three_days_ago,
        ).all()
        
        for deal in quote_sent_deals:
            # Check if task already exists for today
            existing = db.query(AgencyTask).filter(
                AgencyTask.deal_id == deal.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "followup_quote",
                AgencyTask.status != TaskStatus.DONE,
            ).first()
            
            if not existing:
                days_waiting = (now - deal.last_contact_at).days if deal.last_contact_at else 0
                task = AgencyTask(
                    workspace_id=deal.workspace_id,
                    deal_id=deal.id,
                    title=f"🔔 Relancer devis: {deal.title}",
                    description=f"Devis envoyé il y a {days_waiting} jours sans réponse.\n"
                               f"Client: {deal.client.name if deal.client else 'N/A'}\n"
                               f"Valeur: {deal.value or 'N/A'}€",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    due_date=now,
                    is_auto_generated=True,
                    auto_type="followup_quote",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created followup task for deal {deal.id}: {deal.title}")
        
        # ====================================================================
        # 2. Contacted > 5 days without progress
        # ====================================================================
        five_days_ago = now - timedelta(days=5)
        
        contacted_deals = db.query(Deal).filter(
            Deal.status == DealStatus.CONTACTED,
            Deal.last_contact_at < five_days_ago,
        ).all()
        
        for deal in contacted_deals:
            existing = db.query(AgencyTask).filter(
                AgencyTask.deal_id == deal.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "followup_contact",
                AgencyTask.status != TaskStatus.DONE,
            ).first()
            
            if not existing:
                days_waiting = (now - deal.last_contact_at).days if deal.last_contact_at else 0
                task = AgencyTask(
                    workspace_id=deal.workspace_id,
                    deal_id=deal.id,
                    title=f"📞 Relancer contact: {deal.title}",
                    description=f"Contacté il y a {days_waiting} jours sans avancée.\n"
                               f"Client: {deal.client.name if deal.client else 'N/A'}",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                    due_date=now,
                    is_auto_generated=True,
                    auto_type="followup_contact",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created contact followup task for deal {deal.id}")
        
        # ====================================================================
        # 3. Next action date is past
        # ====================================================================
        overdue_deals = db.query(Deal).filter(
            Deal.next_action_date < now,
            Deal.status.notin_([DealStatus.WON, DealStatus.LOST]),
        ).all()
        
        for deal in overdue_deals:
            existing = db.query(AgencyTask).filter(
                AgencyTask.deal_id == deal.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "action_overdue",
                AgencyTask.status != TaskStatus.DONE,
            ).first()
            
            if not existing:
                days_overdue = (now - deal.next_action_date).days if deal.next_action_date else 0
                task = AgencyTask(
                    workspace_id=deal.workspace_id,
                    deal_id=deal.id,
                    title=f"⚠️ Action en retard: {deal.title}",
                    description=f"Action prévue il y a {days_overdue} jour(s).\n"
                               f"Client: {deal.client.name if deal.client else 'N/A'}",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    due_date=now,
                    is_auto_generated=True,
                    auto_type="action_overdue",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created action overdue task for deal {deal.id}")
        
        db.commit()
        logger.info(f"Auto followup deals: created {tasks_created} tasks")
        return {"tasks_created": tasks_created}
        
    except Exception as e:
        logger.error(f"Error in auto_followup_deals: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# DEADLINE ALERTS
# ============================================================================

@shared_task(name="app.workers.agency_automations.deadline_alerts")
def deadline_alerts():
    """
    Create alert tasks for upcoming deadlines.
    
    Rules:
    - Project deadline < 72h and status != DELIVERED/ARCHIVED → Create alert
    - Deliverable due_date < 72h and status not APPROVED/DELIVERED → Create alert
    
    Runs daily at 07:00
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        urgency_threshold = now + timedelta(hours=72)
        tasks_created = 0
        
        # ====================================================================
        # 1. Project deadlines < 72h
        # ====================================================================
        urgent_projects = db.query(Project).filter(
            Project.deadline <= urgency_threshold,
            Project.deadline >= now,
            Project.status.notin_([ProjectStatus.DELIVERED, ProjectStatus.ARCHIVED]),
        ).all()
        
        for project in urgent_projects:
            existing = db.query(AgencyTask).filter(
                AgencyTask.project_id == project.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "deadline_alert",
                AgencyTask.status != TaskStatus.DONE,
            ).first()
            
            if not existing:
                hours_remaining = int((project.deadline - now).total_seconds() / 3600)
                days_remaining = hours_remaining // 24
                
                task = AgencyTask(
                    workspace_id=project.workspace_id,
                    project_id=project.id,
                    title=f"🚨 Deadline proche: {project.name}",
                    description=f"Deadline dans {days_remaining}j {hours_remaining % 24}h\n"
                               f"Client: {project.client.name if project.client else 'N/A'}\n"
                               f"Statut: {project.status.value}",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    due_date=project.deadline,
                    is_auto_generated=True,
                    auto_type="deadline_alert",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created deadline alert for project {project.id}: {project.name}")
        
        # ====================================================================
        # 2. Deliverable due dates < 72h
        # ====================================================================
        urgent_deliverables = db.query(Deliverable).filter(
            Deliverable.due_date <= urgency_threshold,
            Deliverable.due_date >= now,
            Deliverable.status.notin_([DeliverableStatus.APPROVED, DeliverableStatus.DELIVERED]),
        ).all()
        
        for deliverable in urgent_deliverables:
            # Get project for workspace_id
            project = deliverable.project
            if not project:
                continue
            
            existing = db.query(AgencyTask).filter(
                AgencyTask.project_id == project.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "deliverable_deadline",
                AgencyTask.status != TaskStatus.DONE,
            ).first()
            
            if not existing:
                hours_remaining = int((deliverable.due_date - now).total_seconds() / 3600)
                days_remaining = hours_remaining // 24
                
                task = AgencyTask(
                    workspace_id=project.workspace_id,
                    project_id=project.id,
                    title=f"📦 Livrable urgent: {deliverable.name}",
                    description=f"Due dans {days_remaining}j {hours_remaining % 24}h\n"
                               f"Projet: {project.name}\n"
                               f"Statut: {deliverable.status.value}",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    due_date=deliverable.due_date,
                    is_auto_generated=True,
                    auto_type="deliverable_deadline",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created deliverable deadline alert for {deliverable.id}: {deliverable.name}")
        
        db.commit()
        logger.info(f"Deadline alerts: created {tasks_created} tasks")
        return {"tasks_created": tasks_created}
        
    except Exception as e:
        logger.error(f"Error in deadline_alerts: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# BLOCKED PROJECT ALERTS
# ============================================================================

@shared_task(name="app.workers.agency_automations.blocked_project_alerts")
def blocked_project_alerts():
    """
    Create alert tasks for projects that have been blocked too long.
    
    Rules:
    - Project status = BLOCKED for more than 48h → Create alert
    
    Runs daily at 09:00
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tasks_created = 0
        
        blocked_projects = db.query(Project).filter(
            Project.status == ProjectStatus.BLOCKED,
        ).all()
        
        for project in blocked_projects:
            # Check if already alerted recently
            existing = db.query(AgencyTask).filter(
                AgencyTask.project_id == project.id,
                AgencyTask.is_auto_generated == True,
                AgencyTask.auto_type == "blocked_alert",
                AgencyTask.status != TaskStatus.DONE,
                AgencyTask.created_at > now - timedelta(days=2),  # Don't spam
            ).first()
            
            if not existing:
                task = AgencyTask(
                    workspace_id=project.workspace_id,
                    project_id=project.id,
                    title=f"🛑 Projet bloqué: {project.name}",
                    description=f"Le projet est en statut BLOQUÉ.\n"
                               f"Client: {project.client.name if project.client else 'N/A'}\n"
                               f"Action requise pour débloquer.",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.HIGH,
                    due_date=now,
                    is_auto_generated=True,
                    auto_type="blocked_alert",
                )
                db.add(task)
                tasks_created += 1
                logger.info(f"Created blocked alert for project {project.id}")
        
        db.commit()
        logger.info(f"Blocked project alerts: created {tasks_created} tasks")
        return {"tasks_created": tasks_created}
        
    except Exception as e:
        logger.error(f"Error in blocked_project_alerts: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# CLEANUP OLD AUTO TASKS
# ============================================================================

@shared_task(name="app.workers.agency_automations.cleanup_old_auto_tasks")
def cleanup_old_auto_tasks():
    """
    Clean up old auto-generated tasks that are done or irrelevant.
    
    Rules:
    - Auto-generated tasks marked DONE > 7 days ago → Delete
    - Auto-generated tasks > 30 days old and still TODO → Mark as done (stale)
    
    Runs weekly on Sunday at 02:00
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        deleted = 0
        marked_stale = 0
        
        # Delete old done tasks
        seven_days_ago = now - timedelta(days=7)
        old_done = db.query(AgencyTask).filter(
            AgencyTask.is_auto_generated == True,
            AgencyTask.status == TaskStatus.DONE,
            AgencyTask.updated_at < seven_days_ago,
        ).all()
        
        for task in old_done:
            db.delete(task)
            deleted += 1
        
        # Mark stale tasks
        thirty_days_ago = now - timedelta(days=30)
        stale_tasks = db.query(AgencyTask).filter(
            AgencyTask.is_auto_generated == True,
            AgencyTask.status == TaskStatus.TODO,
            AgencyTask.created_at < thirty_days_ago,
        ).all()
        
        for task in stale_tasks:
            task.status = TaskStatus.DONE
            task.description = (task.description or "") + "\n\n[Auto-marked stale]"
            marked_stale += 1
        
        db.commit()
        logger.info(f"Cleanup: deleted {deleted}, marked stale {marked_stale}")
        return {"deleted": deleted, "marked_stale": marked_stale}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_auto_tasks: {e}")
        db.rollback()
        raise
    finally:
        db.close()
