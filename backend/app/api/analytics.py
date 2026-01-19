"""
Advanced Analytics Dashboard API
Graphiques, tendances, KPIs avancés
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_, case, extract
from sqlalchemy.orm import Session
from collections import defaultdict

from app.db import get_db
from app.db.models.user import User
from app.db.models.opportunity import Opportunity, OpportunityStatus, OpportunityCategory
from app.api.deps import get_current_user
from app.core.cache import cache_get, cache_set

router = APIRouter(prefix="/analytics", tags=["analytics"])

CACHE_TTL = 300  # 5 minutes


# ============================================================================
# ÉVOLUTION TEMPORELLE
# ============================================================================

@router.get("/timeline")
def get_timeline_data(
    period: str = Query("30d", regex="^(7d|30d|90d|12m)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Évolution des opportunités dans le temps
    - Nouvelles opportunités par jour/semaine
    - Tendance globale
    """
    cache_key = f"analytics:timeline:{current_user.id}:{period}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    
    # Parse period
    if period == "7d":
        start_date = now - timedelta(days=7)
        group_by = "day"
    elif period == "30d":
        start_date = now - timedelta(days=30)
        group_by = "day"
    elif period == "90d":
        start_date = now - timedelta(days=90)
        group_by = "week"
    else:  # 12m
        start_date = now - timedelta(days=365)
        group_by = "month"
    
    # Query opportunities
    opps = db.query(Opportunity).filter(
        Opportunity.created_at >= start_date
    ).all()
    
    # Group by period
    timeline = defaultdict(lambda: {"new": 0, "won": 0, "lost": 0, "total_value": 0})
    
    for opp in opps:
        if group_by == "day":
            key = opp.created_at.strftime("%Y-%m-%d")
        elif group_by == "week":
            key = opp.created_at.strftime("%Y-W%W")
        else:
            key = opp.created_at.strftime("%Y-%m")
        
        timeline[key]["new"] += 1
        if opp.budget_amount:
            timeline[key]["total_value"] += float(opp.budget_amount)
        
        if opp.status == OpportunityStatus.WON:
            timeline[key]["won"] += 1
        elif opp.status == OpportunityStatus.LOST:
            timeline[key]["lost"] += 1
    
    # Convert to sorted list
    data = [
        {"date": k, **v}
        for k, v in sorted(timeline.items())
    ]
    
    # Calculate trend (compare last half to first half)
    if len(data) >= 2:
        mid = len(data) // 2
        first_half = sum(d["new"] for d in data[:mid])
        second_half = sum(d["new"] for d in data[mid:])
        if first_half > 0:
            trend = round(((second_half - first_half) / first_half) * 100, 1)
        else:
            trend = 100 if second_half > 0 else 0
    else:
        trend = 0
    
    result = {
        "period": period,
        "data": data,
        "trend": trend,
        "trend_label": "↑" if trend > 0 else "↓" if trend < 0 else "→"
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


# ============================================================================
# TAUX DE CONVERSION
# ============================================================================

@router.get("/conversion")
def get_conversion_metrics(
    period: str = Query("30d", regex="^(7d|30d|90d|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Métriques de conversion
    - Taux de conversion global
    - Par catégorie
    - Par source
    """
    cache_key = f"analytics:conversion:{current_user.id}:{period}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    
    # Date filter
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = None
    
    query = db.query(Opportunity)
    if start_date:
        query = query.filter(Opportunity.created_at >= start_date)
    
    opps = query.all()
    
    # Global conversion
    total = len(opps)
    won = len([o for o in opps if o.status == OpportunityStatus.WON])
    lost = len([o for o in opps if o.status == OpportunityStatus.LOST])
    pending = len([o for o in opps if o.status in [
        OpportunityStatus.NEW, 
        OpportunityStatus.CONTACTED,
        OpportunityStatus.IN_PROGRESS
    ]])
    
    global_rate = round((won / (won + lost) * 100), 1) if (won + lost) > 0 else 0
    
    # By category
    by_category = defaultdict(lambda: {"total": 0, "won": 0, "lost": 0})
    for opp in opps:
        cat = opp.category.value if opp.category else "unknown"
        by_category[cat]["total"] += 1
        if opp.status == OpportunityStatus.WON:
            by_category[cat]["won"] += 1
        elif opp.status == OpportunityStatus.LOST:
            by_category[cat]["lost"] += 1
    
    category_rates = []
    for cat, data in by_category.items():
        decided = data["won"] + data["lost"]
        rate = round((data["won"] / decided * 100), 1) if decided > 0 else None
        category_rates.append({
            "category": cat,
            "total": data["total"],
            "won": data["won"],
            "lost": data["lost"],
            "rate": rate
        })
    category_rates.sort(key=lambda x: x["rate"] or 0, reverse=True)
    
    # By source
    by_source = defaultdict(lambda: {"total": 0, "won": 0, "lost": 0})
    for opp in opps:
        source = opp.source_name or "unknown"
        by_source[source]["total"] += 1
        if opp.status == OpportunityStatus.WON:
            by_source[source]["won"] += 1
        elif opp.status == OpportunityStatus.LOST:
            by_source[source]["lost"] += 1
    
    source_rates = []
    for source, data in by_source.items():
        decided = data["won"] + data["lost"]
        rate = round((data["won"] / decided * 100), 1) if decided > 0 else None
        source_rates.append({
            "source": source,
            "total": data["total"],
            "won": data["won"],
            "lost": data["lost"],
            "rate": rate
        })
    source_rates.sort(key=lambda x: x["rate"] or 0, reverse=True)
    
    result = {
        "period": period,
        "global": {
            "total": total,
            "won": won,
            "lost": lost,
            "pending": pending,
            "conversion_rate": global_rate
        },
        "by_category": category_rates[:10],
        "by_source": source_rates[:10]
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


# ============================================================================
# HEATMAP DEADLINES
# ============================================================================

@router.get("/deadline-heatmap")
def get_deadline_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Heatmap des deadlines par mois
    - Nombre d'opportunités par mois
    - Valeur totale par mois
    """
    cache_key = f"analytics:heatmap:{current_user.id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Get opportunities with deadlines in the next 12 months
    now = datetime.utcnow()
    end_date = now + timedelta(days=365)
    
    opps = db.query(Opportunity).filter(
        and_(
            Opportunity.deadline_at.isnot(None),
            Opportunity.deadline_at >= now,
            Opportunity.deadline_at <= end_date,
            Opportunity.status.notin_([OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.CANCELLED])
        )
    ).all()
    
    # Group by month
    heatmap = defaultdict(lambda: {"count": 0, "value": 0, "high_priority": 0})
    
    for opp in opps:
        month_key = opp.deadline_at.strftime("%Y-%m")
        heatmap[month_key]["count"] += 1
        if opp.budget_amount:
            heatmap[month_key]["value"] += float(opp.budget_amount)
        if opp.score and opp.score >= 70:
            heatmap[month_key]["high_priority"] += 1
    
    # Convert to list with month names
    months_fr = {
        "01": "Jan", "02": "Fév", "03": "Mar", "04": "Avr",
        "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Déc"
    }
    
    data = []
    for key in sorted(heatmap.keys()):
        year, month = key.split("-")
        data.append({
            "month": key,
            "label": f"{months_fr[month]} {year}",
            "count": heatmap[key]["count"],
            "value": round(heatmap[key]["value"], 2),
            "high_priority": heatmap[key]["high_priority"]
        })
    
    # Find hottest month
    hottest = max(data, key=lambda x: x["count"]) if data else None
    
    result = {
        "data": data,
        "hottest_month": hottest,
        "total_upcoming": sum(d["count"] for d in data),
        "total_value": sum(d["value"] for d in data)
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


# ============================================================================
# COMPARAISON PÉRIODE
# ============================================================================

@router.get("/comparison")
def get_period_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Comparaison ce mois vs mois précédent
    - Nouvelles opportunités
    - Valeur totale
    - Taux de conversion
    """
    cache_key = f"analytics:comparison:{current_user.id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    
    # Current month
    current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous month
    prev_end = current_start - timedelta(seconds=1)
    prev_start = prev_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Query both periods
    current_opps = db.query(Opportunity).filter(
        Opportunity.created_at >= current_start
    ).all()
    
    prev_opps = db.query(Opportunity).filter(
        and_(
            Opportunity.created_at >= prev_start,
            Opportunity.created_at < current_start
        )
    ).all()
    
    def calc_metrics(opps):
        total = len(opps)
        won = len([o for o in opps if o.status == OpportunityStatus.WON])
        lost = len([o for o in opps if o.status == OpportunityStatus.LOST])
        value = sum(float(o.budget_amount) for o in opps if o.budget_amount)
        rate = round((won / (won + lost) * 100), 1) if (won + lost) > 0 else 0
        return {
            "count": total,
            "won": won,
            "lost": lost,
            "value": round(value, 2),
            "conversion_rate": rate
        }
    
    current = calc_metrics(current_opps)
    previous = calc_metrics(prev_opps)
    
    def calc_change(curr, prev):
        if prev == 0:
            return 100 if curr > 0 else 0
        return round(((curr - prev) / prev) * 100, 1)
    
    result = {
        "current_period": {
            "label": current_start.strftime("%B %Y"),
            **current
        },
        "previous_period": {
            "label": prev_start.strftime("%B %Y"),
            **previous
        },
        "changes": {
            "count": calc_change(current["count"], previous["count"]),
            "value": calc_change(current["value"], previous["value"]),
            "conversion_rate": round(current["conversion_rate"] - previous["conversion_rate"], 1)
        }
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


# ============================================================================
# KPIs EN TEMPS RÉEL
# ============================================================================

@router.get("/kpis")
def get_realtime_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    KPIs principaux avec tendances
    """
    cache_key = f"analytics:kpis:{current_user.id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Today's new
    today_new = db.query(Opportunity).filter(
        Opportunity.created_at >= today_start
    ).count()
    
    # This week's new
    week_new = db.query(Opportunity).filter(
        Opportunity.created_at >= week_start
    ).count()
    
    # This month's value
    month_opps = db.query(Opportunity).filter(
        Opportunity.created_at >= month_start
    ).all()
    month_value = sum(float(o.budget_amount) for o in month_opps if o.budget_amount)
    
    # Pending high score
    high_score_pending = db.query(Opportunity).filter(
        and_(
            Opportunity.score >= 70,
            Opportunity.status.in_([
                OpportunityStatus.NEW,
                OpportunityStatus.CONTACTED,
                OpportunityStatus.IN_PROGRESS
            ])
        )
    ).count()
    
    # Urgent deadlines (next 7 days)
    urgent_deadline = db.query(Opportunity).filter(
        and_(
            Opportunity.deadline_at.isnot(None),
            Opportunity.deadline_at >= now,
            Opportunity.deadline_at <= now + timedelta(days=7),
            Opportunity.status.notin_([OpportunityStatus.WON, OpportunityStatus.LOST, OpportunityStatus.CANCELLED])
        )
    ).count()
    
    # Average score
    avg_score = db.query(func.avg(Opportunity.score)).filter(
        Opportunity.score.isnot(None)
    ).scalar() or 0
    
    # Compare with last week for trends
    last_week_start = week_start - timedelta(days=7)
    last_week_new = db.query(Opportunity).filter(
        and_(
            Opportunity.created_at >= last_week_start,
            Opportunity.created_at < week_start
        )
    ).count()
    
    week_trend = "↑" if week_new > last_week_new else "↓" if week_new < last_week_new else "→"
    
    result = {
        "today_new": today_new,
        "week_new": week_new,
        "week_trend": week_trend,
        "month_value": round(month_value, 2),
        "high_score_pending": high_score_pending,
        "urgent_deadlines": urgent_deadline,
        "avg_score": round(float(avg_score), 1),
        "updated_at": now.isoformat()
    }
    
    cache_set(cache_key, result, 60)  # 1 minute cache for real-time
    return result


# ============================================================================
# TOP PERFORMERS
# ============================================================================

@router.get("/top-performers")
def get_top_performers(
    period: str = Query("30d", regex="^(30d|90d|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Top sources, catégories et régions performantes
    """
    cache_key = f"analytics:top:{current_user.id}:{period}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    
    if period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = None
    
    query = db.query(Opportunity).filter(
        Opportunity.status == OpportunityStatus.WON
    )
    if start_date:
        query = query.filter(Opportunity.created_at >= start_date)
    
    won_opps = query.all()
    
    # Top sources
    sources = defaultdict(lambda: {"count": 0, "value": 0})
    for opp in won_opps:
        source = opp.source_name or "unknown"
        sources[source]["count"] += 1
        if opp.budget_amount:
            sources[source]["value"] += float(opp.budget_amount)
    
    top_sources = sorted(
        [{"name": k, **v} for k, v in sources.items()],
        key=lambda x: x["value"],
        reverse=True
    )[:5]
    
    # Top categories
    categories = defaultdict(lambda: {"count": 0, "value": 0})
    for opp in won_opps:
        cat = opp.category.value if opp.category else "other"
        categories[cat]["count"] += 1
        if opp.budget_amount:
            categories[cat]["value"] += float(opp.budget_amount)
    
    top_categories = sorted(
        [{"name": k, **v} for k, v in categories.items()],
        key=lambda x: x["value"],
        reverse=True
    )[:5]
    
    # Top regions
    regions = defaultdict(lambda: {"count": 0, "value": 0})
    for opp in won_opps:
        region = opp.location_region or "unknown"
        regions[region]["count"] += 1
        if opp.budget_amount:
            regions[region]["value"] += float(opp.budget_amount)
    
    top_regions = sorted(
        [{"name": k, **v} for k, v in regions.items()],
        key=lambda x: x["value"],
        reverse=True
    )[:5]
    
    result = {
        "period": period,
        "total_won": len(won_opps),
        "total_value": round(sum(float(o.budget_amount) for o in won_opps if o.budget_amount), 2),
        "top_sources": top_sources,
        "top_categories": top_categories,
        "top_regions": top_regions
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result
