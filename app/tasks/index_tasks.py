import asyncio

import structlog

from app.celery_app import celery_app
from app.config.constants import ADVANCE_DAYS_WINDOWS
from app.db.database import AsyncSessionLocal, dispose_engine
from app.services.index_service import calculate_index_for_window

logger = structlog.get_logger(__name__)


@celery_app.task(name="calculate_index_windows", bind=True, max_retries=0)
def calculate_index_windows(self) -> dict:
    """Recalculate route + overall index values for every advance window
    (T+1/7/15/30/45) from whatever fare_observations currently exist.
    """
    try:
        return asyncio.run(_run())
    except Exception:
        logger.error("index_tasks.unexpected_error", exc_info=True)
        raise


async def _run() -> dict:
    try:
        results = {}
        async with AsyncSessionLocal() as session:
            for advance_days in ADVANCE_DAYS_WINDOWS:
                result = await calculate_index_for_window(session, advance_days)
                results[advance_days] = result["status"]
        return results
    finally:
        await dispose_engine()
