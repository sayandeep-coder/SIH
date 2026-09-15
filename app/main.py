import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import airports, fares, index, quality, routes, scraping
from app.config.settings import settings

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper())
    ),
)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraping.router)
app.include_router(fares.router)
app.include_router(routes.router)
app.include_router(airports.router)
app.include_router(index.router)
app.include_router(quality.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
