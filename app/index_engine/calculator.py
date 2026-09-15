"""Combines representative fares, base-period fares, and route weights into
per-route indexes and one overall Airfare Price Index (APIx) value.

Methodology (documented for transparency, per the MoSPI requirement):
  1. For each (route, advance_days) window, take the median normalized fare
     of valid, non-outlier observations as the "current" representative fare.
  2. The same computation against the earliest available observations for
     that route/window is the "base" representative fare (base period).
  3. route_index = (current_fare / base_fare) * 100  (price relative * 100)
  4. overall_index = sum(route_weight_normalized * route_index) across routes
     that have both a current and base fare for that window.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.config.constants import INDEX_BASE_VALUE
from app.index_engine.price_relative import price_relative_index
from app.index_engine.weights import normalize_weights


@dataclass
class RouteIndexResult:
    route_id: UUID
    current_fare: Decimal
    base_fare: Decimal
    index_value: Decimal
    weight: Decimal


@dataclass
class OverallIndexResult:
    index_value: Decimal
    base_value: Decimal
    sample_size: int
    route_indexes: list[RouteIndexResult]


def calculate_route_index(current_fare: Decimal, base_fare: Decimal) -> Decimal:
    return price_relative_index(current_fare, base_fare)


def calculate_overall_index(
    current_fares: dict[UUID, Decimal],
    base_fares: dict[UUID, Decimal],
    route_weights: dict[UUID, Decimal],
) -> OverallIndexResult:
    """Compute route-level indexes and the weighted overall APIx.

    Only routes present in all three inputs (current fare, base fare, and a
    weight) contribute — a route missing any of these can't produce a valid
    relative, so it's excluded rather than assumed/estimated.
    """
    usable_route_ids = set(current_fares) & set(base_fares) & set(route_weights)

    if not usable_route_ids:
        return OverallIndexResult(
            index_value=Decimal(INDEX_BASE_VALUE),
            base_value=Decimal(INDEX_BASE_VALUE),
            sample_size=0,
            route_indexes=[],
        )

    weights_subset = {rid: route_weights[rid] for rid in usable_route_ids}
    normalized = normalize_weights(weights_subset)

    route_results = []
    weighted_sum = Decimal(0)
    for route_id in usable_route_ids:
        current = current_fares[route_id]
        base = base_fares[route_id]
        weight = normalized[route_id]
        route_index = calculate_route_index(current, base)
        weighted_sum += weight * route_index
        route_results.append(
            RouteIndexResult(
                route_id=route_id,
                current_fare=current,
                base_fare=base,
                index_value=route_index,
                weight=weight,
            )
        )

    return OverallIndexResult(
        index_value=weighted_sum,
        base_value=Decimal(INDEX_BASE_VALUE),
        sample_size=len(route_results),
        route_indexes=route_results,
    )
