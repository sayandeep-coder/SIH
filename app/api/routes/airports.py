from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.repositories.airport_repository import AirportRepository
from app.schemas.airport import AirportOut

router = APIRouter(prefix="/api/v1/airports", tags=["airports"])


@router.get("", response_model=list[AirportOut])
async def list_airports(session: AsyncSession = Depends(get_session)) -> list[AirportOut]:
    repo = AirportRepository(session)
    return await repo.list_active()
