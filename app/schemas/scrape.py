import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScrapeRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    records_found: int
    records_valid: int
    error_message: str | None
    route_code: str | None = None
    departure_date: str | None = None
