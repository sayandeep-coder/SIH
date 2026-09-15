from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FlightResult(BaseModel):
    """Normalized representation of a single Google Flights search result."""

    model_config = ConfigDict(frozen=True)

    airline_name: str
    airline_code: str | None = None
    flight_number: str | None = None

    origin: str
    destination: str

    departure_date: date
    departure_time: time | None = None
    arrival_date: date | None = None
    arrival_time: time | None = None

    duration_minutes: int | None = Field(default=None, ge=0)
    stops: int = Field(default=0, ge=0)

    price: Decimal = Field(gt=0)
    currency: str = "INR"

    emissions_kg: float | None = Field(default=None, ge=0)

    source: str = "google_flights"

    @field_validator("origin", "destination", "airline_code")
    @classmethod
    def _upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value
