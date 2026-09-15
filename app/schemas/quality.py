import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DataQualityEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quote_id: uuid.UUID | None
    event_type: str
    severity: str
    message: str
    created_at: datetime


class DataQualitySummaryOut(BaseModel):
    total_quotes: int
    total_observations: int
    valid_observations: int
    outlier_observations: int
    valid_rate: float
    outlier_rate: float
    duplicate_events: int
    validation_failed_events: int
