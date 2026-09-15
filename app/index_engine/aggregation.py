"""Aggregates individual fare_observations into one representative fare per
(route, advance_days) group, for feeding into the price-relative calculation.

The median is used rather than the mean: fares within a route/window are
often right-skewed (a handful of premium fares among many economy fares),
and the median is far less sensitive to that skew or to any outlier that
slipped through IQR flagging.
"""

from decimal import Decimal
from uuid import UUID

import pandas as pd


def representative_fares(
    observations: list[dict], exclude_outliers: bool = True
) -> dict[tuple[UUID, int], Decimal]:
    """Group fare_observations by (route_id, advance_days) and compute the
    median normalized_fare for each group.

    `observations` rows must contain: route_id, advance_days, normalized_fare,
    is_outlier, is_valid.
    """
    if not observations:
        return {}

    df = pd.DataFrame(observations)
    df = df[df["is_valid"]]
    if exclude_outliers:
        df = df[~df["is_outlier"]]

    if df.empty:
        return {}

    df["normalized_fare"] = df["normalized_fare"].astype(float)
    medians = df.groupby(["route_id", "advance_days"])["normalized_fare"].median()

    return {
        (route_id, int(advance_days)): Decimal(str(median))
        for (route_id, advance_days), median in medians.items()
    }
