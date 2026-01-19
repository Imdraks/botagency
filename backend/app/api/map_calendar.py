"""
Map & Calendar API for Opportunities
Geographic visualization and calendar export
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import and_
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.db import get_db
from app.db.models.user import User
from app.db.models.opportunity import Opportunity, OpportunityStatus
from app.api.deps import get_current_user
from app.core.cache import cache_get, cache_set

router = APIRouter(prefix="/map", tags=["map"])

CACHE_TTL = 300  # 5 minutes

# French regions with approximate center coordinates
REGION_COORDS = {
    # Régions métropolitaines
    "ile-de-france": {"lat": 48.8566, "lng": 2.3522, "name": "Île-de-France"},
    "ile de france": {"lat": 48.8566, "lng": 2.3522, "name": "Île-de-France"},
    "paris": {"lat": 48.8566, "lng": 2.3522, "name": "Paris"},
    "auvergne-rhone-alpes": {"lat": 45.7640, "lng": 4.8357, "name": "Auvergne-Rhône-Alpes"},
    "auvergne rhone alpes": {"lat": 45.7640, "lng": 4.8357, "name": "Auvergne-Rhône-Alpes"},
    "rhone-alpes": {"lat": 45.7640, "lng": 4.8357, "name": "Rhône-Alpes"},
    "lyon": {"lat": 45.7640, "lng": 4.8357, "name": "Lyon"},
    "nouvelle-aquitaine": {"lat": 44.8378, "lng": -0.5792, "name": "Nouvelle-Aquitaine"},
    "nouvelle aquitaine": {"lat": 44.8378, "lng": -0.5792, "name": "Nouvelle-Aquitaine"},
    "bordeaux": {"lat": 44.8378, "lng": -0.5792, "name": "Bordeaux"},
    "occitanie": {"lat": 43.6047, "lng": 1.4442, "name": "Occitanie"},
    "toulouse": {"lat": 43.6047, "lng": 1.4442, "name": "Toulouse"},
    "montpellier": {"lat": 43.6108, "lng": 3.8767, "name": "Montpellier"},
    "provence-alpes-cote-d-azur": {"lat": 43.2965, "lng": 5.3698, "name": "PACA"},
    "paca": {"lat": 43.2965, "lng": 5.3698, "name": "PACA"},
    "provence": {"lat": 43.2965, "lng": 5.3698, "name": "Provence"},
    "marseille": {"lat": 43.2965, "lng": 5.3698, "name": "Marseille"},
    "nice": {"lat": 43.7102, "lng": 7.2620, "name": "Nice"},
    "hauts-de-france": {"lat": 49.8941, "lng": 2.2958, "name": "Hauts-de-France"},
    "hauts de france": {"lat": 49.8941, "lng": 2.2958, "name": "Hauts-de-France"},
    "lille": {"lat": 50.6292, "lng": 3.0573, "name": "Lille"},
    "grand-est": {"lat": 48.5734, "lng": 7.7521, "name": "Grand Est"},
    "grand est": {"lat": 48.5734, "lng": 7.7521, "name": "Grand Est"},
    "strasbourg": {"lat": 48.5734, "lng": 7.7521, "name": "Strasbourg"},
    "bretagne": {"lat": 48.1173, "lng": -1.6778, "name": "Bretagne"},
    "rennes": {"lat": 48.1173, "lng": -1.6778, "name": "Rennes"},
    "brest": {"lat": 48.3904, "lng": -4.4861, "name": "Brest"},
    "normandie": {"lat": 49.1829, "lng": -0.3707, "name": "Normandie"},
    "caen": {"lat": 49.1829, "lng": -0.3707, "name": "Caen"},
    "rouen": {"lat": 49.4432, "lng": 1.0993, "name": "Rouen"},
    "pays-de-la-loire": {"lat": 47.2184, "lng": -1.5536, "name": "Pays de la Loire"},
    "pays de la loire": {"lat": 47.2184, "lng": -1.5536, "name": "Pays de la Loire"},
    "nantes": {"lat": 47.2184, "lng": -1.5536, "name": "Nantes"},
    "centre-val-de-loire": {"lat": 47.9029, "lng": 1.9039, "name": "Centre-Val de Loire"},
    "centre": {"lat": 47.9029, "lng": 1.9039, "name": "Centre"},
    "orleans": {"lat": 47.9029, "lng": 1.9039, "name": "Orléans"},
    "tours": {"lat": 47.3941, "lng": 0.6848, "name": "Tours"},
    "bourgogne-franche-comte": {"lat": 47.3220, "lng": 5.0415, "name": "Bourgogne-Franche-Comté"},
    "bourgogne": {"lat": 47.3220, "lng": 5.0415, "name": "Bourgogne"},
    "dijon": {"lat": 47.3220, "lng": 5.0415, "name": "Dijon"},
    "corse": {"lat": 42.0396, "lng": 9.0129, "name": "Corse"},
    "ajaccio": {"lat": 41.9192, "lng": 8.7386, "name": "Ajaccio"},
    # DOM-TOM
    "guadeloupe": {"lat": 16.2650, "lng": -61.5510, "name": "Guadeloupe"},
    "martinique": {"lat": 14.6415, "lng": -61.0242, "name": "Martinique"},
    "guyane": {"lat": 4.9372, "lng": -52.3260, "name": "Guyane"},
    "reunion": {"lat": -21.1151, "lng": 55.5364, "name": "Réunion"},
    "la reunion": {"lat": -21.1151, "lng": 55.5364, "name": "Réunion"},
    "mayotte": {"lat": -12.8275, "lng": 45.1662, "name": "Mayotte"},
    # Autres pays courants
    "belgique": {"lat": 50.8503, "lng": 4.3517, "name": "Belgique"},
    "suisse": {"lat": 46.8182, "lng": 8.2275, "name": "Suisse"},
    "luxembourg": {"lat": 49.6117, "lng": 6.1319, "name": "Luxembourg"},
    "monaco": {"lat": 43.7384, "lng": 7.4246, "name": "Monaco"},
    # National
    "france": {"lat": 46.2276, "lng": 2.2137, "name": "France"},
    "national": {"lat": 46.2276, "lng": 2.2137, "name": "National"},
}


def get_coordinates_for_location(location: str) -> Optional[Dict[str, Any]]:
    """Get coordinates for a location string"""
    if not location:
        return None
    
    location_lower = location.lower().strip()
    
    # Direct match
    if location_lower in REGION_COORDS:
        return REGION_COORDS[location_lower]
    
    # Partial match
    for key, coords in REGION_COORDS.items():
        if key in location_lower or location_lower in key:
            return coords
    
    return None


# ============================================================================
# MAP ENDPOINTS
# ============================================================================

@router.get("/opportunities")
def get_map_opportunities(
    status: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get opportunities with geographic coordinates for map display"""
    cache_key = f"map:opps:{current_user.id}:{status}:{category}:{min_score}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    query = db.query(Opportunity)
    
    # Filters
    if status:
        try:
            status_enum = OpportunityStatus(status)
            query = query.filter(Opportunity.status == status_enum)
        except ValueError:
            pass
    
    if min_score:
        query = query.filter(Opportunity.score >= min_score)
    
    # Exclude closed opportunities
    query = query.filter(
        Opportunity.status.notin_([
            OpportunityStatus.CANCELLED
        ])
    )
    
    opportunities = query.limit(500).all()
    
    # Group by location
    markers = []
    clusters = {}  # Group by region for clustering
    
    for opp in opportunities:
        location = opp.location_region or opp.location_city
        coords = get_coordinates_for_location(location)
        
        if coords:
            # Add some jitter to avoid exact overlaps
            import random
            jitter_lat = (random.random() - 0.5) * 0.1
            jitter_lng = (random.random() - 0.5) * 0.1
            
            marker = {
                "id": opp.id,
                "title": opp.title[:80] if opp.title else "Sans titre",
                "lat": coords["lat"] + jitter_lat,
                "lng": coords["lng"] + jitter_lng,
                "score": opp.score or 0,
                "status": opp.status.value if opp.status else "new",
                "category": opp.category.value if opp.category else None,
                "budget": float(opp.budget_amount) if opp.budget_amount else None,
                "deadline": opp.deadline_at.isoformat() if opp.deadline_at else None,
                "organization": opp.organization,
                "region": coords["name"]
            }
            markers.append(marker)
            
            # Cluster tracking
            region_name = coords["name"]
            if region_name not in clusters:
                clusters[region_name] = {
                    "name": region_name,
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "count": 0,
                    "total_value": 0
                }
            clusters[region_name]["count"] += 1
            if opp.budget_amount:
                clusters[region_name]["total_value"] += float(opp.budget_amount)
    
    result = {
        "markers": markers,
        "clusters": list(clusters.values()),
        "total": len(markers),
        "center": {"lat": 46.2276, "lng": 2.2137},  # France center
        "zoom": 6
    }
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


