"""Validates raw fare_quotes before they're promoted to fare_observations.

Raw fare_quotes are never mutated or deleted here — validation only decides
whether a quote is eligible to produce an observation, and records rejection
reasons as data_quality_events for auditability.
"""

from dataclasses import dataclass

from app.db.models import FareQuote

VALID_CURRENCIES = {"INR", "USD", "EUR"}
MAX_REASONABLE_DURATION_MINUTES = 24 * 60  # a single-leg domestic/international flight
MAX_REASONABLE_STOPS = 3


@dataclass
class ValidationResult:
    is_valid: bool
    reasons: list[str]


def validate_fare_quote(quote: FareQuote) -> ValidationResult:
    """Check a single fare_quote for the defects that should exclude it from
    fare_observations. Returns every failing reason, not just the first.
    """
    reasons: list[str] = []

    if quote.route_id is None:
        reasons.append("missing_route")

    if quote.total_fare is None or quote.total_fare <= 0:
        reasons.append("invalid_price")

    if not quote.currency or quote.currency.upper() not in VALID_CURRENCIES:
        reasons.append("invalid_currency")

    if quote.departure_date is None:
        reasons.append("invalid_departure_date")

    raw_data = quote.raw_data or {}

    duration_minutes = raw_data.get("duration_minutes")
    if duration_minutes is not None and (
        duration_minutes <= 0 or duration_minutes > MAX_REASONABLE_DURATION_MINUTES
    ):
        reasons.append("invalid_duration")

    stops = raw_data.get("stops")
    if stops is not None and (stops < 0 or stops > MAX_REASONABLE_STOPS):
        reasons.append("invalid_stops")

    return ValidationResult(is_valid=not reasons, reasons=reasons)
