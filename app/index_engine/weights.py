"""Route weight resolution for the aggregate index.

Weights come from the index_weights table (the authoritative source per the
MoSPI methodology), not a hardcoded mapping — if the table changes, the
index recalculates accordingly with no code change.
"""

from decimal import Decimal
from uuid import UUID


def normalize_weights(route_weights: dict[UUID, Decimal]) -> dict[UUID, Decimal]:
    """Rescale weights so they sum to 1, so the aggregate index is a proper
    weighted average even if the stored weights don't already total 1
    (e.g. only a subset of routes have current data this period).
    """
    total = sum(route_weights.values())
    if total <= 0:
        return dict.fromkeys(route_weights, Decimal(0))
    return {route_id: weight / total for route_id, weight in route_weights.items()}
