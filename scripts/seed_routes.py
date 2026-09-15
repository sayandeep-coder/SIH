"""Idempotently seeds the routes table from a fixed set of major domestic
IATA pairs. Safe to run repeatedly — uses ON CONFLICT DO NOTHING keyed on
the unique route_code, so re-running never creates duplicates.

Requires airports to already be seeded (run seed_airports.py first).

Usage:
    python scripts/seed_routes.py
"""

import asyncio

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.database import AsyncSessionLocal
from app.db.models import Airport, Route

logger = structlog.get_logger(__name__)

# Major domestic route pairs (origin, destination), both directions where
# traffic is meaningful, mirroring the existing 45 routes already used for
# the Google Flights milestone.
ROUTE_PAIRS: list[tuple[str, str]] = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("DEL", "MAA"), ("DEL", "HYD"),
    ("DEL", "CCU"), ("DEL", "COK"), ("DEL", "AMD"), ("DEL", "PNQ"),
    ("DEL", "GOI"),
    ("BOM", "DEL"), ("BOM", "BLR"), ("BOM", "CCU"), ("BOM", "HYD"),
    ("BOM", "MAA"), ("BOM", "PNQ"), ("BOM", "AMD"), ("BOM", "GOI"),
    ("BLR", "DEL"), ("BLR", "BOM"), ("BLR", "CCU"), ("BLR", "HYD"),
    ("BLR", "MAA"), ("BLR", "PNQ"), ("BLR", "COK"),
    ("MAA", "DEL"), ("MAA", "BOM"), ("MAA", "BLR"), ("MAA", "CCU"),
    ("MAA", "HYD"),
    ("HYD", "DEL"), ("HYD", "BOM"), ("HYD", "BLR"), ("HYD", "MAA"),
    ("CCU", "DEL"), ("CCU", "BOM"), ("CCU", "BLR"), ("CCU", "HYD"),
    ("COK", "DEL"), ("COK", "BOM"), ("COK", "BLR"),
    ("AMD", "DEL"), ("AMD", "BOM"),
    ("PNQ", "DEL"), ("PNQ", "BOM"), ("PNQ", "BLR"),

    # Tier-2/3 spokes connected to the major hubs (hub-and-spoke pattern,
    # matching realistic Indian domestic connectivity rather than a full mesh).
    ("DEL", "LKO"), ("LKO", "DEL"), ("DEL", "PAT"), ("PAT", "DEL"),
    ("DEL", "JAI"), ("JAI", "DEL"), ("DEL", "IXC"), ("IXC", "DEL"),
    ("DEL", "VNS"), ("VNS", "DEL"), ("DEL", "ATQ"), ("ATQ", "DEL"),
    ("DEL", "BHO"), ("BHO", "DEL"), ("DEL", "IDR"), ("IDR", "DEL"),
    ("DEL", "RPR"), ("RPR", "DEL"), ("DEL", "GAU"), ("GAU", "DEL"),
    ("DEL", "IXR"), ("IXR", "DEL"), ("DEL", "BBI"), ("BBI", "DEL"),
    ("DEL", "SXR"), ("SXR", "DEL"), ("DEL", "IXJ"), ("IXJ", "DEL"),
    ("DEL", "UDR"), ("UDR", "DEL"), ("DEL", "JDH"), ("JDH", "DEL"),
    ("DEL", "DED"), ("DED", "DEL"), ("DEL", "GWL"), ("GWL", "DEL"),

    ("BOM", "IDR"), ("IDR", "BOM"), ("BOM", "NAG"), ("NAG", "BOM"),
    ("BOM", "RAJ"), ("RAJ", "BOM"), ("BOM", "BDQ"), ("BDQ", "BOM"),
    ("BOM", "AUR"), ("AUR", "BOM"), ("BOM", "ISK"), ("ISK", "BOM"),
    ("BOM", "JGA"), ("JGA", "BOM"), ("BOM", "COK"), ("BOM", "TRV"), ("TRV", "BOM"),

    ("BLR", "MYQ"), ("MYQ", "BLR"), ("BLR", "HBX"), ("HBX", "BLR"),
    ("BLR", "IXE"), ("IXE", "BLR"), ("BLR", "TRV"), ("TRV", "BLR"),
    ("BLR", "VGA"), ("VGA", "BLR"), ("BLR", "TIR"), ("TIR", "BLR"),
    ("BLR", "CJB"), ("CJB", "BLR"), ("BLR", "IXM"), ("IXM", "BLR"),

    ("MAA", "TRZ"), ("TRZ", "MAA"), ("MAA", "CJB"), ("CJB", "MAA"),
    ("MAA", "IXM"), ("IXM", "MAA"), ("MAA", "TIR"), ("TIR", "MAA"),
    ("MAA", "VGA"), ("VGA", "MAA"), ("MAA", "VTZ"), ("VTZ", "MAA"),
    ("MAA", "COK"), ("COK", "MAA"), ("MAA", "PNY"), ("PNY", "MAA"),

    ("HYD", "VTZ"), ("VTZ", "HYD"), ("HYD", "VGA"), ("VGA", "HYD"),
    ("HYD", "TIR"), ("TIR", "HYD"), ("HYD", "RAJ"), ("RAJ", "HYD"),
    ("HYD", "NAG"), ("NAG", "HYD"),

    ("CCU", "GAU"), ("GAU", "CCU"), ("CCU", "BBI"), ("BBI", "CCU"),
    ("CCU", "PAT"), ("PAT", "CCU"), ("CCU", "IXB"), ("IXB", "CCU"),
    ("CCU", "IXR"), ("IXR", "CCU"), ("CCU", "DIB"), ("DIB", "CCU"),
    ("CCU", "IXA"), ("IXA", "CCU"), ("CCU", "SHL"), ("SHL", "CCU"),
    ("CCU", "KYA"), ("KYA", "CCU"),
]


async def seed_routes() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Airport.iata_code, Airport.id))
        airport_ids = dict(result.all())

        rows = []
        skipped = []
        for origin_code, dest_code in ROUTE_PAIRS:
            origin_id = airport_ids.get(origin_code)
            dest_id = airport_ids.get(dest_code)
            if origin_id is None or dest_id is None:
                skipped.append((origin_code, dest_code))
                continue
            rows.append(
                {
                    "origin_id": origin_id,
                    "destination_id": dest_id,
                    "route_code": f"{origin_code}-{dest_code}",
                }
            )

        if skipped:
            logger.warning("seed_routes.skipped_unknown_airports", pairs=skipped)

        if not rows:
            logger.info("seed_routes.completed", attempted=0, inserted=0)
            return

        stmt = pg_insert(Route).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["route_code"])
        result = await session.execute(stmt)
        await session.commit()
        logger.info("seed_routes.completed", attempted=len(rows), inserted=result.rowcount)


if __name__ == "__main__":
    asyncio.run(seed_routes())
