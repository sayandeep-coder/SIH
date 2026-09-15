import uuid

from pydantic import BaseModel, ConfigDict


class AirportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    iata_code: str
    city: str
    state: str | None
    is_active: bool
