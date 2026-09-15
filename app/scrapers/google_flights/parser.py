"""Parses Google Flights search-result HTML into FlightResult objects.

This module is intentionally isolated: if Google changes its results page
markup, only this file (and selectors.py) should need to change. Extraction
prefers semantic signals (aria-label, role, data-* attributes, visible text)
over Google's generated CSS class names, which are unstable across deploys.
"""

import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

import structlog
from bs4 import BeautifulSoup, Tag

from app.scrapers.google_flights.models import FlightResult
from app.scrapers.google_flights.selectors import (
    ARIA_AIRLINE_RE,
    ARIA_ARRIVAL_RE,
    ARIA_DEPARTURE_RE,
    ARIA_DURATION_RE,
    ARIA_PRICE_RE,
    ARIA_STOPS_RE,
    CO2_DATA_ATTR,
    CURRENCY_NAME_TO_CODE,
    FLIGHT_LINK_SELECTOR,
    FLIGHT_NUMBER_DATA_ATTR,
)

logger = structlog.get_logger(__name__)

_STOPS_WORD_TO_COUNT = {
    "nonstop": 0,
    "1 stop": 1,
    "2 stops": 2,
    "3 stops": 3,
}

_MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_flight_cards(
    html: str,
    origin: str,
    destination: str,
    search_departure_date: date,
) -> list[FlightResult]:
    """Extract all flight results from a Google Flights results page.

    Cards that fail to parse are skipped (and logged) rather than aborting
    the whole page — a single malformed card should never drop every other
    valid result.
    """
    soup = BeautifulSoup(html, "lxml")
    links = soup.select(FLIGHT_LINK_SELECTOR)

    results: list[FlightResult] = []
    for link in links:
        aria_label = link.get("aria-label", "")
        if not aria_label or "Select flight" not in aria_label:
            continue

        # The aria-label-bearing element is a near-empty marker div; the
        # actual price/time/CO2/flight-number markup lives in sibling
        # elements under the same result card container, so DOM-lookup
        # fallbacks must search the card, not just this element's descendants.
        card = _find_card_container(link)

        try:
            flight = _parse_single_card(
                card, aria_label, origin, destination, search_departure_date
            )
        except Exception:
            logger.warning(
                "google_flights.parser.card_failed",
                aria_label=aria_label[:200],
                exc_info=True,
            )
            continue

        if flight is not None:
            results.append(flight)

    logger.info(
        "google_flights.parser.completed",
        cards_seen=len(links),
        flights_parsed=len(results),
    )
    return results


def _find_card_container(link: Tag) -> Tag:
    """Walk up to the nearest ancestor <li> result card, if present."""
    parent = link.parent
    while parent is not None and isinstance(parent, Tag):
        if parent.name == "li":
            return parent
        parent = parent.parent
    return link


def _parse_single_card(
    card: Tag,
    aria_label: str,
    origin: str,
    destination: str,
    search_departure_date: date,
) -> FlightResult | None:
    price, currency = _parse_price(card, aria_label)
    if price is None:
        logger.debug("google_flights.parser.no_price", aria_label=aria_label[:200])
        return None

    airline_name = _parse_airline_name(card, aria_label)
    if not airline_name:
        logger.debug("google_flights.parser.no_airline", aria_label=aria_label[:200])
        return None

    stops = _parse_stops(card, aria_label)
    duration_minutes = _parse_duration(card, aria_label)
    departure_time, departure_date = _parse_departure(card, aria_label, search_departure_date)
    arrival_time, arrival_date = _parse_arrival(card, aria_label, search_departure_date)
    emissions_kg = _parse_emissions(card)
    flight_number, airline_code = _parse_flight_number(card, origin, destination)

    return FlightResult(
        airline_name=airline_name,
        airline_code=airline_code,
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        departure_date=departure_date or search_departure_date,
        departure_time=departure_time,
        arrival_date=arrival_date,
        arrival_time=arrival_time,
        duration_minutes=duration_minutes,
        stops=stops,
        price=price,
        currency=currency,
        emissions_kg=emissions_kg,
        source="google_flights",
    )


def _parse_price(link: Tag, aria_label: str) -> tuple[Decimal | None, str]:
    # Prefer the dedicated price element's own aria-label, e.g.
    # aria-label="8463 Indian rupees"
    price_el = link.find(
        "span", attrs={"aria-label": lambda v: bool(v) and _looks_like_price_label(v)}
    )
    if price_el is not None:
        amount, currency = _parse_price_text(price_el["aria-label"])
        if amount is not None:
            return amount, currency

    # Fallback: parse from the aggregate card aria-label,
    # e.g. "From 8463 Indian rupees. ..."
    match = ARIA_PRICE_RE.search(aria_label)
    if match:
        amount, currency = _parse_price_text(f"{match.group(1)} {match.group(2)}")
        if amount is not None:
            return amount, currency

    return None, "INR"


def _looks_like_price_label(value: str) -> bool:
    lowered = value.lower()
    return any(name in lowered for name in CURRENCY_NAME_TO_CODE)


def _parse_price_text(text: str) -> tuple[Decimal | None, str]:
    lowered = text.lower()
    currency = "INR"
    for name, code in CURRENCY_NAME_TO_CODE.items():
        if name in lowered:
            currency = code
            break

    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None, currency
    try:
        return Decimal(digits), currency
    except InvalidOperation:
        return None, currency


