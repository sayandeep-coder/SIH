"""Google Flights deeplink generator.

Builds a Google Flights search URL from a route and date. Google Flights
resolves the human-readable ``q`` query (e.g. "Flights from CCU to BOM on
2026-09-16") server-side into an origin/destination/date search, which means
we don't have to maintain our own IATA -> Google Knowledge Graph MID mapping
(the format used internally by Google Flights' ``tfs`` protobuf parameter).
"""

from datetime import date, datetime
from urllib.parse import urlencode

from app.config.constants import CabinClass, TripType
from app.config.settings import settings

_CABIN_QUERY_TERMS: dict[CabinClass, str] = {
    CabinClass.ECONOMY: "economy",
    CabinClass.PREMIUM_ECONOMY: "premium economy",
    CabinClass.BUSINESS: "business class",
    CabinClass.FIRST: "first class",
}


def _coerce_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def generate_deeplink(
    origin: str,
    destination: str,
    departure_date: date | str,
    return_date: date | str | None = None,
    passengers: int = 1,
    cabin: CabinClass = CabinClass.ECONOMY,
    trip_type: TripType = TripType.ONE_WAY,
) -> str:
    """Build a Google Flights search URL for the given route and date.

    Args:
        origin: Origin IATA code, e.g. "CCU".
        destination: Destination IATA code, e.g. "BOM".
        departure_date: Departure date (date object or "YYYY-MM-DD" string).
        return_date: Return date, required when trip_type is ROUND_TRIP.
        passengers: Number of adult passengers.
        cabin: Cabin class.
        trip_type: ONE_WAY or ROUND_TRIP.

    Returns:
        A fully-qualified Google Flights search URL.
    """
    origin = origin.strip().upper()
    destination = destination.strip().upper()
    dep_date = _coerce_date(departure_date)

    if trip_type == TripType.ROUND_TRIP and return_date is None:
        raise ValueError("return_date is required for round-trip searches")

    query = f"Flights from {origin} to {destination} on {dep_date.isoformat()}"
    if trip_type == TripType.ROUND_TRIP and return_date is not None:
        ret_date = _coerce_date(return_date)
        query += f" through {ret_date.isoformat()}"

    cabin_term = _CABIN_QUERY_TERMS.get(cabin)
    if cabin_term and cabin != CabinClass.ECONOMY:
        query += f" {cabin_term}"

    if passengers > 1:
        query += f" for {passengers} passengers"

    params = {
        "q": query,
        "hl": settings.google_flights_language,
        "gl": settings.google_flights_country,
        "curr": "INR" if settings.google_flights_country == "IN" else "USD",
    }

    return f"{settings.google_flights_base_url}?{urlencode(params)}"
