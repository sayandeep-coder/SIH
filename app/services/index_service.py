"""Orchestrates index calculation: pulls fare_observations and index_weights,
aggregates representative fares, computes route + overall indexes, and
persists index_values.

Base period: the earliest available observation date for a given
(route, advance_days) is treated as the base period (index = 100), since
this is the system's first run and no separate base-period table exists.
As more history accumulates, "earliest available" naturally becomes a
fixed historical base rather than a moving one.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ADVANCE_DAYS_WINDOWS, INDEX_METHODOLOGY_VERSION
from app.db.models import IndexValue
from app.db.repositories.index_repository import IndexRepository
from app.index_engine.aggregation import representative_fares
from app.index_engine.calculator import calculate_overall_index

logger = structlog.get_logger(__name__)


def _methodology_version_for_window(advance_days: int) -> str:
    return f"{INDEX_METHODOLOGY_VERSION}-t{advance_days}"


async def calculate_index_for_window(
    session: AsyncSession, advance_days: int, index_date: date | None = None
) -> dict:
    """Calculate and persist route + overall index values for one advance
    window (e.g. T+7). Returns a summary including per-route index values.
    """
    if advance_days not in ADVANCE_DAYS_WINDOWS:
        raise ValueError(f"advance_days must be one of {ADVANCE_DAYS_WINDOWS}, got {advance_days}")

    index_date = index_date or datetime.now(timezone.utc).date()
    repo = IndexRepository(session)

    observations = await repo.get_observations_for_advance_days(advance_days)
    if not observations:
        return {"advance_days": advance_days, "index_date": index_date, "status": "no_data"}

    rows = [
        {
            "route_id": o.route_id,
            "advance_days": o.advance_days,
            "normalized_fare": o.normalized_fare,
            "is_valid": o.is_valid,
            "is_outlier": o.is_outlier,
            "observation_date": o.observation_date,
            "created_at": o.created_at,
        }
        for o in observations
    ]

    current_fares = _latest_representative_fares(rows)
    base_fares = _earliest_representative_fares(rows)

    weights = await repo.get_current_route_weights(index_date)

    result = calculate_overall_index(current_fares, base_fares, weights)

    methodology_version = _methodology_version_for_window(advance_days)

    saved_route_values = []
    for route_result in result.route_indexes:
        index_value = IndexValue(
            index_date=index_date,
            frequency="daily",
            route_id=route_result.route_id,
            index_value=route_result.index_value,
            base_value=Decimal(100),
            sample_size=1,
            methodology_version=methodology_version,
        )
        saved_route_values.append(await repo.save_index_value(index_value))

    overall_value = IndexValue(
        index_date=index_date,
        frequency="daily",
        route_id=None,
        index_value=result.index_value,
        base_value=result.base_value,
        sample_size=result.sample_size,
        methodology_version=methodology_version,
    )
    await repo.save_index_value(overall_value)

    await session.commit()

    logger.info(
        "index_service.window_calculated",
        advance_days=advance_days,
        index_date=index_date.isoformat(),
        overall_index=float(result.index_value),
        routes_included=result.sample_size,
    )

    return {
        "advance_days": advance_days,
        "index_date": index_date,
        "status": "ok",
        "overall_index": result.index_value,
        "sample_size": result.sample_size,
        "routes_included": [r.route_id for r in result.route_indexes],
    }


async def calculate_all_windows(session: AsyncSession, index_date: date | None = None) -> dict:
    """Calculate index values for every advance window (T+1/7/15/30/45)."""
    results = {}
    for advance_days in ADVANCE_DAYS_WINDOWS:
        results[advance_days] = await calculate_index_for_window(session, advance_days, index_date)
    return results


def _latest_representative_fares(rows: list[dict]) -> dict[UUID, Decimal]:
    if not rows:
        return {}
    max_date = max(r["observation_date"] for r in rows)
    latest_rows = [r for r in rows if r["observation_date"] == max_date]
    grouped = representative_fares(latest_rows)
    return {route_id: fare for (route_id, _advance_days), fare in grouped.items()}


def _earliest_representative_fares(rows: list[dict]) -> dict[UUID, Decimal]:
    if not rows:
        return {}
    min_date = min(r["observation_date"] for r in rows)
    earliest_rows = [r for r in rows if r["observation_date"] == min_date]
    grouped = representative_fares(earliest_rows)
    return {route_id: fare for (route_id, _advance_days), fare in grouped.items()}
