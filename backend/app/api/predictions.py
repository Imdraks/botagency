"""
API endpoints for predictions and weekly reports.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..api.deps import get_current_user, get_db
from ..db.models.user import User
from ..db.models.opportunity import Opportunity
from ..intelligence.predictions import predictions_engine, PredictionResult
from ..intelligence.weekly_report import weekly_report_generator


router = APIRouter(prefix="/predictions", tags=["predictions"])


# Pydantic models for API
class PredictionResponse(BaseModel):
    opportunity_id: str
    success_probability: float
    confidence_level: float
    predicted_outcome: str
    key_factors: List[dict]
    recommendations: List[str]
    risk_assessment: str
    estimated_decision_date: Optional[str] = None


class TrendAnalysisResponse(BaseModel):
    period_days: int
    total_opportunities: int
    by_status: dict
    average_score: float
    score_distribution: dict
    growth_rate: float
    predicted_next_period: int
    recommendations: List[str]


class WeeklyReportResponse(BaseModel):
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    summary: dict
    highlights: List[dict]
    metrics: dict
    recommendations: List[str]
    html_content: str
    markdown_content: str


@router.get("/{opportunity_id}", response_model=PredictionResponse)
async def get_prediction(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI prediction for a specific opportunity."""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Convert to dict for prediction engine
    opp_dict = {
        "id": opportunity.id,
        "title": opportunity.title,
        "description": opportunity.description,
        "organization": opportunity.organization,
        "score": opportunity.score,
        "status": opportunity.status,
        "budget_amount": opportunity.budget_amount,
        "deadline_at": opportunity.deadline_at.isoformat() if opportunity.deadline_at else None,
        "source_type": opportunity.source.source_type if opportunity.source else None,
        "contact_email": opportunity.contact_email,
        "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None,
        "updated_at": opportunity.updated_at.isoformat() if opportunity.updated_at else None,
    }
    
    result = await predictions_engine.predict_opportunity(opp_dict)
    
    return PredictionResponse(
        opportunity_id=result.opportunity_id,
        success_probability=result.success_probability,
        confidence_level=result.confidence_level,
        predicted_outcome=result.predicted_outcome,
        key_factors=result.key_factors,
        recommendations=result.recommendations,
        risk_assessment=result.risk_assessment,
        estimated_decision_date=result.estimated_decision_date.isoformat() if result.estimated_decision_date else None
    )


@router.post("/batch", response_model=List[PredictionResponse])
async def batch_predict(
    opportunity_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI predictions for multiple opportunities."""
    opportunities = db.query(Opportunity).filter(
        Opportunity.id.in_(opportunity_ids)
    ).all()
    
    if not opportunities:
        raise HTTPException(status_code=404, detail="No opportunities found")
    
    opp_dicts = [
        {
            "id": o.id,
            "title": o.title,
            "description": o.description,
            "organization": o.organization,
            "score": o.score,
            "status": o.status,
            "budget_amount": o.budget_amount,
            "deadline_at": o.deadline_at.isoformat() if o.deadline_at else None,
            "source_type": o.source.source_type if o.source else None,
            "contact_email": o.contact_email,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in opportunities
    ]
    
    results = await predictions_engine.batch_predict(opp_dicts)
    
    return [
        PredictionResponse(
            opportunity_id=r.opportunity_id,
            success_probability=r.success_probability,
            confidence_level=r.confidence_level,
            predicted_outcome=r.predicted_outcome,
            key_factors=r.key_factors,
            recommendations=r.recommendations,
            risk_assessment=r.risk_assessment,
            estimated_decision_date=r.estimated_decision_date.isoformat() if r.estimated_decision_date else None
        )
        for r in results
    ]


@router.get("/trends/analysis", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trend analysis for opportunities."""
    opportunities = db.query(Opportunity).all()
    
    opp_dicts = [
        {
            "id": o.id,
            "title": o.title,
            "score": o.score,
            "status": o.status,
            "budget_amount": o.budget_amount,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in opportunities
    ]
    
    result = await predictions_engine.get_trend_analysis(opp_dicts, period_days)
    
    return TrendAnalysisResponse(**result)


# Weekly Report endpoints
reports_router = APIRouter(prefix="/reports", tags=["reports"])


@reports_router.get("/weekly", response_model=WeeklyReportResponse)
async def generate_weekly_report(
    period_days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a weekly report."""
    opportunities = db.query(Opportunity).all()
    
    opp_dicts = [
        {
            "id": o.id,
            "title": o.title,
            "description": o.description,
            "organization": o.organization,
            "score": o.score,
            "status": o.status,
            "budget_amount": o.budget_amount,
            "deadline_at": o.deadline_at.isoformat() if o.deadline_at else None,
            "source_type": o.source.source_type if o.source else None,
            "contact_email": o.contact_email,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        }
        for o in opportunities
    ]
    
    report = await weekly_report_generator.generate_report(opp_dicts, period_days)
    
    return WeeklyReportResponse(
        report_id=report.report_id,
        generated_at=report.generated_at.isoformat(),
        period_start=report.period_start.isoformat(),
        period_end=report.period_end.isoformat(),
        summary=report.summary,
        highlights=report.highlights,
        metrics=report.metrics,
        recommendations=report.recommendations,
        html_content=report.html_content,
        markdown_content=report.markdown_content
    )


@reports_router.post("/weekly/send")
async def send_weekly_report(
    background_tasks: BackgroundTasks,
    recipients: List[str] = None,
    channels: List[str] = None,  # "email", "slack", "discord"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and send weekly report via configured channels."""
    # In production, this would integrate with actual notification services
    
    opportunities = db.query(Opportunity).all()
    opp_dicts = [
        {
            "id": o.id,
            "title": o.title,
            "description": o.description,
            "organization": o.organization,
            "score": o.score,
            "status": o.status,
            "budget_amount": o.budget_amount,
            "deadline_at": o.deadline_at.isoformat() if o.deadline_at else None,
            "source_type": o.source.source_type if o.source else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in opportunities
    ]
    
    report = await weekly_report_generator.generate_report(opp_dicts)
    
    # Add background task to send report
    # background_tasks.add_task(send_report_notifications, report, recipients, channels)
    
    return {
        "status": "scheduled",
        "report_id": report.report_id,
        "recipients": recipients or ["default"],
        "channels": channels or ["email"]
    }
