import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.cleaning.normalizer import compute_advance_days
from app.db.models import Airline, DataQualityEvent, FareObservation, FareQuote
from app.scrapers.google_flights.models import FlightResult


class FareRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_airline(self, code: str | None, name: str) -> Airline | None:
        """Resolve an airline by code, inserting it if not yet known.

        The airlines table is seeded separately, but scraped results may
        reference carriers we haven't seeded yet. Auto-upserting keeps the
        pipeline unblocked rather than dropping airline attribution.
        """
        if not code:
            return None

        stmt = select(Airline).where(Airline.code == code.upper())
        result = await self._session.execute(stmt)
        airline = result.scalar_one_or_none()
        if airline is not None:
            return airline

        insert_stmt = (
            pg_insert(Airline)
            .values(code=code.upper(), name=name)
            .on_conflict_do_nothing(index_elements=["code"])
            .returning(Airline)
        )
        result = await self._session.execute(insert_stmt)
        airline = result.scalar_one_or_none()
        if airline is not None:
            return airline

        # Conflicting concurrent insert won the race; fetch the existing row.
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_fare_quote(
        self,
        flight: FlightResult,
        scrape_run_id: uuid.UUID,
        route_id: uuid.UUID,
        airline_id: uuid.UUID | None,
        scrape_date: date,
    ) -> FareQuote:
        actual_advance_days, advance_days = compute_advance_days(flight.departure_date, scrape_date)
        quote = FareQuote(
            scrape_run_id=scrape_run_id,
            route_id=route_id,
            airline_id=airline_id,
            source=flight.source,
            flight_number=flight.flight_number,
            departure_date=flight.departure_date,
            departure_time=flight.departure_time,
            advance_days=advance_days,
            total_fare=flight.price,
            currency=flight.currency,
            availability=True,
            raw_data={
                **flight.model_dump(mode="json"),
                "actual_advance_days": actual_advance_days,
            },
        )
        self._session.add(quote)
        await self._session.flush()
        return quote

    async def get_quotes_by_scrape_run(self, scrape_run_id: uuid.UUID) -> list[FareQuote]:
        stmt = select(FareQuote).where(FareQuote.scrape_run_id == scrape_run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save_fare_observations(self, observations: list[FareObservation]) -> None:
        if not observations:
            return
        self._session.add_all(observations)
        await self._session.flush()

    async def get_already_processed_quote_ids(self, quote_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        """Quote IDs that have already been through cleaning once, whether
        they produced an observation or were rejected as invalid/duplicate.
        A quote rejected as a duplicate never gets a fare_observation, so
        checking observations alone would cause it to be reprocessed (and
        potentially re-flagged as a "new" duplicate) on every cleaning re-run.
        """
        if not quote_ids:
            return set()

        observed_stmt = select(FareObservation.quote_id).where(FareObservation.quote_id.in_(quote_ids))
        observed = set((await self._session.execute(observed_stmt)).scalars().all())

        event_stmt = select(DataQualityEvent.quote_id).where(
            DataQualityEvent.quote_id.in_(quote_ids),
            DataQualityEvent.event_type.in_(["validation_failed", "duplicate_dropped"]),
        )
        rejected = set((await self._session.execute(event_stmt)).scalars().all())

        return observed | rejected
