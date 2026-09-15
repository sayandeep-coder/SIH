from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.dependencies import get_session
from app.db.models import FareQuote, Route
from app.schemas.fare import FareQuoteOut

router = APIRouter(prefix="/api/v1/fares", tags=["fares"])


@router.get("", response_model=list[FareQuoteOut])
async def list_fares(
    origin: str | None = Query(default=None, description="Origin IATA code"),
    destination: str | None = Query(default=None, description="Destination IATA code"),
    airline: str | None = Query(default=None, description="Airline code"),
    departure_date: date | None = Query(default=None),
    advance_days: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[FareQuoteOut]:
    stmt = (
        select(FareQuote)
        .join(Route, FareQuote.route_id == Route.id)
        .options(joinedload(FareQuote.route), joinedload(FareQuote.airline))
    )

    if origin:
        stmt = stmt.where(Route.origin.has(iata_code=origin.upper()))
    if destination:
        stmt = stmt.where(Route.destination.has(iata_code=destination.upper()))
    if airline:
        stmt = stmt.where(FareQuote.airline.has(code=airline.upper()))
    if departure_date:
        stmt = stmt.where(FareQuote.departure_date == departure_date)
    if advance_days is not None:
        stmt = stmt.where(FareQuote.advance_days == advance_days)

    stmt = stmt.order_by(FareQuote.scraped_at.desc()).limit(limit)

    result = await session.execute(stmt)
    quotes = list(result.scalars().all())

    return [
        FareQuoteOut(
            id=q.id,
            route_id=q.route_id,
            route_code=q.route.route_code,
            airline_id=q.airline_id,
            airline_code=q.airline.code if q.airline else None,
            airline_name=q.airline.name if q.airline else None,
            source=q.source,
            flight_number=q.flight_number,
            departure_date=q.departure_date,
            departure_time=q.departure_time,
            advance_days=q.advance_days,
            total_fare=q.total_fare,
            currency=q.currency,
            availability=q.availability,
            stops=(q.raw_data or {}).get("stops"),
            duration_minutes=(q.raw_data or {}).get("duration_minutes"),
            scraped_at=q.scraped_at,
        )
        for q in quotes
    ]
