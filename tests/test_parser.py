from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest

from app.scrapers.google_flights.parser import (
    _parse_duration,
    _parse_price_text,
    _parse_stops,
    parse_flight_cards,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "google_flights_ccu_bom.html"
SEARCH_DATE = date(2026, 9, 16)


@pytest.fixture(scope="module")
def fixture_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed_flights(fixture_html):
    return parse_flight_cards(fixture_html, origin="CCU", destination="BOM", search_departure_date=SEARCH_DATE)


def test_parses_three_valid_flights(parsed_flights):
    # A 4th malformed card (missing price) is present in the fixture and
    # must be skipped without crashing the rest of the parse.
    assert len(parsed_flights) == 3


def test_airline_names(parsed_flights):
    names = {f.airline_name for f in parsed_flights}
    assert names == {"Akasa Air", "IndiGo", "Air India"}


def test_airline_codes(parsed_flights):
    by_name = {f.airline_name: f.airline_code for f in parsed_flights}
    assert by_name["Akasa Air"] == "QP"
    assert by_name["IndiGo"] == "6E"
    assert by_name["Air India"] == "AI"


def test_origin_destination(parsed_flights):
    for flight in parsed_flights:
        assert flight.origin == "CCU"
        assert flight.destination == "BOM"


def test_prices_and_currency(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].price == Decimal("8463")
    assert by_name["IndiGo"].price == Decimal("8850")
    assert by_name["Air India"].price == Decimal("8851")

    for flight in parsed_flights:
        assert flight.currency == "INR"


def test_departure_times(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].departure_time == time(23, 0)
    assert by_name["IndiGo"].departure_time == time(9, 15)
    assert by_name["Air India"].departure_time == time(10, 30)


def test_arrival_times(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].arrival_time == time(1, 40)
    assert by_name["IndiGo"].arrival_time == time(11, 45)
    assert by_name["Air India"].arrival_time == time(13, 35)


def test_overnight_arrival_rolls_to_next_day(parsed_flights):
    akasa = next(f for f in parsed_flights if f.airline_name == "Akasa Air")

    assert akasa.departure_date == date(2026, 9, 16)
    assert akasa.arrival_date == date(2026, 9, 17)


def test_same_day_arrival_date(parsed_flights):
    indigo = next(f for f in parsed_flights if f.airline_name == "IndiGo")

    assert indigo.departure_date == date(2026, 9, 16)
    assert indigo.arrival_date == date(2026, 9, 16)


def test_duration_converted_to_minutes(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].duration_minutes == 160
    assert by_name["IndiGo"].duration_minutes == 150
    assert by_name["Air India"].duration_minutes == 185


def test_nonstop_detection(parsed_flights):
    for flight in parsed_flights:
        assert flight.stops == 0


def test_emissions_converted_to_kg(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].emissions_kg == pytest.approx(116.0)
    assert by_name["IndiGo"].emissions_kg == pytest.approx(119.0)
    assert by_name["Air India"].emissions_kg == pytest.approx(138.0)


def test_flight_numbers_from_metadata(parsed_flights):
    by_name = {f.airline_name: f for f in parsed_flights}

    assert by_name["Akasa Air"].flight_number == "QP1126"
    assert by_name["IndiGo"].flight_number == "6E5183"
    assert by_name["Air India"].flight_number == "AI2772"


def test_source_is_google_flights(parsed_flights):
    for flight in parsed_flights:
        assert flight.source == "google_flights"


def test_malformed_card_does_not_crash_parser(fixture_html):
    # The fixture's 4th card has no parseable price and must be silently
    # skipped rather than raising or corrupting the other results.
    results = parse_flight_cards(fixture_html, origin="CCU", destination="BOM", search_departure_date=SEARCH_DATE)
    assert all(f.airline_name != "SpiceJet" for f in results)


def test_parse_flight_cards_returns_empty_list_for_empty_html():
    assert parse_flight_cards("<html><body></body></html>", "CCU", "BOM", SEARCH_DATE) == []


def test_parse_price_text_handles_thousands_separator():
    amount, currency = _parse_price_text("8,463 Indian rupees")
    assert amount == Decimal("8463")
    assert currency == "INR"


def test_parse_price_text_returns_none_for_unparseable_text():
    amount, _ = _parse_price_text("Price unavailable")
    assert amount is None


def test_parse_stops_nonstop():
    from bs4 import BeautifulSoup

    html = '<div class="card"><span aria-label="Nonstop flight.">Nonstop</span></div>'
    tag = BeautifulSoup(html, "lxml").find("div", class_="card")
    assert _parse_stops(tag, "Nonstop flight with Akasa Air.") == 0


def test_parse_duration_hours_and_minutes():
    from bs4 import BeautifulSoup

    html = '<div class="card"><div aria-label="Total duration 2 hr 40 min.">2 hr 40 min</div></div>'
    tag = BeautifulSoup(html, "lxml").find("div", class_="card")
    assert _parse_duration(tag, "") == 160
