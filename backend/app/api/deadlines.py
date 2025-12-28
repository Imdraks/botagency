"""
Deadline Guard API - Deadline Alerts Management
"""
from datetime import datetime, timedelta, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db import get_db
from app.db.models import Opportunity, DeadlineAlert, AlertType, AlertStatus
from app.api.deps import get_current_user, get_current_admin_user
from app.schemas.radar_features import (
    DeadlineAlertResponse,
    UpcomingDeadlinesResponse,
    TestNotificationRequest,
    TestNotificationResponse,
)

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


def create_deadline_alerts_for_opportunity(db: Session, opportunity: Opportunity):
    """Create D7, D3, D1 alerts for an opportunity with a deadline"""
    if not opportunity.deadline_at:
        return
    
    now = datetime.utcnow()
    
    # Define alert schedules
    alert_configs = [
        (AlertType.D7, 7),
        (AlertType.D3, 3),
        (AlertType.D1, 1),
    ]
    
    for alert_type, days_before in alert_configs:
        scheduled_for = opportunity.deadline_at - timedelta(days=days_before)
        
        # Only create if in the future
        if scheduled_for > now:
            # Check if alert already exists
            existing = db.query(DeadlineAlert).filter(
                DeadlineAlert.opportunity_id == opportunity.id,
                DeadlineAlert.alert_type == alert_type
            ).first()
            
            if not existing:
                alert = DeadlineAlert(
                    opportunity_id=opportunity.id,
                    alert_type=alert_type,
                    scheduled_for=scheduled_for,
                    status=AlertStatus.PENDING,
                    channels=["email"],
                )
                db.add(alert)
    
    db.commit()


@router.get("/upcoming", response_model=UpcomingDeadlinesResponse)
def get_upcoming_deadlines(
    days_ahead: int = Query(default=14, ge=1, le=60),
    status_filter: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get upcoming deadline alerts"""
    now = datetime.utcnow()
    future_limit = now + timedelta(days=days_ahead)
    
    query = db.query(DeadlineAlert).filter(
        DeadlineAlert.scheduled_for >= now,
        DeadlineAlert.scheduled_for <= future_limit,
    )
    
    if status_filter:
        try:
            status_enum = AlertStatus(status_filter)
            query = query.filter(DeadlineAlert.status == status_enum)
        except ValueError:
            pass
    
    alerts = query.order_by(DeadlineAlert.scheduled_for.asc()).limit(limit).all()
    
    # Fetch opportunity details
    opportunity_ids = [a.opportunity_id for a in alerts]
    opportunities = {
        o.id: o for o in db.query(Opportunity).filter(
            Opportunity.id.in_(opportunity_ids)
        ).all()
    }
    
    alert_responses = []
    for alert in alerts:
        opp = opportunities.get(alert.opportunity_id)
        if opp:
            alert_responses.append(DeadlineAlertResponse(
                id=alert.id,
                opportunity_id=alert.opportunity_id,
                opportunity_title=opp.title,
                organization=opp.organization,
                alert_type=alert.alert_type.value,
                scheduled_for=alert.scheduled_for,
                deadline_at=opp.deadline_at,
                status=alert.status.value,
                sent_at=alert.sent_at,
            ))
    
    return UpcomingDeadlinesResponse(
        alerts=alert_responses,
        total=len(alert_responses),
    )


@router.get("/past", response_model=UpcomingDeadlinesResponse)
def get_past_deadline_alerts(
    days_back: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get past deadline alerts (for review)"""
    now = datetime.utcnow()
    past_limit = now - timedelta(days=days_back)
    
    alerts = db.query(DeadlineAlert).filter(
        DeadlineAlert.scheduled_for >= past_limit,
        DeadlineAlert.scheduled_for < now,
    ).order_by(DeadlineAlert.scheduled_for.desc()).limit(limit).all()
    
    # Fetch opportunity details
    opportunity_ids = [a.opportunity_id for a in alerts]
    opportunities = {
        o.id: o for o in db.query(Opportunity).filter(
            Opportunity.id.in_(opportunity_ids)
        ).all()
    }
    
    alert_responses = []
    for alert in alerts:
        opp = opportunities.get(alert.opportunity_id)
        if opp:
            alert_responses.append(DeadlineAlertResponse(
                id=alert.id,
                opportunity_id=alert.opportunity_id,
                opportunity_title=opp.title,
                organization=opp.organization,
                alert_type=alert.alert_type.value,
                scheduled_for=alert.scheduled_for,
                deadline_at=opp.deadline_at,
                status=alert.status.value,
                sent_at=alert.sent_at,
            ))
    
    return UpcomingDeadlinesResponse(
        alerts=alert_responses,
        total=len(alert_responses),
    )


@router.post("/test-notification", response_model=TestNotificationResponse)
async def test_notification(
    data: TestNotificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Test sending a deadline notification"""
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == data.opportunity_id
    ).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # For now, just log the test
    # In production, this would send actual email/webhook
    
    if data.channel == "email":
        # Mock email sending
        message = f"Test notification sent for: {opportunity.title}"
        # background_tasks.add_task(send_email_notification, opportunity, current_user)
        return TestNotificationResponse(
            success=True,
            message=message,
            channel="email",
        )
    elif data.channel == "webhook":
        message = f"Webhook test for: {opportunity.title}"
        return TestNotificationResponse(
            success=True,
            message=message,
            channel="webhook",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown channel: {data.channel}"
        )


@router.post("/schedule-all")
def schedule_all_deadline_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Schedule deadline alerts for all opportunities with deadlines"""
    # Get opportunities with deadlines in the future
    now = datetime.utcnow()
    
    opportunities = db.query(Opportunity).filter(
        Opportunity.deadline_at > now,
        Opportunity.status.notin_(["ARCHIVED", "LOST", "WON"]),
    ).all()
    
    created_count = 0
    for opp in opportunities:
        # Count before
        before = db.query(DeadlineAlert).filter(
            DeadlineAlert.opportunity_id == opp.id
        ).count()
        
        create_deadline_alerts_for_opportunity(db, opp)
        
        # Count after
        after = db.query(DeadlineAlert).filter(
            DeadlineAlert.opportunity_id == opp.id
        ).count()
        
        created_count += (after - before)
    
    return {
        "opportunities_processed": len(opportunities),
        "alerts_created": created_count,
    }


@router.delete("/{alert_id}")
def cancel_deadline_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
):
    """Cancel a deadline alert"""
    alert = db.query(DeadlineAlert).filter(DeadlineAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.status == AlertStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel an already sent alert"
        )
    
    alert.status = AlertStatus.CANCELLED
    db.commit()
    
    return {"status": "cancelled", "alert_id": str(alert_id)}
