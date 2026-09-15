"""Seeds/rebalances index_weights with equal weighting across all active
routes (1/N each) as a placeholder until real MoSPI traffic-share weights
are available.

Idempotent in the sense that matters: if the active route count hasn't
changed since the last equal-weight seed, running again is a no-op. If new
routes were added (or removed), all equal-weight rows are rebalanced
together as a new dated version — so weights across every route always sum
to 1, rather than mixing stale 1/N values from before a route count change
with new ones.

Usage:
    python scripts/seed_index_weights.py
"""

import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import IndexWeight, Route

logger = structlog.get_logger(__name__)

WEIGHT_SOURCE = "equal_weight_seed"


async def seed_index_weights() -> None:
    async with AsyncSessionLocal() as session:
        routes_result = await session.execute(select(Route.id).where(Route.is_active.is_(True)))
        route_ids = [row[0] for row in routes_result.all()]

        if not route_ids:
            logger.info("seed_index_weights.completed", attempted=0, inserted=0)
            return

        today = datetime.now(timezone.utc).date()

        # Find the currently-open equal-weight rows (effective_to IS NULL)
        # to see if they already cover exactly this route set.
        open_result = await session.execute(
            select(IndexWeight).where(
                IndexWeight.source == WEIGHT_SOURCE, IndexWeight.effective_to.is_(None)
            )
        )
        open_weights = list(open_result.scalars().all())
        open_route_ids = {w.route_id for w in open_weights}

        if open_route_ids == set(route_ids):
            logger.info(
                "seed_index_weights.completed",
                attempted=0,
                inserted=0,
                note="route set unchanged, equal weights already balanced",
            )
            return

        equal_weight = 1 / len(route_ids)
        new_version = f"v-equal-{today.isoformat()}"

        # Close out any previously-open equal-weight rows so history stays
        # queryable (effective_to marks when that weight stopped applying).
        for weight_row in open_weights:
            weight_row.effective_to = today

        session.add_all(
            [
                IndexWeight(
                    route_id=route_id,
                    weight=equal_weight,
                    source=WEIGHT_SOURCE,
                    effective_from=today,
                    version=new_version,
                )
                for route_id in route_ids
            ]
        )
        await session.commit()
        logger.info(
            "seed_index_weights.completed",
            attempted=len(route_ids),
            inserted=len(route_ids),
            closed_previous=len(open_weights),
            weight_per_route=equal_weight,
            version=new_version,
        )


if __name__ == "__main__":
    asyncio.run(seed_index_weights())
