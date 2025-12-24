"""
Celery tasks for background enrichment jobs
Uses Viberate web scraping for social stats
"""
from celery import group
from app.workers.celery_app import celery_app
from app.enrichment.service import ArtistEnrichmentService
from app.enrichment.config import EnrichmentConfig
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize service with Viberate scraping
enrichment_config = EnrichmentConfig(
    viberate_enabled=getattr(settings, 'viberate_enabled', True),
    viberate_request_delay=getattr(settings, 'viberate_request_delay', 1.5)
)

enrichment_service = ArtistEnrichmentService(
    config=enrichment_config,
    spotify_client_id=settings.spotify_client_id,
    spotify_client_secret=settings.spotify_client_secret
)


@celery_app.task(bind=True, max_retries=3)
def enrich_artist_task(self, artist_id: str):
    """
    Background task to enrich a single artist
    
    Usage:
        enrich_artist_task.delay("2pvfGvbL4mouaDY9ZSwUmv")
    """
    try:
        logger.info(f"Starting background enrichment for {artist_id}")
        
        # Run enrichment (async)
        import asyncio
        result = asyncio.run(enrichment_service.enrich(artist_id, force_refresh=True))
        
        # TODO: Store result in database
        
        logger.info(f"Completed enrichment for {artist_id}")
        return {
            "artist_id": artist_id,
            "status": "success",
            "monthly_listeners": result.monthly_listeners.value,
            "label": result.labels.principal
        }
        
    except Exception as e:
        logger.error(f"Error enriching {artist_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True)
def enrich_artists_batch_task(self, artist_ids: list):
    """
    Background task to enrich multiple artists
    
    Usage:
        enrich_artists_batch_task.delay([
            "2pvfGvbL4mouaDY9ZSwUmv",
            "7bXgB6jMjp9ATFy66eO08Z"
        ])
    """
    try:
        logger.info(f"Starting batch enrichment for {len(artist_ids)} artists")
        
        # Create subtasks for each artist
        job = group([
            enrich_artist_task.s(artist_id)
            for artist_id in artist_ids
        ])
        
        result = job.apply_async()
        
        return {
            "batch_id": self.request.id,
            "total_artists": len(artist_ids),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error in batch enrichment: {e}")
        raise


@celery_app.task
def refresh_top_artists_daily():
    """
    Scheduled task to refresh top 100 artists daily
    
    Configure in celery beat:
        'refresh-top-artists': {
            'task': 'app.workers.enrichment_tasks.refresh_top_artists_daily',
            'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        }
    """
    try:
        logger.info("Starting daily top artists refresh")
        
        # TODO: Get top 100 artists from database
        # top_artist_ids = db.query(Artist).order_by(Artist.score.desc()).limit(100).all()
        
        top_artist_ids = [
            "2pvfGvbL4mouaDY9ZSwUmv",  # Gims
            # ... more artists
        ]
        
        # Enqueue batch job
        enrich_artists_batch_task.delay(top_artist_ids)
        
        logger.info(f"Queued refresh for {len(top_artist_ids)} artists")
        return {"status": "queued", "count": len(top_artist_ids)}
        
    except Exception as e:
        logger.error(f"Error in daily refresh: {e}")
        raise


@celery_app.task
def cleanup_old_enrichment_cache():
    """
    Scheduled task to cleanup old cache entries
    
    Configure in celery beat:
        'cleanup-cache': {
            'task': 'app.workers.enrichment_tasks.cleanup_old_enrichment_cache',
            'schedule': crontab(hour=3, minute=0),  # 3 AM daily
        }
    """
    try:
        logger.info("Starting enrichment cache cleanup")
        
        # TODO: Implement Redis cache cleanup
        # Delete keys older than TTL
        
        logger.info("Cache cleanup completed")
        return {"status": "completed"}
        
    except Exception as e:
        logger.error(f"Error in cache cleanup: {e}")
        raise
