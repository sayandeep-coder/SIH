import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ScrapeRun


class ScrapeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(self, source: str, metadata: dict | None = None) -> ScrapeRun:
        run = ScrapeRun(source=source, status="running", run_metadata=metadata or {})
        self._session.add(run)
        await self._session.flush()
        return run

    async def mark_success(self, run: ScrapeRun, records_found: int, records_valid: int) -> None:
        run.status = "success"
        run.records_found = records_found
        run.records_valid = records_valid
        run.completed_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def mark_failed(self, run: ScrapeRun, error_message: str) -> None:
        run.status = "failed"
        run.error_message = error_message
        run.completed_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def get_by_id(self, run_id: uuid.UUID) -> ScrapeRun | None:
        stmt = select(ScrapeRun).where(ScrapeRun.id == run_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 50) -> list[ScrapeRun]:
        stmt = select(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
