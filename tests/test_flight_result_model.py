from datetime import date, time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.scrapers.google_flights.models import FlightResult


def _base_kwargs(**overrides):
    kwargs = dict(
        airline_name="Akasa Air",
        airline_code="qp",
        flight_number="QP1126",
        origin="ccu",
        destination="bom",
        departure_date=date(2026, 9, 16),
        departure_time=time(23, 0),
        arrival_date=date(2026, 9, 17),
        arrival_time=time(1, 40),
        duration_minutes=160,
        stops=0,
        price=Decimal("8463"),
        currency="INR",
        emissions_kg=116.0,
    )
    kwargs.update(overrides)
    return kwargs


def test_valid_flight_result_constructs():
    flight = FlightResult(**_base_kwargs())
    assert flight.price == Decimal("8463")


def test_origin_destination_airline_code_uppercased():
    flight = FlightResult(**_base_kwargs())
    assert flight.origin == "CCU"
    assert flight.destination == "BOM"
    assert flight.airline_code == "QP"


def test_default_source_is_google_flights():
    flight = FlightResult(**_base_kwargs())
    assert flight.source == "google_flights"


def test_negative_price_rejected():
    with pytest.raises(ValidationError):
        FlightResult(**_base_kwargs(price=Decimal("-1")))


def test_zero_price_rejected():
    with pytest.raises(ValidationError):
        FlightResult(**_base_kwargs(price=Decimal("0")))


def test_negative_stops_rejected():
    with pytest.raises(ValidationError):
        FlightResult(**_base_kwargs(stops=-1))


def test_negative_duration_rejected():
    with pytest.raises(ValidationError):
        FlightResult(**_base_kwargs(duration_minutes=-5))


def test_optional_fields_can_be_none():
    flight = FlightResult(
        **_base_kwargs(
            airline_code=None,
            flight_number=None,
            departure_time=None,
            arrival_date=None,
            arrival_time=None,
            duration_minutes=None,
            emissions_kg=None,
        )
    )
    assert flight.airline_code is None
    assert flight.flight_number is None
