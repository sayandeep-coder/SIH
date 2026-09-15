from datetime import date

import pytest

from app.config.constants import CabinClass, TripType
from app.scrapers.google_flights.deeplink import generate_deeplink


def test_generate_deeplink_basic():
    url = generate_deeplink(origin="CCU", destination="BOM", departure_date="2026-09-16")

    assert url.startswith("https://www.google.com/travel/flights/search?")
    assert "Flights+from+CCU+to+BOM+on+2026-09-16" in url or "Flights%20from%20CCU%20to%20BOM%20on%202026-09-16" in url


def test_generate_deeplink_accepts_date_object():
    url = generate_deeplink(origin="ccu", destination="bom", departure_date=date(2026, 9, 16))

    assert "CCU" in url
    assert "BOM" in url
    assert "2026-09-16" in url


def test_generate_deeplink_includes_locale_params():
    url = generate_deeplink(origin="CCU", destination="BOM", departure_date="2026-09-16")

    assert "hl=en" in url
    assert "gl=IN" in url


def test_generate_deeplink_round_trip_requires_return_date():
    with pytest.raises(ValueError):
        generate_deeplink(
            origin="CCU",
            destination="BOM",
            departure_date="2026-09-16",
            trip_type=TripType.ROUND_TRIP,
        )


def test_generate_deeplink_round_trip_includes_return_date():
    url = generate_deeplink(
        origin="CCU",
        destination="BOM",
        departure_date="2026-09-16",
        return_date="2026-09-20",
        trip_type=TripType.ROUND_TRIP,
    )

    assert "2026-09-20" in url


def test_generate_deeplink_business_cabin_reflected_in_query():
    url = generate_deeplink(
        origin="CCU",
        destination="BOM",
        departure_date="2026-09-16",
        cabin=CabinClass.BUSINESS,
    )

    assert "business" in url.lower()


def test_generate_deeplink_multiple_passengers_reflected_in_query():
    url = generate_deeplink(
        origin="CCU",
        destination="BOM",
        departure_date="2026-09-16",
        passengers=3,
    )

    assert "3" in url