@router.get("/regions/stats")
def get_region_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get statistics per region"""
    cache_key = f"map:regions:{current_user.id}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    opportunities = db.query(Opportunity).filter(
        Opportunity.status.notin_([OpportunityStatus.CANCELLED])
    ).all()
    
    regions = {}
    for opp in opportunities:
        location = opp.location_region or opp.location_city
        coords = get_coordinates_for_location(location)
        
        if coords:
            region = coords["name"]
            if region not in regions:
                regions[region] = {
                    "name": region,
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "count": 0,
                    "won": 0,
                    "total_value": 0,
                    "avg_score": []
                }
            
            regions[region]["count"] += 1
            if opp.status == OpportunityStatus.WON:
                regions[region]["won"] += 1
            if opp.budget_amount:
                regions[region]["total_value"] += float(opp.budget_amount)
            if opp.score:
                regions[region]["avg_score"].append(opp.score)
    
    result = []
    for region_data in regions.values():
        scores = region_data.pop("avg_score")
        region_data["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
        region_data["total_value"] = round(region_data["total_value"], 2)
        result.append(region_data)
    
    result.sort(key=lambda x: x["count"], reverse=True)
    
    cache_set(cache_key, result, CACHE_TTL)
    return result


# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================

calendar_router = APIRouter(prefix="/calendar", tags=["calendar"])


@calendar_router.get("/ical")
def get_ical_feed(
    token: str = Query(..., description="User API token"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate iCal feed for deadlines
    Subscribe to this URL in Google Calendar, Outlook, etc.
    """
    # Validate token and get user
    from app.core.security import decode_token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return Response(content="Invalid token", status_code=401)
    except Exception:
        return Response(content="Invalid token", status_code=401)
    
    # Get opportunities with deadlines
    now = datetime.utcnow()
    opportunities = db.query(Opportunity).filter(
        and_(
            Opportunity.deadline_at.isnot(None),
            Opportunity.deadline_at >= now,
            Opportunity.status.notin_([
                OpportunityStatus.WON,
                OpportunityStatus.LOST,
                OpportunityStatus.CANCELLED
            ])
        )
    ).order_by(Opportunity.deadline_at).limit(100).all()
    
    # Build iCal content
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Radar//Opportunities Calendar//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Radar Deadlines",
        "X-WR-TIMEZONE:Europe/Paris",
    ]
    
    for opp in opportunities:
        uid = f"opp-{opp.id}@radar.app"
        dtstart = opp.deadline_at.strftime("%Y%m%d")
        dtend = (opp.deadline_at + timedelta(days=1)).strftime("%Y%m%d")
        created = opp.created_at.strftime("%Y%m%dT%H%M%SZ") if opp.created_at else now.strftime("%Y%m%dT%H%M%SZ")
        
        summary = f"[Deadline] {opp.title[:50]}" if opp.title else "[Deadline] Opportunité"
        description = []
        if opp.organization:
            description.append(f"Organisation: {opp.organization}")
        if opp.budget_amount:
            description.append(f"Budget: {opp.budget_amount}€")
        if opp.score:
            description.append(f"Score: {opp.score}")
        description.append(f"\\nVoir: https://radarapp.fr/leads/{opp.id}")
        
        ical_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"DTSTAMP:{created}",
            f"CREATED:{created}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{' | '.join(description)}",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            # Add reminder 1 day before
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Deadline demain!",
            "TRIGGER:-P1D",
            "END:VALARM",
            # Add reminder 1 week before
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Deadline dans 7 jours",
            "TRIGGER:-P7D",
            "END:VALARM",
            "END:VEVENT",
        ])
    
    ical_lines.append("END:VCALENDAR")
    
    content = "\r\n".join(ical_lines)
    
    return Response(
        content=content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=radar-deadlines.ics"
        }
    )


