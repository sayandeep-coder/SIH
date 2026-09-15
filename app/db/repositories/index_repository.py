import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FareObservation, IndexValue, IndexWeight, Route


class IndexRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_observations_for_advance_days(self, advance_days: int) -> list[FareObservation]:
        stmt = select(FareObservation).where(FareObservation.advance_days == advance_days)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_route_weights(self, as_of: date) -> dict[uuid.UUID, float]:
        """Latest weight per route effective as of the given date."""
        stmt = select(IndexWeight).where(
            IndexWeight.effective_from <= as_of,
            (IndexWeight.effective_to.is_(None)) | (IndexWeight.effective_to >= as_of),
        )
        result = await self._session.execute(stmt)
        weights = result.scalars().all()

        latest_by_route: dict[uuid.UUID, IndexWeight] = {}
        for w in weights:
            existing = latest_by_route.get(w.route_id)
            if existing is None or w.effective_from > existing.effective_from:
                latest_by_route[w.route_id] = w

        return {route_id: w.weight for route_id, w in latest_by_route.items()}

    async def save_index_value(self, index_value: IndexValue) -> IndexValue:
        self._session.add(index_value)
        await self._session.flush()
        return index_value

    async def get_active_routes(self) -> list[Route]:
        stmt = select(Route).where(Route.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_overall_index(
        self, methodology_version: str
    ) -> IndexValue | None:
        """Most recent overall (route_id IS NULL) index value for a window."""
        stmt = (
            select(IndexValue)
            .where(
                IndexValue.route_id.is_(None),
                IndexValue.methodology_version == methodology_version,
            )
            .order_by(IndexValue.index_date.desc(), IndexValue.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_route_indexes(
        self, methodology_version: str
    ) -> list[IndexValue]:
        """Most recent per-route index value (one row per route_id) for a window."""
        stmt = (
            select(IndexValue)
            .where(
                IndexValue.route_id.is_not(None),
                IndexValue.methodology_version == methodology_version,
            )
            .order_by(IndexValue.route_id, IndexValue.index_date.desc(), IndexValue.created_at.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        latest_by_route: dict[uuid.UUID, IndexValue] = {}
        for row in rows:
            if row.route_id not in latest_by_route:
                latest_by_route[row.route_id] = row
        return list(latest_by_route.values())

    async def get_index_values(
        self,
        index_date: date | None = None,
        route_id: uuid.UUID | None = None,
        methodology_version: str | None = None,
    ) -> list[IndexValue]:
        stmt = select(IndexValue)
        if index_date is not None:
            stmt = stmt.where(IndexValue.index_date == index_date)
        if route_id is not None:
            stmt = stmt.where(IndexValue.route_id == route_id)
        if methodology_version is not None:
            stmt = stmt.where(IndexValue.methodology_version == methodology_version)
        stmt = stmt.order_by(IndexValue.index_date.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
