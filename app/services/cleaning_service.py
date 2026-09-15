"""Orchestrates the cleaning pipeline: validate -> normalize -> dedupe ->
outlier-flag -> persist fare_observations. Raw fare_quotes are never
mutated; every rejection/flag is recorded as a data_quality_event.
"""

import uuid
from datetime import date, datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.cleaning.deduplicator import dedupe_fare_quotes
from app.cleaning.normalizer import (
    compute_advance_days,
    normalize_currency,
    normalize_price,
)
from app.cleaning.outlier import flag_outliers_grouped
from app.cleaning.validator import validate_fare_quote
from app.db.models import DataQualityEvent, FareObservation, FareQuote
from app.db.repositories.fare_repository import FareRepository

logger = structlog.get_logger(__name__)


async def clean_scrape_run(session: AsyncSession, scrape_run_id: uuid.UUID) -> dict:
    """Run the full cleaning pipeline for every fare_quote produced by one
    scrape_run, writing fare_observations and data_quality_events.

    Idempotent: quotes that already have an observation are skipped, so
    re-running cleaning for the same scrape_run is safe.
    """
    fare_repo = FareRepository(session)

    quotes = await fare_repo.get_quotes_by_scrape_run(scrape_run_id)
    if not quotes:
        return {"scrape_run_id": scrape_run_id, "observations_created": 0, "quotes_seen": 0}

    already_processed = await fare_repo.get_already_processed_quote_ids([q.id for q in quotes])
    pending = [q for q in quotes if q.id not in already_processed]

    valid_quotes, quality_events = _validate(pending)
    kept_quotes, dropped_duplicates = dedupe_fare_quotes(valid_quotes)
    quality_events.extend(_duplicate_events(dropped_duplicates))

    observations = _build_observations(kept_quotes)
    _apply_outlier_flags(observations)

    session.add_all(quality_events)
    await fare_repo.save_fare_observations(observations)
    await session.commit()

    logger.info(
        "cleaning_service.completed",
        scrape_run_id=str(scrape_run_id),
        quotes_seen=len(quotes),
        already_processed=len(already_processed),
        invalid=len(pending) - len(valid_quotes),
        duplicates=len(dropped_duplicates),
        observations_created=len(observations),
        outliers_flagged=sum(1 for o in observations if o.is_outlier),
    )

    return {
        "scrape_run_id": scrape_run_id,
        "quotes_seen": len(quotes),
        "observations_created": len(observations),
        "invalid_dropped": len(pending) - len(valid_quotes),
        "duplicates_dropped": len(dropped_duplicates),
        "outliers_flagged": sum(1 for o in observations if o.is_outlier),
    }


def _validate(quotes: list[FareQuote]) -> tuple[list[FareQuote], list[DataQualityEvent]]:
    valid: list[FareQuote] = []
    events: list[DataQualityEvent] = []
    for quote in quotes:
        result = validate_fare_quote(quote)
        if result.is_valid:
            valid.append(quote)
        else:
            events.append(
                DataQualityEvent(
                    quote_id=quote.id,
                    event_type="validation_failed",
                    severity="warning",
                    message=f"Fare quote failed validation: {', '.join(result.reasons)}",
                    event_metadata={"reasons": result.reasons},
                )
            )
    return valid, events


def _duplicate_events(dropped: list[FareQuote]) -> list[DataQualityEvent]:
    return [
        DataQualityEvent(
            quote_id=quote.id,
            event_type="duplicate_dropped",
            severity="info",
            message="Fare quote is a duplicate of an earlier-scraped quote in the same run",
            event_metadata={},
        )
        for quote in dropped
    ]


def _build_observations(quotes: list[FareQuote]) -> list[FareObservation]:
    scrape_date = datetime.now(timezone.utc).date()
    observations = []
    for quote in quotes:
        actual_advance_days, advance_days = compute_advance_days(
            quote.departure_date, _quote_scrape_date(quote, scrape_date)
        )
        observations.append(
            FareObservation(
                quote_id=quote.id,
                route_id=quote.route_id,
                airline_id=quote.airline_id,
                observation_date=quote.departure_date,
                advance_days=advance_days,
                normalized_fare=normalize_price(quote.total_fare),
                base_fare=quote.base_fare,
                taxes=quote.taxes,
                udf=quote.udf,
                convenience_fee=quote.convenience_fee,
                other_fees=quote.other_fees,
                is_outlier=False,
                is_valid=True,
            )
        )
        # normalize_currency is applied at read-time via quote.currency;
        # fare_observations has no currency column (inherits from fare_quotes
        # via quote_id), so we only validate/normalize it here defensively.
        normalize_currency(quote.currency)
    return observations


def _quote_scrape_date(quote: FareQuote, fallback: date) -> date:
    """Prefer the actual scraped_at date recorded on the quote over "today",
    so cleaning re-runs later still bucket advance_days the same way the
    scrape did.
    """
    if quote.scraped_at is not None:
        return quote.scraped_at.date()
    return fallback


def _apply_outlier_flags(observations: list[FareObservation]) -> None:
    if not observations:
        return
    rows = [
        {
            "route_id": str(o.route_id),
            "advance_days": o.advance_days,
            "normalized_fare": o.normalized_fare,
        }
        for o in observations
    ]
    flags = flag_outliers_grouped(rows)
    for observation, is_outlier in zip(observations, flags):
        observation.is_outlier = bool(is_outlier)
