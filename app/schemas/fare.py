import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FareQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_id: uuid.UUID
    route_code: str
    airline_id: uuid.UUID | None
    airline_code: str | None
    airline_name: str | None
    source: str
    flight_number: str | None
    departure_date: date
    departure_time: time | None
    advance_days: int
    total_fare: Decimal
    currency: str
    availability: bool
    stops: int | None
    duration_minutes: int | None
    scraped_at: datetime
