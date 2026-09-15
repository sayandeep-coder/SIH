import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.airport import AirportOut


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_code: str
    weight: Decimal | None
    is_active: bool
    origin: AirportOut
    destination: AirportOut
