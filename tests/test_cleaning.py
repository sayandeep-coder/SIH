import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

from app.cleaning.deduplicator import dedupe_fare_quotes
from app.cleaning.normalizer import (
    bucket_advance_days,
    compute_advance_days,
    normalize_airline_name,
    normalize_airport_code,
    normalize_currency,
    normalize_price,
)
from app.cleaning.outlier import flag_outliers, flag_outliers_grouped
from app.cleaning.validator import validate_fare_quote
from app.db.models import FareQuote


def _make_quote(**overrides) -> FareQuote:
    defaults = dict(
        id=uuid.uuid4(),
        scrape_run_id=uuid.uuid4(),
        route_id=uuid.uuid4(),
        airline_id=uuid.uuid4(),
        source="google_flights",
        flight_number="QP1126",
        departure_date=date(2026, 9, 16),
        departure_time=time(23, 0),
        advance_days=1,
        total_fare=Decimal("8463"),
        currency="INR",
        availability=True,
        raw_data={"duration_minutes": 160, "stops": 0},
        scraped_at=datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return FareQuote(**defaults)


# --- Validator ---


def test_validator_accepts_clean_quote():
    result = validate_fare_quote(_make_quote())
    assert result.is_valid
    assert result.reasons == []


def test_validator_rejects_missing_route():
    result = validate_fare_quote(_make_quote(route_id=None))
    assert not result.is_valid
    assert "missing_route" in result.reasons


def test_validator_rejects_zero_price():
    result = validate_fare_quote(_make_quote(total_fare=Decimal("0")))
    assert not result.is_valid
    assert "invalid_price" in result.reasons


def test_validator_rejects_negative_price():
    result = validate_fare_quote(_make_quote(total_fare=Decimal("-100")))
    assert not result.is_valid
    assert "invalid_price" in result.reasons


def test_validator_rejects_invalid_currency():
    result = validate_fare_quote(_make_quote(currency="XYZ"))
    assert not result.is_valid
    assert "invalid_currency" in result.reasons


def test_validator_rejects_invalid_duration():
    result = validate_fare_quote(_make_quote(raw_data={"duration_minutes": -5, "stops": 0}))
    assert not result.is_valid
    assert "invalid_duration" in result.reasons


def test_validator_rejects_invalid_stops():
    result = validate_fare_quote(_make_quote(raw_data={"duration_minutes": 160, "stops": 10}))
    assert not result.is_valid
    assert "invalid_stops" in result.reasons


def test_validator_reports_multiple_reasons():
    result = validate_fare_quote(_make_quote(total_fare=Decimal("0"), currency="XYZ"))
    assert not result.is_valid
    assert "invalid_price" in result.reasons
    assert "invalid_currency" in result.reasons


# --- Normalizer ---


def test_bucket_advance_days_exact_matches():
    assert bucket_advance_days(1) == 1
    assert bucket_advance_days(7) == 7
    assert bucket_advance_days(15) == 15
    assert bucket_advance_days(30) == 30
    assert bucket_advance_days(45) == 45


def test_bucket_advance_days_snaps_to_nearest():
    assert bucket_advance_days(3) == 1
    assert bucket_advance_days(10) == 7
    assert bucket_advance_days(20) == 15
    assert bucket_advance_days(37) == 30
    assert bucket_advance_days(100) == 45


def test_bucket_advance_days_floors_at_minimum():
    assert bucket_advance_days(0) == 1
    assert bucket_advance_days(-5) == 1


def test_compute_advance_days_returns_actual_and_bucketed():
    actual, bucketed = compute_advance_days(date(2026, 9, 25), date(2026, 9, 15))
    assert actual == 10
    assert bucketed == 7


def test_normalize_price_rounds_to_two_decimals():
    assert normalize_price(Decimal("100.005")) == Decimal("100.01") or normalize_price(
        Decimal("100.005")
    ) == Decimal("100.00")
    assert normalize_price(Decimal("100.1")) == Decimal("100.10")


def test_normalize_currency_uppercases():
    assert normalize_currency(" inr ") == "INR"


def test_normalize_airline_name_collapses_whitespace():
    assert normalize_airline_name("  Air   India  ") == "Air India"


def test_normalize_airport_code_uppercases():
    assert normalize_airport_code("ccu") == "CCU"


# --- Deduplicator ---


def test_dedupe_removes_exact_duplicates():
    route_id = uuid.uuid4()
    airline_id = uuid.uuid4()
    q1 = _make_quote(
        route_id=route_id,
        airline_id=airline_id,
        scraped_at=datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc),
    )
    q2 = _make_quote(
        route_id=route_id,
        airline_id=airline_id,
        scraped_at=datetime(2026, 9, 15, 11, 0, tzinfo=timezone.utc),
    )
    kept, dropped = dedupe_fare_quotes([q1, q2])
    assert len(kept) == 1
    assert len(dropped) == 1
    assert kept[0].id == q1.id  # earliest scraped_at wins


def test_dedupe_keeps_distinct_flights():
    q1 = _make_quote(flight_number="QP1126")
    q2 = _make_quote(flight_number="6E5183")
    kept, dropped = dedupe_fare_quotes([q1, q2])
    assert len(kept) == 2
    assert len(dropped) == 0


def test_dedupe_empty_list():
    kept, dropped = dedupe_fare_quotes([])
    assert kept == []
    assert dropped == []


# --- Outlier ---


def test_flag_outliers_detects_high_outlier():
    fares = [Decimal(v) for v in [8000, 8100, 8200, 8300, 8400, 50000]]
    flags = flag_outliers(fares)
    assert bool(flags[-1]) is True
    assert all(not f for f in flags[:-1])


def test_flag_outliers_no_outliers_in_tight_cluster():
    fares = [Decimal(v) for v in [8000, 8050, 8100, 8150, 8200]]
    flags = flag_outliers(fares)
    assert all(not f for f in flags)


def test_flag_outliers_below_min_group_size_returns_all_false():
    fares = [Decimal(v) for v in [8000, 50000]]
    flags = flag_outliers(fares)
    assert flags == [False, False]


def test_flag_outliers_grouped_isolates_groups():
    route_a = str(uuid.uuid4())
    route_b = str(uuid.uuid4())
    rows = [
        {"route_id": route_a, "advance_days": 1, "normalized_fare": Decimal(v)}
        for v in [8000, 8100, 8200, 8300, 50000]
    ] + [
        {"route_id": route_b, "advance_days": 1, "normalized_fare": Decimal(v)}
        for v in [5000, 5100, 5200, 5300]
    ]
    flags = flag_outliers_grouped(rows)
    assert bool(flags[4]) is True  # the 50000 in route_a
    assert not any(flags[5:])  # route_b has no outliers and is below iqr==0 or tight cluster


def test_flag_outliers_grouped_empty_input():
    assert flag_outliers_grouped([]) == []
