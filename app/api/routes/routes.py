from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.repositories.route_repository import RouteRepository
from app.schemas.route import RouteOut

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
async def list_routes(session: AsyncSession = Depends(get_session)) -> list[RouteOut]:
    repo = RouteRepository(session)
    return await repo.list_active()
