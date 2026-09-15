from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.db.models import DataQualityEvent, FareObservation, FareQuote
from app.schemas.quality import DataQualityEventOut, DataQualitySummaryOut

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])


@router.get("/events", response_model=list[DataQualityEventOut])
async def list_quality_events(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[DataQualityEventOut]:
    stmt = select(DataQualityEvent).order_by(DataQualityEvent.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/summary", response_model=DataQualitySummaryOut)
async def get_quality_summary(session: AsyncSession = Depends(get_session)) -> DataQualitySummaryOut:
    total_quotes = (await session.execute(select(func.count()).select_from(FareQuote))).scalar_one()
    total_observations = (
        await session.execute(select(func.count()).select_from(FareObservation))
    ).scalar_one()
    valid_observations = (
        await session.execute(
            select(func.count()).select_from(FareObservation).where(FareObservation.is_valid.is_(True))
        )
    ).scalar_one()
    outlier_observations = (
        await session.execute(
            select(func.count()).select_from(FareObservation).where(FareObservation.is_outlier.is_(True))
        )
    ).scalar_one()
    duplicate_events = (
        await session.execute(
            select(func.count())
            .select_from(DataQualityEvent)
            .where(DataQualityEvent.event_type == "duplicate_dropped")
        )
    ).scalar_one()
    validation_failed_events = (
        await session.execute(
            select(func.count())
            .select_from(DataQualityEvent)
            .where(DataQualityEvent.event_type == "validation_failed")
        )
    ).scalar_one()

    valid_rate = (valid_observations / total_observations) if total_observations else 0.0
    outlier_rate = (outlier_observations / total_observations) if total_observations else 0.0

    return DataQualitySummaryOut(
        total_quotes=total_quotes,
        total_observations=total_observations,
        valid_observations=valid_observations,
        outlier_observations=outlier_observations,
        valid_rate=round(valid_rate, 4),
        outlier_rate=round(outlier_rate, 4),
        duplicate_events=duplicate_events,
        validation_failed_events=validation_failed_events,
    )
