import asyncio
from datetime import date, datetime

import structlog

from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal, dispose_engine
from app.services.scraping_service import ScrapingServiceError, run_google_flights_scrape

logger = structlog.get_logger(__name__)


@celery_app.task(name="scrape_google_flights", bind=True, max_retries=0)
def scrape_google_flights(self, route_code: str, departure_date: str) -> dict:
    """Celery entrypoint: scrape one route/date via Google Flights and persist results.

    Args:
        route_code: Route code, e.g. "CCU-BOM".
        departure_date: ISO date string, e.g. "2026-09-16".
    """
    parsed_date = datetime.strptime(departure_date, "%Y-%m-%d").date()

    try:
        result = asyncio.run(_run(route_code, parsed_date))
        return {
            "scrape_run_id": str(result["scrape_run_id"]),
            "status": result["status"],
            "records_found": result["records_found"],
            "records_valid": result["records_valid"],
            "observations_created": result.get("observations_created", 0),
        }
    except ScrapingServiceError:
        logger.error("scraping_tasks.service_error", route_code=route_code, exc_info=True)
        raise
    except Exception:
        logger.error("scraping_tasks.unexpected_error", route_code=route_code, exc_info=True)
        raise


async def _run(route_code: str, departure_date: date) -> dict:
    try:
        async with AsyncSessionLocal() as session:
            return await run_google_flights_scrape(session, route_code, departure_date)
    finally:
        await dispose_engine()
