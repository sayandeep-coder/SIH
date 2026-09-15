"""Deduplicates fare_quotes before they're promoted to fare_observations.

A duplicate is the same bookable fare seen more than once: same route,
airline, flight number, departure date/time, and fare. We keep the earliest
scrape of each duplicate group (first-seen wins) — later duplicates add no
new information for the index. Uses vectorized pandas operations rather than
O(n^2) pairwise comparisons.
"""

import pandas as pd

from app.db.models import FareQuote

DEDUPE_KEY_COLUMNS = [
    "route_id",
    "airline_id",
    "flight_number",
    "departure_date",
    "departure_time",
    "total_fare",
]


def dedupe_fare_quotes(quotes: list[FareQuote]) -> tuple[list[FareQuote], list[FareQuote]]:
    """Split quotes into (kept, dropped_as_duplicate).

    Ordering is preserved by scraped_at so "first seen" is deterministic
    regardless of the input list's original order.
    """
    if not quotes:
        return [], []

    ordered = sorted(quotes, key=lambda q: q.scraped_at)
    df = pd.DataFrame(
        {
            "idx": range(len(ordered)),
            "route_id": [q.route_id for q in ordered],
            "airline_id": [q.airline_id for q in ordered],
            "flight_number": [q.flight_number for q in ordered],
            "departure_date": [q.departure_date for q in ordered],
            "departure_time": [q.departure_time for q in ordered],
            "total_fare": [q.total_fare for q in ordered],
        }
    )

    is_duplicate = df.duplicated(subset=DEDUPE_KEY_COLUMNS, keep="first")

    kept = [ordered[i] for i in df.loc[~is_duplicate, "idx"]]
    dropped = [ordered[i] for i in df.loc[is_duplicate, "idx"]]
    return kept, dropped
