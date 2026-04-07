"""
Celery tasks for syncing events from multiple sources:
- Ticketmaster Discovery API
- Bandsintown REST API
Runs periodically to fetch real concert/festival data for artists.
"""
import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


def _fetch_events_for_artist(tm, bit, artist_name: str) -> list:
    """Search both Ticketmaster and Bandsintown for an artist, deduplicate."""
    all_events = []
    seen_ids = set()

    # --- Ticketmaster ---
    if tm:
        try:
            tm_events = tm.search_events_for_artist(artist_name, country_code="FR")
            if len(tm_events) < 3:
                intl = tm.search_events_for_artist(artist_name, country_code="")
                for e in intl:
                    if e["external_id"] not in {x["external_id"] for x in tm_events}:
                        tm_events.append(e)
            for e in tm_events:
                seen_ids.add(e["external_id"])
                all_events.append(e)
        except Exception as e:
            logger.warning("  %s TM error: %s", artist_name, e)

    # --- Bandsintown ---
    if bit:
        try:
            bit_events = bit.search_events_for_artist(artist_name)
            for e in bit_events:
                if e["external_id"] not in seen_ids:
                    e["source"] = "bandsintown"
                    seen_ids.add(e["external_id"])
                    all_events.append(e)
        except Exception as e:
            logger.warning("  %s BIT error: %s", artist_name, e)

    return all_events


@celery_app.task(bind=True, name="app.workers.event_sync_tasks.sync_artist_events", max_retries=1)
def sync_artist_events(self, workspace_id: int = None):
    """Sync events from Ticketmaster + Bandsintown for all artists."""

    from app.services.ticketmaster import TicketmasterService
    from app.services.bandsintown import BandsintownService
    from app.db.models.discovery import DiscoveryArtist, DiscoveryComputedMetrics
    from app.db.models.workspace import Workspace
    from app.db.models.artist_snapshot import ArtistSnapshot
    from sqlalchemy import distinct

    # Init sources
    tm = None
    if settings.ticketmaster_api_key:
        try:
            tm = TicketmasterService()
        except Exception:
            logger.warning("Ticketmaster init failed")

    bit = BandsintownService()

    if not tm and not bit:
        return {"status": "skipped", "reason": "no_sources"}

    db = SessionLocal()
    try:
        # Determine workspaces
        if workspace_id:
            workspace_ids = [workspace_id]
        else:
            workspace_ids = [
                w.id for w in db.query(Workspace.id).filter(Workspace.is_active == True).all()
            ]

        total_events = 0

        for ws_id in workspace_ids:
            # --- Collect artist names to search ---
            artist_names = []

            # 1) From discovery_artists
            rows = (
                db.query(
                    DiscoveryArtist.id,
                    DiscoveryArtist.canonical_name,
                    DiscoveryArtist.image_url,
                    DiscoveryArtist.genres,
                    DiscoveryComputedMetrics.score,
                    DiscoveryComputedMetrics.monthly_listeners,
                )
                .outerjoin(DiscoveryComputedMetrics, DiscoveryArtist.id == DiscoveryComputedMetrics.artist_id)
                .filter(
                    DiscoveryArtist.workspace_id == ws_id,
                    DiscoveryArtist.is_deleted == False,
                )
                .order_by(DiscoveryComputedMetrics.score.desc().nullslast())
                .limit(100)
                .all()
            )

            for row in rows:
                if row.canonical_name:
                    artist_names.append({
                        "name": row.canonical_name,
                        "id": str(row.id),
                        "meta": {
                            "name": row.canonical_name,
                            "image_url": row.image_url,
                            "genres": row.genres or [],
                            "score": row.score,
                            "monthly_listeners": row.monthly_listeners,
                        },
                    })

            # 2) Fallback: artist_snapshots
            if not artist_names:
                snapshot_names = (
                    db.query(distinct(ArtistSnapshot.artist_name))
                    .filter(ArtistSnapshot.workspace_id == ws_id)
                    .all()
                )
                for (sname,) in snapshot_names:
                    if sname:
                        artist_names.append({
                            "name": sname,
                            "id": None,
                            "meta": {"name": sname, "image_url": None, "genres": [], "score": None, "monthly_listeners": None},
                        })
                if artist_names:
                    logger.info("Workspace %d: using %d artists from snapshots", ws_id, len(artist_names))

            logger.info("Workspace %d: syncing events for %d artists (TM=%s, BIT=%s)",
                        ws_id, len(artist_names), bool(tm), True)

            # --- Search each artist on all sources ---
            for a in artist_names:
                events = _fetch_events_for_artist(tm, bit, a["name"])
                if events:
                    count = TicketmasterService.upsert_events(
                        db, ws_id, events,
                        artist_id=a["id"],
                        artist_meta=a["meta"],
                    )
                    total_events += count
                    logger.info("  %s: %d events upserted", a["name"], count)

            # --- General France events from Ticketmaster ---
            if tm:
                try:
                    general = tm.search_all_music_events(country_code="FR", pages=2)
                    if general:
                        count = TicketmasterService.upsert_events(db, ws_id, general)
                        total_events += count
                        logger.info("Workspace %d: %d general FR events upserted", ws_id, count)
                except Exception as e:
                    logger.warning("Workspace %d: general events error: %s", ws_id, e)

        return {"status": "ok", "total_events": total_events, "workspaces": len(workspace_ids)}

    except Exception as e:
        logger.error("Event sync failed: %s", e)
        raise self.retry(exc=e, countdown=120)
    finally:
        db.close()


@celery_app.task(name="app.workers.event_sync_tasks.cleanup_past_events")
def cleanup_past_events(days_ago: int = 30):
    """Soft-delete events that are more than N days in the past."""
    from app.db.models.artist_event import ArtistEvent

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days_ago)
        updated = (
            db.query(ArtistEvent)
            .filter(ArtistEvent.event_date < cutoff, ArtistEvent.is_deleted == False)
            .update({"is_deleted": True, "updated_at": datetime.utcnow()})
        )
        db.commit()
        logger.info("Cleaned up %d past events (older than %d days)", updated, days_ago)
        return {"cleaned": updated}
    finally:
        db.close()
