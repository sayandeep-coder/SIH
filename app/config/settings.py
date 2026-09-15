from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Neon (and most managed Postgres providers) issue DATABASE_URL in the
# psycopg2/libpq style: scheme "postgresql://" with "sslmode"/"channel_binding"
# query params. asyncpg needs the "postgresql+asyncpg://" scheme and doesn't
# understand those libpq-specific params (it uses ssl=true instead), so we
# normalize here rather than requiring a hand-edited .env.
_LIBPQ_TO_ASYNCPG_DROP_PARAMS = {"sslmode", "channel_binding"}


def _to_asyncpg_url(raw_url: str) -> str:
    parts = urlsplit(raw_url)
    scheme = parts.scheme
    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"

    query_pairs = [
        (k, v)
        for k, v in (p.split("=", 1) for p in parts.query.split("&") if p)
        if k not in _LIBPQ_TO_ASYNCPG_DROP_PARAMS
    ]
    query_pairs.append(("ssl", "require"))
    new_query = "&".join(f"{k}={v}" for k, v in query_pairs)

    return urlunsplit((scheme, parts.netloc, parts.path, new_query, parts.fragment))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "Airfare Price Index"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (Neon PostgreSQL)
    database_url: str

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return _to_asyncpg_url(value)

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Google Flights
    google_flights_base_url: str = "https://www.google.com/travel/flights/search"
    google_flights_language: str = "en"
    google_flights_country: str = "IN"

    # Scraper
    scraper_headless: bool = True
    scraper_timeout: int = 30000
    scraper_max_retries: int = 3
    scraper_rate_limit_seconds: int = 2

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
