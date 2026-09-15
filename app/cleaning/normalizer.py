"""Normalizes raw FlightResult/fare_quotes data into consistent, comparable
values before it becomes a fare_observation: currency, price precision,
airline/airport code casing, and advance_days bucketing.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.config.constants import ADVANCE_DAYS_WINDOWS


def bucket_advance_days(actual_days: int) -> int:
    """Snap an actual scrape-to-departure gap to the nearest allowed
    advance-booking window (1/7/15/30/45).

    Both fare_quotes and fare_observations have a DB check constraint
    restricting advance_days to these exact values, so the gap computed from
    the real scrape date is always bucketed rather than stored as-is. We
    never hardcode the bucket from what the scraper was *asked* for — this
    is derived from the actual dates each time it's called.
    """
    clamped = max(actual_days, ADVANCE_DAYS_WINDOWS[0])
    return min(ADVANCE_DAYS_WINDOWS, key=lambda bucket: abs(bucket - clamped))


def compute_advance_days(departure_date: date, scrape_date: date) -> tuple[int, int]:
    """Returns (actual_days, bucketed_days) for a departure relative to the
    date it was actually scraped/observed.
    """
    actual_days = (departure_date - scrape_date).days
    return actual_days, bucket_advance_days(actual_days)


def normalize_price(amount: Decimal) -> Decimal:
    """Round to 2 decimal places (currency minor unit) using standard
    rounding, matching the NUMERIC columns' expected precision.
    """
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_currency(currency: str) -> str:
    return currency.strip().upper()


def normalize_airline_name(name: str) -> str:
    return " ".join(name.strip().split())


def normalize_airport_code(code: str) -> str:
    return code.strip().upper()
