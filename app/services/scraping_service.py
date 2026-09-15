"""Orchestrates a Google Flights scrape: run tracking, scraping, validation,
persistence, and failure recording. Contains no SQL — all persistence goes
through the repositories.
"""

from datetime import date, datetime, timezone

import structlog
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SOURCE_GOOGLE_FLIGHTS
from app.db.models import DataQualityEvent, FareQuote
from app.db.repositories.fare_repository import FareRepository
from app.db.repositories.route_repository import RouteRepository
from app.db.repositories.scrape_repository import ScrapeRepository
from app.scrapers.google_flights.deeplink import generate_deeplink
from app.scrapers.google_flights.models import FlightResult
from app.scrapers.google_flights.scraper import GoogleFlightsScraperError, scrape_google_flights
from app.services.cleaning_service import clean_scrape_run

logger = structlog.get_logger(__name__)


class ScrapingServiceError(Exception):
    """Raised when the scrape cannot be completed for a route."""


async def run_google_flights_scrape(
    session: AsyncSession,
    route_code: str,
    departure_date: date,
) -> dict:
    """Run a full scrape for one route and persist the results.

    Returns a summary dict with scrape_run_id, status, and counts.
    """
    route_repo = RouteRepository(session)
    scrape_repo = ScrapeRepository(session)
    fare_repo = FareRepository(session)

    route = await route_repo.get_by_route_code(route_code)
    if route is None:
        raise ScrapingServiceError(f"Unknown route_code: {route_code}")

    scrape_run = await scrape_repo.create_run(
        source=SOURCE_GOOGLE_FLIGHTS,
        metadata={"route_code": route.route_code, "departure_date": departure_date.isoformat()},
    )
    await session.commit()

    try:
        deeplink = generate_deeplink(
            origin=route.origin.iata_code,
            destination=route.destination.iata_code,
            departure_date=departure_date,
        )

        raw_results = await scrape_google_flights(
            deeplink=deeplink,
            origin=route.origin.iata_code,
            destination=route.destination.iata_code,
            departure_date=departure_date,
        )

        valid_results, invalid_count = _validate_results(raw_results)

        saved_quotes: list[FareQuote] = []
        for flight in valid_results:
            airline = await fare_repo.get_or_create_airline(flight.airline_code, flight.airline_name)
            quote = await fare_repo.save_fare_quote(
                flight=flight,
                scrape_run_id=scrape_run.id,
                route_id=route.id,
                airline_id=airline.id if airline else None,
                scrape_date=datetime.now(timezone.utc).date(),
            )
            saved_quotes.append(quote)

        if invalid_count:
            session.add(
                DataQualityEvent(
                    event_type="parse_validation_failed",
                    severity="warning",
                    message=f"{invalid_count} flight result(s) failed validation and were dropped",
                    event_metadata={"route_code": route.route_code, "scrape_run_id": str(scrape_run.id)},
                )
            )

        await scrape_repo.mark_success(
            scrape_run, records_found=len(raw_results), records_valid=len(saved_quotes)
        )
        await session.commit()

        cleaning_result = await clean_scrape_run(session, scrape_run.id)

        logger.info(
            "scraping_service.completed",
            route_code=route.route_code,
            scrape_run_id=str(scrape_run.id),
            records_found=len(raw_results),
            records_valid=len(saved_quotes),
            observations_created=cleaning_result["observations_created"],
        )

        return {
            "scrape_run_id": scrape_run.id,
            "status": "success",
            "records_found": len(raw_results),
            "records_valid": len(saved_quotes),
            "observations_created": cleaning_result["observations_created"],
            "flights": valid_results,
        }

    except (GoogleFlightsScraperError, ScrapingServiceError) as exc:
        await _record_failure(session, scrape_repo, scrape_run, str(exc))
        raise
    except Exception as exc:
        await _record_failure(session, scrape_repo, scrape_run, f"Unexpected error: {exc}")
        raise


async def _record_failure(
    session: AsyncSession, scrape_repo: ScrapeRepository, scrape_run, message: str
) -> None:
    logger.error("scraping_service.failed", scrape_run_id=str(scrape_run.id), error=message)
    await scrape_repo.mark_failed(scrape_run, message)
    await session.commit()


def _validate_results(raw_results: list[FlightResult]) -> tuple[list[FlightResult], int]:
    """FlightResult objects are already Pydantic-validated on construction by
    the parser; this re-validates defensively in case results were built
    from partially-trusted intermediate data.
    """
    valid: list[FlightResult] = []
    invalid_count = 0
    for result in raw_results:
        try:
            FlightResult.model_validate(result.model_dump())
            valid.append(result)
        except ValidationError:
            logger.warning("scraping_service.invalid_flight_result", exc_info=True)
            invalid_count += 1
    return valid, invalid_count
