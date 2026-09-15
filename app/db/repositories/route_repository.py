import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Route


class RouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_route_code(self, route_code: str) -> Route | None:
        stmt = (
            select(Route)
            .options(joinedload(Route.origin), joinedload(Route.destination))
            .where(Route.route_code == route_code.upper())
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, route_id: uuid.UUID) -> Route | None:
        stmt = (
            select(Route)
            .options(joinedload(Route.origin), joinedload(Route.destination))
            .where(Route.id == route_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Route]:
        stmt = (
            select(Route)
            .options(joinedload(Route.origin), joinedload(Route.destination))
            .where(Route.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, route_ids: list[uuid.UUID]) -> dict[uuid.UUID, Route]:
        if not route_ids:
            return {}
        stmt = select(Route).where(Route.id.in_(route_ids))
        result = await self._session.execute(stmt)
        return {route.id: route for route in result.scalars().all()}
