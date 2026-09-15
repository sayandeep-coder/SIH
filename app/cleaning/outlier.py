"""Flags statistically unusual fares within a comparable group (same route +
advance_days bucket) using the IQR (interquartile range) method.

IQR is chosen over z-score because fare distributions are typically
right-skewed (a few very expensive last-minute/business fares), and IQR
doesn't assume normality. A point is flagged if it falls outside
[Q1 - 1.5*IQR, Q3 + 1.5*IQR] — the standard Tukey fence.

Outliers are flagged, never dropped: raw fare_quotes stay untouched, and
fare_observations.is_outlier lets the index calculation choose to exclude
them.
"""

from decimal import Decimal

import pandas as pd

IQR_MULTIPLIER = 1.5
MIN_GROUP_SIZE_FOR_DETECTION = 4  # IQR is unstable/meaningless on tiny samples


def flag_outliers(fares: list[Decimal]) -> list[bool]:
    """Returns a same-length list of booleans: True where the fare at that
    index is an IQR outlier within the given group of fares.

    Callers are expected to pass fares already grouped by (route, advance_days)
    — outlier detection only makes sense within a comparable cohort.
    """
    if len(fares) < MIN_GROUP_SIZE_FOR_DETECTION:
        return [False] * len(fares)

    values = pd.Series([float(f) for f in fares])
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return [False] * len(fares)

    lower_fence = q1 - IQR_MULTIPLIER * iqr
    upper_fence = q3 + IQR_MULTIPLIER * iqr

    return list(((values < lower_fence) | (values > upper_fence)).to_numpy(dtype=bool))


def flag_outliers_grouped(
    rows: list[dict],
    group_keys: tuple[str, ...] = ("route_id", "advance_days"),
    fare_key: str = "normalized_fare",
) -> list[bool]:
    """Vectorized IQR outlier detection across multiple groups at once.

    `rows` is a list of dicts each containing the group_keys and fare_key.
    Returns a same-length list of outlier flags aligned to the input order.
    """
    if not rows:
        return []

    df = pd.DataFrame(rows)
    df["_fare"] = df[fare_key].astype(float)

    group_size = df.groupby(list(group_keys), dropna=False)["_fare"].transform("size")
    q1 = df.groupby(list(group_keys), dropna=False)["_fare"].transform("quantile", 0.25)
    q3 = df.groupby(list(group_keys), dropna=False)["_fare"].transform("quantile", 0.75)
    iqr = q3 - q1

    lower_fence = q1 - IQR_MULTIPLIER * iqr
    upper_fence = q3 + IQR_MULTIPLIER * iqr

    is_outlier = (group_size >= MIN_GROUP_SIZE_FOR_DETECTION) & (iqr > 0) & (
        (df["_fare"] < lower_fence) | (df["_fare"] > upper_fence)
    )
    return list(is_outlier.to_numpy(dtype=bool))
