from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "apix",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.scraping_tasks",
        "app.tasks.index_tasks",
        "app.scheduler.jobs",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "daily-advance-window-scrape": {
            "task": "schedule_daily_scrapes",
            "schedule": 24 * 60 * 60,  # once a day; simple interval schedule for this milestone
        },
    },
)
