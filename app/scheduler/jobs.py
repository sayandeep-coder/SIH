"""Daily scheduling entrypoint: for every active route, queue a Google
Flights scrape for each advance-booking window (T+1/7/15/30/45), then queue
an index recalculation once scraping has had time to complete.

This task only enqueues work onto Celery/Redis — it never runs Playwright
itself, matching the required architecture:

    Scheduler -> Celery -> Redis -> Celery worker -> Playwright -> DB
"""

import asyncio
from datetime import datetime, timedelta, timezone

import structlog

from app.celery_app import celery_app
from app.config.constants import ADVANCE_DAYS_WINDOWS
from app.db.database import AsyncSessionLocal, dispose_engine
from app.db.repositories.route_repository import RouteRepository
from app.tasks.scraping_tasks import scrape_google_flights

logger = structlog.get_logger(__name__)


@celery_app.task(name="schedule_daily_scrapes", bind=True, max_retries=0)
def schedule_daily_scrapes(self) -> dict:
    """Queue one scrape task per (active route, advance window) pair."""
    route_codes = asyncio.run(_get_active_route_codes())

    today = datetime.now(timezone.utc).date()
    queued = 0

    for route_code in route_codes:
        for advance_days in ADVANCE_DAYS_WINDOWS:
            departure_date = today + timedelta(days=advance_days)
            scrape_google_flights.delay(route_code, departure_date.isoformat())
            queued += 1

    logger.info(
        "scheduler.daily_scrapes_queued",
        routes=len(route_codes),
        windows=len(ADVANCE_DAYS_WINDOWS),
        tasks_queued=queued,
    )

    return {"routes": len(route_codes), "tasks_queued": queued}


async def _get_active_route_codes() -> list[str]:
    try:
        async with AsyncSessionLocal() as session:
            repo = RouteRepository(session)
            routes = await repo.list_active()
            return [r.route_code for r in routes]
    finally:
        await dispose_engine()