@calendar_router.get("/events")
def get_calendar_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get events for calendar view (FullCalendar format)"""
    query = db.query(Opportunity).filter(
        Opportunity.deadline_at.isnot(None)
    )
    
    if start:
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            query = query.filter(Opportunity.deadline_at >= start_date)
        except ValueError:
            pass
    
    if end:
        try:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            query = query.filter(Opportunity.deadline_at <= end_date)
        except ValueError:
            pass
    
    opportunities = query.order_by(Opportunity.deadline_at).all()
    
    events = []
    for opp in opportunities:
        # Color based on status
        color = "#3B82F6"  # blue default
        if opp.status == OpportunityStatus.WON:
            color = "#10B981"  # green
        elif opp.status == OpportunityStatus.LOST:
            color = "#EF4444"  # red
        elif opp.status == OpportunityStatus.IN_PROGRESS:
            color = "#F59E0B"  # amber
        elif opp.score and opp.score >= 70:
            color = "#8B5CF6"  # purple for high score
        
        events.append({
            "id": str(opp.id),
            "title": opp.title[:40] if opp.title else "Opportunité",
            "start": opp.deadline_at.isoformat(),
            "allDay": True,
            "backgroundColor": color,
            "borderColor": color,
            "extendedProps": {
                "opportunityId": opp.id,
                "score": opp.score,
                "status": opp.status.value if opp.status else None,
                "budget": float(opp.budget_amount) if opp.budget_amount else None,
                "organization": opp.organization
            }
        })
    
    return events


@calendar_router.get("/subscription-url")
def get_subscription_url(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Get the iCal subscription URL for this user"""
    from app.core.security import create_access_token
    
    # Create a long-lived token for calendar subscription
    token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(days=365)
    )
    
    return {
        "url": f"https://radarapp.fr/api/v1/calendar/ical?token={token}",
        "instructions": "Copiez cette URL et ajoutez-la comme calendrier externe dans Google Calendar ou Outlook"
    }
