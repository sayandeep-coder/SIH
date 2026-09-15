import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class RouteIndexOut(BaseModel):
    route_id: uuid.UUID
    route_code: str
    index_value: Decimal
    base_value: Decimal


class AdvanceWindowIndexOut(BaseModel):
    advance_days: int
    index_value: Decimal
    base_value: Decimal
    sample_size: int


class IndexSummaryOut(BaseModel):
    date: date
    index: Decimal
    base: Decimal
    advance_windows: dict[int, Decimal]


class AdvanceWindowsOut(BaseModel):
    windows: list[int]
