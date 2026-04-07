"""
Radar Analytics V2 — Tour de contrôle du marché
Cockpit, terrain analysis, qualification funnel, competitive gaps.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_, desc, case
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models.user import User
from app.api.deps import get_current_user, get_user_workspace_id
from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics-v2", tags=["analytics-v2"])

CACHE_TTL = 120  # 2 min


# ============================================================================
# COCKPIT — "Qu'est-ce qui bouge maintenant ?"
# ============================================================================

@router.get("/cockpit")
def get_cockpit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
) -> Dict[str, Any]:
    cache_key = f"analytics-v2:cockpit:{workspace_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    try:
        from app.db.models.discovery import DiscoveryArtist, DiscoveryComputedMetrics
        from app.db.models.artist_event import ArtistEvent
    except ImportError:
        return {"signals_count": 0, "kpis": {}, "movements": [], "upcoming": [], "data_quality": {}, "hotspots": []}

    # ── Signals count (artists accelerating this week) ──
    rising_q = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.velocity > 0,
        )
    )
    signals_count = rising_q.scalar() or 0

    # ── 4 KPIs ──
    events_30d = db.query(func.count(ArtistEvent.id)).filter(
        ArtistEvent.workspace_id == workspace_id,
        ArtistEvent.is_deleted == False,
        ArtistEvent.event_date >= now,
        ArtistEvent.event_date <= now + timedelta(days=30),
    ).scalar() or 0

    artists_moving = signals_count

    active_cities = db.query(func.count(func.distinct(ArtistEvent.city))).filter(
        ArtistEvent.workspace_id == workspace_id,
        ArtistEvent.is_deleted == False,
        ArtistEvent.event_date >= now,
        ArtistEvent.city.isnot(None),
    ).scalar() or 0

    qualified_opps = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.score >= 60,
        )
        .scalar() or 0
    )

    kpis = {
        "events_30d": events_30d,
        "artists_moving": artists_moving,
        "active_cities": active_cities,
        "qualified_opportunities": qualified_opps,
    }

    # ── Movements (last 10 notable changes) ──
    movements: List[Dict[str, Any]] = []

    # New events added recently
    recent_events = (
        db.query(ArtistEvent)
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.created_at >= week_ago,
        )
        .order_by(desc(ArtistEvent.created_at))
        .limit(5)
        .all()
    )
    for ev in recent_events:
        movements.append({
            "type": "new_event",
            "icon": "calendar",
            "text": f"{ev.artist_name} — {ev.event_name} à {ev.city or '?'}",
            "timestamp": ev.created_at.isoformat() if ev.created_at else None,
            "artist_name": ev.artist_name,
            "city": ev.city,
        })

    # Artists accelerating
    accelerating = (
        db.query(
            DiscoveryArtist.canonical_name,
            DiscoveryArtist.image_url,
            DiscoveryComputedMetrics.velocity,
            DiscoveryComputedMetrics.score,
        )
        .join(DiscoveryComputedMetrics, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.velocity > 3,
        )
        .order_by(desc(DiscoveryComputedMetrics.velocity))
        .limit(5)
        .all()
    )
    for a in accelerating:
        movements.append({
            "type": "acceleration",
            "icon": "trending-up",
            "text": f"{a.canonical_name} — +{round(a.velocity, 1)}% de croissance",
            "timestamp": now.isoformat(),
            "artist_name": a.canonical_name,
        })

    movements.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    movements = movements[:8]

    # ── Upcoming events (next 5 by date) ──
    upcoming = (
        db.query(ArtistEvent)
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
        )
        .order_by(ArtistEvent.event_date.asc())
        .limit(5)
        .all()
    )
    upcoming_list = []
    for ev in upcoming:
        days_until = (ev.event_date - now).days if ev.event_date else 999
        upcoming_list.append({
            "artist_name": ev.artist_name,
            "venue": ev.venue,
            "city": ev.city,
            "date": ev.event_date.isoformat() if ev.event_date else None,
            "date_label": ev.event_date.strftime("%d %b %Y") if ev.event_date else "",
            "days_until": days_until,
            "event_type": ev.event_type,
        })

    # ── Data quality ──
    total_artists = db.query(func.count(DiscoveryArtist.id)).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
    ).scalar() or 0

    with_score = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.score > 0,
        )
        .scalar() or 0
    )

    with_fee = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.fee_estimate_min.isnot(None),
            DiscoveryComputedMetrics.fee_estimate_min > 0,
        )
        .scalar() or 0
    )

    with_event = db.query(func.count(func.distinct(ArtistEvent.artist_name))).filter(
        ArtistEvent.workspace_id == workspace_id,
        ArtistEvent.is_deleted == False,
    ).scalar() or 0

    data_quality = {
        "total_artists": total_artists,
        "scored_pct": round((with_score / total_artists * 100) if total_artists > 0 else 0),
        "fee_estimated_pct": round((with_fee / total_artists * 100) if total_artists > 0 else 0),
        "event_coverage_pct": round((with_event / total_artists * 100) if total_artists > 0 else 0),
    }

    # ── Hotspots (cities with most upcoming events — for mini-map) ──
    city_events = (
        db.query(
            ArtistEvent.city,
            func.count(ArtistEvent.id).label("count"),
            func.avg(ArtistEvent.lat).label("lat"),
            func.avg(ArtistEvent.lng).label("lng"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
            ArtistEvent.city.isnot(None),
            ArtistEvent.lat.isnot(None),
        )
        .group_by(ArtistEvent.city)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )
    hotspots = [
        {"city": c.city, "count": c.count, "lat": float(c.lat), "lng": float(c.lng)}
        for c in city_events
    ]

    result = {
        "signals_count": signals_count,
        "kpis": kpis,
        "movements": movements,
        "upcoming": upcoming_list,
        "data_quality": data_quality,
        "hotspots": hotspots,
        "generated_at": now.isoformat(),
    }

    cache_set(cache_key, result, ttl=CACHE_TTL)
    return result


# ============================================================================
# TERRAIN OVERVIEW — "Quelle est la structure du terrain ?"
# ============================================================================

@router.get("/terrain")
def get_terrain_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
) -> Dict[str, Any]:
    cache_key = f"analytics-v2:terrain:{workspace_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    now = datetime.utcnow()

    try:
        from app.db.models.discovery import DiscoveryArtist, DiscoveryComputedMetrics
        from app.db.models.artist_event import ArtistEvent
    except ImportError:
        return {"overview": {}, "by_genre": [], "by_zone": [], "by_event_type": {}, "by_source": {}, "by_fee_tier": {}, "timeline": [], "heatmap": [], "funnel": {}}

    # ── Overview KPIs ──
    total_artists = db.query(func.count(DiscoveryArtist.id)).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
    ).scalar() or 0

    total_events = db.query(func.count(ArtistEvent.id)).filter(
        ArtistEvent.workspace_id == workspace_id,
        ArtistEvent.is_deleted == False,
    ).scalar() or 0

    real_events = db.query(func.count(ArtistEvent.id)).filter(
        ArtistEvent.workspace_id == workspace_id,
        ArtistEvent.is_deleted == False,
        ArtistEvent.source == "ticketmaster",
    ).scalar() or 0

    # Contact coverage (artists with at least instagram or spotify URL)
    with_contact = db.query(func.count(DiscoveryArtist.id)).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
        (DiscoveryArtist.instagram_url.isnot(None)) | (DiscoveryArtist.spotify_artist_id.isnot(None)),
    ).scalar() or 0

    # Total estimated budget
    total_budget = (
        db.query(func.sum(DiscoveryComputedMetrics.fee_estimate_max))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.fee_estimate_max.isnot(None),
            DiscoveryComputedMetrics.fee_estimate_max > 0,
        )
        .scalar() or 0
    )

    overview = {
        "total_artists": total_artists,
        "total_events": total_events,
        "real_events": real_events,
        "contact_coverage_pct": round((with_contact / total_artists * 100) if total_artists > 0 else 0),
        "total_budget_estimated": int(total_budget),
    }

    # ── By genre (top 12) ──
    all_artists = db.query(
        DiscoveryArtist.genres,
        DiscoveryComputedMetrics.score,
    ).join(
        DiscoveryComputedMetrics, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id
    ).filter(
        DiscoveryArtist.workspace_id == workspace_id,
        DiscoveryArtist.is_deleted == False,
    ).all()

    genre_data: Dict[str, List[int]] = defaultdict(list)
    for row in all_artists:
        for g in (row.genres or [])[:3]:
            genre_data[g.strip().lower()].append(row.score or 0)

    by_genre = sorted(
        [{"name": g, "count": len(scores), "avg_score": round(sum(scores) / len(scores), 1) if scores else 0}
         for g, scores in genre_data.items()],
        key=lambda x: x["count"], reverse=True,
    )[:12]

    # ── By zone (top 12 cities by event count) ──
    city_stats = (
        db.query(
            ArtistEvent.city,
            func.count(ArtistEvent.id).label("count"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
            ArtistEvent.city.isnot(None),
        )
        .group_by(ArtistEvent.city)
        .order_by(desc("count"))
        .limit(12)
        .all()
    )
    by_zone = []
    for c in city_stats:
        density = "forte" if c.count >= 10 else ("moyenne" if c.count >= 4 else "faible")
        by_zone.append({"city": c.city, "count": c.count, "density": density})

    # ── By event type ──
    type_stats = (
        db.query(
            ArtistEvent.event_type,
            func.count(ArtistEvent.id).label("count"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
        )
        .group_by(ArtistEvent.event_type)
        .all()
    )
    by_event_type = {t.event_type: t.count for t in type_stats}

    # ── By source ──
    source_stats = (
        db.query(
            ArtistEvent.source,
            func.count(ArtistEvent.id).label("count"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
        )
        .group_by(ArtistEvent.source)
        .all()
    )
    by_source = {s.source or "generated": s.count for s in source_stats}

    # ── By fee tier ──
    fee_tiers = {"< 5k": 0, "5-15k": 0, "15-40k": 0, "40-100k": 0, "> 100k": 0}
    fee_rows = (
        db.query(DiscoveryComputedMetrics.fee_estimate_max)
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.fee_estimate_max.isnot(None),
            DiscoveryComputedMetrics.fee_estimate_max > 0,
        )
        .all()
    )
    for (fee,) in fee_rows:
        if fee < 5000:
            fee_tiers["< 5k"] += 1
        elif fee < 15000:
            fee_tiers["5-15k"] += 1
        elif fee < 40000:
            fee_tiers["15-40k"] += 1
        elif fee < 100000:
            fee_tiers["40-100k"] += 1
        else:
            fee_tiers["> 100k"] += 1

    # ── Activity timeline (last 12 months — events per month) ──
    twelve_months_ago = now - timedelta(days=365)
    monthly_events = (
        db.query(
            func.date_trunc("month", ArtistEvent.event_date).label("month"),
            func.count(ArtistEvent.id).label("count"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= twelve_months_ago,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    timeline = [
        {"month": m.month.strftime("%Y-%m") if m.month else "", "count": m.count}
        for m in monthly_events
    ]

    # ── Calendar heatmap (next 12 months) ──
    twelve_months_ahead = now + timedelta(days=365)
    heatmap_data = (
        db.query(
            func.date_trunc("month", ArtistEvent.event_date).label("month"),
            func.count(ArtistEvent.id).label("count"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
            ArtistEvent.event_date <= twelve_months_ahead,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    heatmap = [
        {"month": m.month.strftime("%Y-%m") if m.month else "", "label": m.month.strftime("%b %Y") if m.month else "", "count": m.count}
        for m in heatmap_data
    ]

    # ── Qualification funnel ──
    scored = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(DiscoveryArtist.workspace_id == workspace_id, DiscoveryArtist.is_deleted == False, DiscoveryComputedMetrics.score > 0)
        .scalar() or 0
    )
    with_fee_est = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(DiscoveryArtist.workspace_id == workspace_id, DiscoveryArtist.is_deleted == False, DiscoveryComputedMetrics.fee_estimate_min.isnot(None), DiscoveryComputedMetrics.fee_estimate_min > 0)
        .scalar() or 0
    )
    actionable = (
        db.query(func.count(DiscoveryComputedMetrics.id))
        .join(DiscoveryArtist, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.score >= 60,
            DiscoveryComputedMetrics.fee_estimate_min.isnot(None),
            DiscoveryComputedMetrics.fee_estimate_min > 0,
        )
        .scalar() or 0
    )

    funnel = {
        "detected": total_artists,
        "scored": scored,
        "contact_found": with_contact,
        "fee_estimated": with_fee_est,
        "actionable": actionable,
    }

    result = {
        "overview": overview,
        "by_genre": by_genre,
        "by_zone": by_zone,
        "by_event_type": by_event_type,
        "by_source": by_source,
        "by_fee_tier": fee_tiers,
        "timeline": timeline,
        "heatmap": heatmap,
        "funnel": funnel,
        "generated_at": now.isoformat(),
    }

    cache_set(cache_key, result, ttl=CACHE_TTL)
    return result


# ============================================================================
# COMPETITIVE GAPS — "Où sont les ouvertures ?"
# ============================================================================

@router.get("/competitive-gaps")
def get_competitive_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: int = Depends(get_user_workspace_id),
) -> Dict[str, Any]:
    cache_key = f"analytics-v2:gaps:{workspace_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    now = datetime.utcnow()

    try:
        from app.db.models.discovery import DiscoveryArtist, DiscoveryComputedMetrics
        from app.db.models.artist_event import ArtistEvent
    except ImportError:
        return {"underserved_zones": [], "underrepresented_genres": [], "empty_slots": []}

    # ── Zones with high-scored artists but few events ──
    # Get artists per city (from events)
    events_by_city = dict(
        db.query(ArtistEvent.city, func.count(ArtistEvent.id))
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
            ArtistEvent.city.isnot(None),
        )
        .group_by(ArtistEvent.city)
        .all()
    )

    # Get high-score artists per city (from events history)
    scored_by_city_q = (
        db.query(
            ArtistEvent.city,
            func.count(func.distinct(ArtistEvent.artist_name)).label("artist_count"),
            func.avg(ArtistEvent.artist_score).label("avg_score"),
        )
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.city.isnot(None),
            ArtistEvent.artist_score.isnot(None),
            ArtistEvent.artist_score >= 50,
        )
        .group_by(ArtistEvent.city)
        .all()
    )

    underserved_zones = []
    for row in scored_by_city_q:
        upcoming = events_by_city.get(row.city, 0)
        if upcoming <= 2 and row.artist_count >= 2:
            underserved_zones.append({
                "city": row.city,
                "scored_artists": row.artist_count,
                "avg_score": round(float(row.avg_score or 0), 1),
                "upcoming_events": upcoming,
            })
    underserved_zones.sort(key=lambda x: x["scored_artists"], reverse=True)

    # ── Genres with growth but few events ──
    genre_growth: Dict[str, Dict] = defaultdict(lambda: {"artists": 0, "avg_velocity": 0.0, "velocities": []})
    artist_rows = (
        db.query(
            DiscoveryArtist.genres,
            DiscoveryComputedMetrics.velocity,
        )
        .join(DiscoveryComputedMetrics, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
        .filter(
            DiscoveryArtist.workspace_id == workspace_id,
            DiscoveryArtist.is_deleted == False,
            DiscoveryComputedMetrics.velocity > 0,
        )
        .all()
    )
    for row in artist_rows:
        for g in (row.genres or [])[:3]:
            gn = g.strip().lower()
            genre_growth[gn]["artists"] += 1
            genre_growth[gn]["velocities"].append(row.velocity or 0)

    # Events by genre classification
    genre_events: Dict[str, int] = defaultdict(int)
    event_genres = (
        db.query(ArtistEvent.artist_genres)
        .filter(
            ArtistEvent.workspace_id == workspace_id,
            ArtistEvent.is_deleted == False,
            ArtistEvent.event_date >= now,
        )
        .all()
    )
    for (genres,) in event_genres:
        for g in (genres or [])[:3]:
            genre_events[g.strip().lower()] += 1

    underrepresented_genres = []
    for genre, data in genre_growth.items():
        ev_count = genre_events.get(genre, 0)
        if data["artists"] >= 2 and ev_count <= 1:
            avg_v = sum(data["velocities"]) / len(data["velocities"]) if data["velocities"] else 0
            underrepresented_genres.append({
                "genre": genre,
                "growing_artists": data["artists"],
                "avg_velocity": round(avg_v, 1),
                "upcoming_events": ev_count,
            })
    underrepresented_genres.sort(key=lambda x: x["growing_artists"], reverse=True)

    # ── Empty time slots (months with < 3 events in active cities) ──
    empty_slots = []
    for i in range(12):
        month_start = (now.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        month_label = month_start.strftime("%B %Y")

        city_counts = (
            db.query(ArtistEvent.city, func.count(ArtistEvent.id).label("cnt"))
            .filter(
                ArtistEvent.workspace_id == workspace_id,
                ArtistEvent.is_deleted == False,
                ArtistEvent.event_date >= month_start,
                ArtistEvent.event_date < month_end,
                ArtistEvent.city.isnot(None),
            )
            .group_by(ArtistEvent.city)
            .all()
        )
        active_city_names = {c.city for c in (scored_by_city_q or []) if c.artist_count >= 2}
        for city_name in active_city_names:
            city_ev = next((c.cnt for c in city_counts if c.city == city_name), 0)
            if city_ev == 0:
                empty_slots.append({"month": month_label, "city": city_name})

    empty_slots = empty_slots[:15]

    result = {
        "underserved_zones": underserved_zones[:10],
        "underrepresented_genres": underrepresented_genres[:10],
        "empty_slots": empty_slots,
        "generated_at": now.isoformat(),
    }

    cache_set(cache_key, result, ttl=CACHE_TTL)
    return result
