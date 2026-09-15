"""Idempotently seeds the airports table. Safe to run repeatedly — uses
ON CONFLICT DO NOTHING keyed on the unique iata_code, so re-running never
creates duplicates or disturbs already-seeded rows.

Usage:
    python scripts/seed_airports.py
"""

import asyncio

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.database import AsyncSessionLocal
from app.db.models import Airport

logger = structlog.get_logger(__name__)

# (iata_code, city, state) — major Indian domestic airports.
AIRPORTS: list[tuple[str, str, str]] = [
    ("DEL", "Delhi", "Delhi"),
    ("BOM", "Mumbai", "Maharashtra"),
    ("BLR", "Bengaluru", "Karnataka"),
    ("MAA", "Chennai", "Tamil Nadu"),
    ("HYD", "Hyderabad", "Telangana"),
    ("CCU", "Kolkata", "West Bengal"),
    ("COK", "Kochi", "Kerala"),
    ("AMD", "Ahmedabad", "Gujarat"),
    ("PNQ", "Pune", "Maharashtra"),
    ("JAI", "Jaipur", "Rajasthan"),
    ("GOI", "Goa", "Goa"),
    ("GOX", "Goa Mopa", "Goa"),
    ("LKO", "Lucknow", "Uttar Pradesh"),
    ("IXC", "Chandigarh", "Chandigarh"),
    ("NAG", "Nagpur", "Maharashtra"),
    ("BBI", "Bhubaneswar", "Odisha"),
    ("PAT", "Patna", "Bihar"),
    ("GAU", "Guwahati", "Assam"),
    ("IXR", "Ranchi", "Jharkhand"),
    ("RPR", "Raipur", "Chhattisgarh"),
    ("BHO", "Bhopal", "Madhya Pradesh"),
    ("IDR", "Indore", "Madhya Pradesh"),
    ("TRV", "Thiruvananthapuram", "Kerala"),
    ("CCJ", "Kozhikode", "Kerala"),
    ("IXE", "Mangaluru", "Karnataka"),
    ("CJB", "Coimbatore", "Tamil Nadu"),
    ("IXM", "Madurai", "Tamil Nadu"),
    ("VGA", "Vijayawada", "Andhra Pradesh"),
    ("VNS", "Varanasi", "Uttar Pradesh"),
    ("ATQ", "Amritsar", "Punjab"),
    ("IXJ", "Jammu", "Jammu and Kashmir"),
    ("SXR", "Srinagar", "Jammu and Kashmir"),
    ("JDH", "Jodhpur", "Rajasthan"),
    ("UDR", "Udaipur", "Rajasthan"),
    ("BDQ", "Vadodara", "Gujarat"),
    ("DED", "Dehradun", "Uttarakhand"),
    ("IXA", "Agartala", "Tripura"),
    ("IMF", "Imphal", "Manipur"),
    ("TRZ", "Tiruchirappalli", "Tamil Nadu"),
    ("SXV", "Salem", "Tamil Nadu"),
    ("TIR", "Tirupati", "Andhra Pradesh"),
    ("VTZ", "Visakhapatnam", "Andhra Pradesh"),
    ("RJA", "Rajahmundry", "Andhra Pradesh"),
    ("CDP", "Cuddapah", "Andhra Pradesh"),
    ("HBX", "Hubli", "Karnataka"),
    ("BEP", "Bellary", "Karnataka"),
    ("IXG", "Belagavi", "Karnataka"),
    ("STV", "Surat", "Gujarat"),
    ("RAJ", "Rajkot", "Gujarat"),
    ("BHJ", "Bhuj", "Gujarat"),
    ("PBD", "Porbandar", "Gujarat"),
    ("KLH", "Kolhapur", "Maharashtra"),
    ("SSE", "Solapur", "Maharashtra"),
    ("AUR", "Aurangabad", "Maharashtra"),
    ("NDC", "Nanded", "Maharashtra"),
    ("ISK", "Nashik", "Maharashtra"),
    ("BKB", "Bhatinda", "Punjab"),
    ("LUH", "Ludhiana", "Punjab"),
    ("KUU", "Kullu", "Himachal Pradesh"),
    ("SLV", "Shimla", "Himachal Pradesh"),
    ("GGN", "Gaggal", "Himachal Pradesh"),
    ("LEH", "Leh", "Ladakh"),
    ("KNU", "Kanpur", "Uttar Pradesh"),
    ("IXD", "Allahabad", "Uttar Pradesh"),
    ("GOP", "Gorakhpur", "Uttar Pradesh"),
    ("BUP", "Bareilly", "Uttar Pradesh"),
    ("HJR", "Khajuraho", "Madhya Pradesh"),
    ("JLR", "Jabalpur", "Madhya Pradesh"),
    ("GWL", "Gwalior", "Madhya Pradesh"),
    ("REW", "Rewa", "Madhya Pradesh"),
    ("DBD", "Dhanbad", "Jharkhand"),
    ("JRG", "Jharsuguda", "Odisha"),
    ("SHL", "Shillong", "Meghalaya"),
    ("DIB", "Dibrugarh", "Assam"),
    ("JRH", "Jorhat", "Assam"),
    ("SIL", "Silchar", "Assam"),
    ("TEZ", "Tezpur", "Assam"),
    ("IXB", "Bagdogra", "West Bengal"),
    ("KYA", "Durgapur", "West Bengal"),
    ("JGA", "Jamnagar", "Gujarat"),
    ("MYQ", "Mysuru", "Karnataka"),
    ("PNY", "Puducherry", "Puducherry"),
    ("PGH", "Pantnagar", "Uttarakhand"),
]


async def seed_airports() -> None:
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(Airport).values(
            [{"iata_code": code, "city": city, "state": state} for code, city, state in AIRPORTS]
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["iata_code"])
        result = await session.execute(stmt)
        await session.commit()
        logger.info("seed_airports.completed", attempted=len(AIRPORTS), inserted=result.rowcount)


if __name__ == "__main__":
    asyncio.run(seed_airports())
