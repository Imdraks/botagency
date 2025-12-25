"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "opportunities_radar",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks", "app.workers.collection_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Email ingestion every 5 minutes
    "ingest-emails": {
        "task": "app.workers.tasks.run_email_ingestion",
        "schedule": crontab(minute=f"*/{settings.imap_poll_interval_minutes}"),
    },
    # Web ingestion every 6 hours
    "ingest-web-sources": {
        "task": "app.workers.tasks.run_web_ingestion",
        "schedule": crontab(
            minute="0",
            hour=f"*/{settings.ingestion_web_interval_hours}"
        ),
    },
    # Check for notifications every 15 minutes
    "check-notifications": {
        "task": "app.workers.tasks.check_and_send_notifications",
        "schedule": crontab(minute="*/15"),
    },
}
