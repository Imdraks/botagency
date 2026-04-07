"""
Celery tasks for syncing Ticketmaster events.
Runs periodically to fetch real concert/festival data for discovered artists.
"""
import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.event_sync_tasks.sync_artist_events", max_retries=1)
def sync_artist_events(self, workspace_id: int = None):
    """Sync Ticketmaster events for all discovered artists in a workspace (or all workspaces)."""

    if not settings.ticketmaster_api_key:
        logger.info("TICKETMASTER_API_KEY not set — skipping event sync")
        return {"status": "skipped", "reason": "no_api_key"}

    from app.services.ticketmaster import TicketmasterService
    from app.db.models.discovery import DiscoveryArtist, DiscoveryComputedMetrics
    from app.db.models.workspace import Workspace

    db = SessionLocal()
    try:
        tm = TicketmasterService()

        # Determine which workspaces to sync
        if workspace_id:
            workspace_ids = [workspace_id]
        else:
            workspace_ids = [
                w.id for w in db.query(Workspace.id).filter(Workspace.is_active == True).all()
            ]

        total_events = 0

        for ws_id in workspace_ids:
            # Get top artists (by score) for this workspace
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
                .limit(100)  # Top 100 artists per workspace
                .all()
            )

            logger.info("Workspace %d: syncing events for %d artists", ws_id, len(rows))

            for row in rows:
                artist_name = row.canonical_name
                if not artist_name:
                    continue

                artist_meta = {
                    "name": artist_name,
                    "image_url": row.image_url,
                    "genres": row.genres or [],
                    "score": row.score,
                    "monthly_listeners": row.monthly_listeners,
                }

                try:
                    events = tm.search_events_for_artist(artist_name, country_code="FR")
                    # Also search without country filter for international events
                    if len(events) < 3:
                        intl = tm.search_events_for_artist(artist_name, country_code="")
                        seen = {e["external_id"] for e in events}
                        for e in intl:
                            if e["external_id"] not in seen:
                                events.append(e)

                    if events:
                        count = TicketmasterService.upsert_events(
                            db,
                            ws_id,
                            events,
                            artist_id=str(row.id),
                            artist_meta=artist_meta,
                        )
                        total_events += count
                        logger.info("  %s: %d events upserted", artist_name, count)
                except Exception as e:
                    logger.warning("  %s: error fetching events: %s", artist_name, e)
                    continue

            # Also fetch general music events in France (catches events not matched to specific artists)
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
