"""Semantic selectors for the Google Flights results page.

Google regenerates its CSS class names (e.g. ``gQ6yfe``, ``yR1fYc``, ``x8klId``)
across deploys, so they are unreliable for scraping. Instead we anchor on
attributes that carry meaning and are unlikely to change: ``aria-label``,
``role``, and visible text patterns. CSS classes are used only as a last
resort for coarse structural navigation (e.g. "find list items"), never to
identify what a field *means*.
"""

import re

# Structural: a flight result card. Google Flights renders each result as a
# list item; the clickable element inside carries the full aria-label summary
# ending in "Select flight". We filter on that suffix (rather than a bare
# [role='link'][aria-label] selector) because the page also has other
# role=link/aria-label elements in its nav chrome (e.g. an "Explore" tab)
# that would otherwise match first and never resolve to an actual result.
FLIGHT_CARD_SELECTOR = "li"
FLIGHT_LINK_SELECTOR = "[role='link'][aria-label*='Select flight']"

# Regex patterns applied against the card's full aria-label summary, e.g.:
# "From 8463 Indian rupees. Nonstop flight with Akasa Air. Leaves ... at
#  11:00 PM on Wednesday, September 16 and arrives at ... Mumbai at 1:40 AM
#  on Thursday, September 17. Total duration 2 hr 40 min. Select flight"
ARIA_PRICE_RE = re.compile(r"From\s+([\d,]+)\s+([A-Za-z ]+?)\.", re.IGNORECASE)
ARIA_STOPS_RE = re.compile(
    r"\b(Nonstop|1 stop|2 stops|3 stops)\s+flight\b", re.IGNORECASE
)
ARIA_AIRLINE_RE = re.compile(r"flight with ([^.]+?)\.", re.IGNORECASE)
ARIA_DURATION_RE = re.compile(
    r"Total duration\s+(?:(\d+)\s*hr)?\s*(?:(\d+)\s*min)?", re.IGNORECASE
)
ARIA_DEPARTURE_RE = re.compile(
    r"Leaves .*? at (\d{1,2}:\d{2}\s?[AP]M) on\s+(\w+,\s+\w+\s+\d{1,2})", re.IGNORECASE
)
ARIA_ARRIVAL_RE = re.compile(
    r"arrives at .*? at (\d{1,2}:\d{2}\s?[AP]M) on\s+(\w+,\s+\w+\s+\d{1,2})", re.IGNORECASE
)

# Standalone element-level selectors, used as a fallback / cross-check
# against the aggregate aria-label when individual spans are present.
DEPARTURE_TIME_ARIA_PREFIX = "Departure time:"
ARRIVAL_TIME_ARIA_PREFIX = "Arrival time:"
DURATION_ARIA_PREFIX = "Total duration"
STOPS_ARIA_SUFFIX = "flight."
PRICE_ARIA_SUFFIX_CURRENCIES = ("Indian rupees", "US dollars", "Euros")

CO2_DATA_ATTR = "data-co2currentflight"

# Flight number isn't exposed as a dedicated attribute. It appears embedded
# in the Travel Impact Model lookup URL Google attaches to each result's
# emissions widget, e.g.:
#   data-travelimpactmodelwebsiteurl="https://www.travelimpactmodel.org/
#   lookup/flight?itinerary=CCU-BOM-QP-1126-20260916"
# We parse the "itinerary=ORIGIN-DEST-CODE-NUMBER-YYYYMMDD" token from it.
FLIGHT_NUMBER_DATA_ATTR = "data-travelimpactmodelwebsiteurl"

CURRENCY_NAME_TO_CODE = {
    "indian rupees": "INR",
    "us dollars": "USD",
    "euros": "EUR",
}
