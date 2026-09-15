import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    iata_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Airline(Base):
    __tablename__ = "airlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (UniqueConstraint("origin_id", "destination_id", name="unique_route"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    origin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("airports.id"), nullable=False)
    destination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("airports.id"), nullable=False)
    route_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    origin: Mapped["Airport"] = relationship(foreign_keys=[origin_id])
    destination: Mapped["Airport"] = relationship(foreign_keys=[destination_id])


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="running")
    records_found: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    records_valid: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FareQuote(Base):
    __tablename__ = "fare_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    scrape_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scrape_runs.id"), nullable=False)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    airline_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("airlines.id"), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    flight_number: Mapped[str | None] = mapped_column(String, nullable=True)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    advance_days: Mapped[int] = mapped_column(Integer, nullable=False)
    fare_class: Mapped[str | None] = mapped_column(String, nullable=True)
    base_fare: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    taxes: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, server_default="0")
    udf: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, server_default="0")
    convenience_fee: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, server_default="0")
    other_fees: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True, server_default="0")
    total_fare: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, server_default="INR")
    availability: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    route: Mapped["Route"] = relationship()
    airline: Mapped["Airline | None"] = relationship()


class FareObservation(Base):
    __tablename__ = "fare_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fare_quotes.id"), nullable=False)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    airline_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("airlines.id"), nullable=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    advance_days: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_fare: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    base_fare: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    taxes: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    udf: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    convenience_fee: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    other_fees: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    is_outlier: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    cleaning_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndexWeight(Base):
    __tablename__ = "index_weights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndexValue(Base):
    __tablename__ = "index_values"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    index_date: Mapped[date] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)
    route_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True)
    index_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    base_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False, server_default="100")
    previous_value: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    change_percent: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    methodology_version: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataQualityEvent(Base):
    __tablename__ = "data_quality_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fare_quotes.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
