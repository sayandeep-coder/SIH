from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.config.constants import ADVANCE_DAYS_WINDOWS, INDEX_METHODOLOGY_VERSION
from app.db.repositories.index_repository import IndexRepository
from app.db.repositories.route_repository import RouteRepository
from app.schemas.index import AdvanceWindowsOut, IndexSummaryOut, RouteIndexOut

router = APIRouter(prefix="/api/v1/index", tags=["index"])


def _methodology_version_for_window(advance_days: int) -> str:
    return f"{INDEX_METHODOLOGY_VERSION}-t{advance_days}"


@router.get("", response_model=IndexSummaryOut)
async def get_index(
    date_filter: date | None = Query(default=None, alias="date"),
    session: AsyncSession = Depends(get_session),
) -> IndexSummaryOut:
    """Overall APIx across all advance windows, optionally as-of a specific date."""
    repo = IndexRepository(session)

    advance_windows: dict[int, Decimal] = {}
    latest_index_date: date | None = None
    latest_index_value = Decimal(100)
    latest_base_value = Decimal(100)

    for advance_days in ADVANCE_DAYS_WINDOWS:
        methodology_version = _methodology_version_for_window(advance_days)
        if date_filter is not None:
            values = await repo.get_index_values(
                index_date=date_filter, route_id=None, methodology_version=methodology_version
            )
            overall = values[0] if values else None
        else:
            overall = await repo.get_latest_overall_index(methodology_version)

        if overall is not None:
            advance_windows[advance_days] = overall.index_value
            if latest_index_date is None or overall.index_date > latest_index_date:
                latest_index_date = overall.index_date
                latest_index_value = overall.index_value
                latest_base_value = overall.base_value

    return IndexSummaryOut(
        date=latest_index_date or date_filter or date.today(),
        index=latest_index_value,
        base=latest_base_value,
        advance_windows=advance_windows,
    )


@router.get("/routes", response_model=list[RouteIndexOut])
async def get_route_indexes(
    route_code: str | None = Query(default=None),
    advance_days: int | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[RouteIndexOut]:
    """Per-route index values, optionally filtered to one route and/or one
    advance-booking window.
    """
    repo = IndexRepository(session)
    route_repo = RouteRepository(session)

    route_id: UUID | None = None
    if route_code is not None:
        route = await route_repo.get_by_route_code(route_code)
        if route is None:
            return []
        route_id = route.id

    windows = [advance_days] if advance_days is not None else list(ADVANCE_DAYS_WINDOWS)

    all_values = []
    for window in windows:
        methodology_version = _methodology_version_for_window(window)
        if route_id is not None:
            values = await repo.get_index_values(route_id=route_id, methodology_version=methodology_version)
            values = values[:1]
        else:
            values = await repo.get_latest_route_indexes(methodology_version)
        all_values.extend(values)

    routes_by_id = await route_repo.get_by_ids([v.route_id for v in all_values])

    results: list[RouteIndexOut] = []
    for value in all_values:
        route = routes_by_id.get(value.route_id)
        if route is None:
            continue
        results.append(
            RouteIndexOut(
                route_id=value.route_id,
                route_code=route.route_code,
                index_value=value.index_value,
                base_value=value.base_value,
            )
        )

    return results


@router.get("/advance-windows", response_model=AdvanceWindowsOut)
async def get_advance_windows() -> AdvanceWindowsOut:
    return AdvanceWindowsOut(windows=list(ADVANCE_DAYS_WINDOWS))
