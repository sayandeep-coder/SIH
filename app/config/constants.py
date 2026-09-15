from enum import Enum


class CabinClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class TripType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


# Google Flights TFS proto field codes for cabin class (flights.tfs "seat" enum)
GOOGLE_FLIGHTS_CABIN_CODE: dict[CabinClass, int] = {
    CabinClass.ECONOMY: 1,
    CabinClass.PREMIUM_ECONOMY: 2,
    CabinClass.BUSINESS: 3,
    CabinClass.FIRST: 4,
}

# Google Flights TFS proto field codes for trip type (flights.tfs "flight type" enum)
GOOGLE_FLIGHTS_TRIP_CODE: dict[TripType, int] = {
    TripType.ROUND_TRIP: 1,
    TripType.ONE_WAY: 2,
}

DEFAULT_CURRENCY = "INR"

SCRAPE_RUN_STATUS_RUNNING = "running"
SCRAPE_RUN_STATUS_SUCCESS = "success"
SCRAPE_RUN_STATUS_FAILED = "failed"

SOURCE_GOOGLE_FLIGHTS = "google_flights"

# Advance-booking windows the MoSPI methodology tracks. fare_quotes and
# fare_observations both have a DB check constraint restricting advance_days
# to exactly these values.
ADVANCE_DAYS_WINDOWS: tuple[int, ...] = (1, 7, 15, 30, 45)

INDEX_METHODOLOGY_VERSION = "apix-v1"
INDEX_BASE_VALUE = 100
