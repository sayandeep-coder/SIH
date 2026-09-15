from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Airport


class AirportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_iata_code(self, iata_code: str) -> Airport | None:
        stmt = select(Airport).where(Airport.iata_code == iata_code.upper())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Airport]:
        stmt = select(Airport).where(Airport.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