def _parse_airline_name(link: Tag, aria_label: str) -> str | None:
    match = ARIA_AIRLINE_RE.search(aria_label)
    if match:
        return match.group(1).strip()

    # Fallback: first plain <span> text near an airline logo <img alt="...">
    img = link.find("img", attrs={"alt": True})
    if img and img.get("alt"):
        return img["alt"].strip()

    return None


def _parse_stops(link: Tag, aria_label: str) -> int:
    stops_el = link.find(
        "span", attrs={"aria-label": lambda v: bool(v) and v.strip().lower().endswith("flight.")}
    )
    text = stops_el["aria-label"] if stops_el is not None else aria_label

    match = ARIA_STOPS_RE.search(text)
    if not match:
        return 0
    return _STOPS_WORD_TO_COUNT.get(match.group(1).strip().lower(), 0)


def _parse_duration(link: Tag, aria_label: str) -> int | None:
    duration_el = link.find(
        "div", attrs={"aria-label": lambda v: bool(v) and "total duration" in v.lower()}
    )
    text = duration_el["aria-label"] if duration_el is not None else aria_label

    match = ARIA_DURATION_RE.search(text)
    if not match:
        return None
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    if hours == 0 and minutes == 0:
        return None
    return hours * 60 + minutes


def _parse_departure(
    link: Tag, aria_label: str, search_departure_date: date
) -> tuple[time | None, date | None]:
    time_el = link.find(
        "span", attrs={"aria-label": lambda v: bool(v) and v.lower().startswith("departure time")}
    )
    if time_el is not None:
        parsed_time = _parse_time_str(time_el["aria-label"])
        if parsed_time is not None:
            return parsed_time, search_departure_date

    match = ARIA_DEPARTURE_RE.search(aria_label)
    if match:
        parsed_time = _parse_time_str(match.group(1))
        parsed_date = _parse_month_day(match.group(2), search_departure_date.year)
        return parsed_time, parsed_date or search_departure_date

    return None, None


def _parse_arrival(
    link: Tag, aria_label: str, search_departure_date: date
) -> tuple[time | None, date | None]:
    time_el = link.find(
        "span", attrs={"aria-label": lambda v: bool(v) and v.lower().startswith("arrival time")}
    )
    if time_el is not None:
        arrival_label = time_el["aria-label"]
        parsed_time = _parse_time_str(arrival_label)
        date_match = re.search(r"on\s+(\w+,\s+\w+\s+\d{1,2})", arrival_label)
        parsed_date = (
            _parse_month_day(date_match.group(1), search_departure_date.year)
            if date_match
            else None
        )
        return parsed_time, parsed_date or search_departure_date

    match = ARIA_ARRIVAL_RE.search(aria_label)
    if match:
        parsed_time = _parse_time_str(match.group(1))
        parsed_date = _parse_month_day(match.group(2), search_departure_date.year)
        return parsed_time, parsed_date or search_departure_date

    return None, None


def _parse_time_str(text: str) -> time | None:
    match = re.search(r"(\d{1,2}):(\d{2})\s?([AP]M)", text, re.IGNORECASE)
    if not match:
        return None
    try:
        parsed = datetime.strptime(
            f"{match.group(1)}:{match.group(2)} {match.group(3).upper()}", "%I:%M %p"
        )
    except ValueError:
        return None
    return parsed.time()


def _parse_month_day(text: str, year: int) -> date | None:
    # e.g. "Wednesday, September 16"
    match = re.search(r"(\w{3})\w*\s+(\d{1,2})", text)
    if not match:
        return None
    month = _MONTH_ABBR.get(match.group(1).lower()[:3])
    if not month:
        return None
    try:
        return date(year, month, int(match.group(2)))
    except ValueError:
        return None


def _parse_emissions(card: Tag) -> float | None:
    co2_el = card.find(attrs={CO2_DATA_ATTR: True})
    grams = co2_el.get(CO2_DATA_ATTR) if co2_el is not None else None
    if not grams:
        return None
    try:
        return round(float(grams) / 1000, 3)
    except ValueError:
        return None


def _parse_flight_number(card: Tag, origin: str, destination: str) -> tuple[str | None, str | None]:
    """Extract flight number only when reliably present in page metadata.

    Never guesses: if no explicit flight-number metadata is found, returns
    (None, None) for the number and lets the airline code be resolved from
    the metadata token when available.
    """
    meta_el = card.find(attrs={FLIGHT_NUMBER_DATA_ATTR: True})
    if meta_el is None:
        return None, None

    # e.g. "https://www.travelimpactmodel.org/lookup/flight?itinerary=CCU-BOM-QP-1126-20260916"
    url_value = meta_el.get(FLIGHT_NUMBER_DATA_ATTR, "")
    match = re.search(r"itinerary=([A-Z0-9-]+)", url_value)
    if not match:
        return None, None

    token = match.group(1)
    # Expected token shape: "CCU-BOM-QP-1126-20260916"
    parts = token.split("-")
    if len(parts) < 4:
        return None, None

    parsed_origin, parsed_destination, airline_code, number = parts[0], parts[1], parts[2], parts[3]
    if parsed_origin.upper() != origin.upper() or parsed_destination.upper() != destination.upper():
        logger.debug(
            "google_flights.parser.flight_number_mismatch",
            token=token,
            expected_origin=origin,
            expected_destination=destination,
        )
        return None, airline_code or None

    return f"{airline_code}{number}", airline_code or None
