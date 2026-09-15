from datetime import date

from pydantic import BaseModel

from app.scrapers.google_flights.models import FlightResult


class ScrapeRequest(BaseModel):
    departure_date: date


class QuoteRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date


class QuoteResponse(BaseModel):
    route_code: str
    departure_date: date
    flights_found: int
    flights: list[FlightResult]


class ScrapeJobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None = None
    error: str | None = None
