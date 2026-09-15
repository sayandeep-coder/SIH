from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.celery_app import celery_app
from app.db.repositories.scrape_repository import ScrapeRepository
from app.schemas.flight import JobStatusResponse, QuoteRequest, QuoteResponse, ScrapeJobResponse, ScrapeRequest
from app.schemas.scrape import ScrapeRunOut
from app.services.scraping_service import ScrapingServiceError, run_google_flights_scrape
from app.tasks.scraping_tasks import scrape_google_flights

router = APIRouter(prefix="/api/v1/scraping", tags=["scraping"])


@router.post("/route/{route_code}", response_model=ScrapeJobResponse)
async def trigger_scrape(route_code: str, request: ScrapeRequest) -> ScrapeJobResponse:
    task = scrape_google_flights.delay(route_code.upper(), request.departure_date.isoformat())
    return ScrapeJobResponse(job_id=task.id, status="queued")


@router.post("/quote", response_model=QuoteResponse)
async def get_live_quote(
    request: QuoteRequest, session: AsyncSession = Depends(get_session)
) -> QuoteResponse:
    """Scrape Google Flights synchronously for one origin/destination/date
    and return the flight prices directly in the response.

    Unlike POST /route/{route_code}, this does not queue a Celery job — it
    runs Playwright inline and blocks until the scrape completes (typically
    a few seconds, but can take longer under load or retries).
    """
    route_code = f"{request.origin.upper()}-{request.destination.upper()}"

    try:
        result = await run_google_flights_scrape(session, route_code, request.departure_date)
    except ScrapingServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    flights = result.get("flights", [])
    return QuoteResponse(
        route_code=route_code,
        departure_date=request.departure_date,
        flights_found=len(flights),
        flights=flights,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    result = AsyncResult(job_id, app=celery_app)

    if not result.id:
        raise HTTPException(status_code=404, detail="Job not found")

    response = JobStatusResponse(job_id=job_id, status=result.status)
    if result.successful():
        response.result = result.result
    elif result.failed():
        response.error = str(result.result)

    return response


@router.get("/runs", response_model=list[ScrapeRunOut])
async def list_scrape_runs(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[ScrapeRunOut]:
    repo = ScrapeRepository(session)
    runs = await repo.list_recent(limit=limit)
    return [
        ScrapeRunOut(
            id=run.id,
            source=run.source,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            records_found=run.records_found,
            records_valid=run.records_valid,
            error_message=run.error_message,
            route_code=(run.run_metadata or {}).get("route_code"),
            departure_date=(run.run_metadata or {}).get("departure_date"),
        )
        for run in runs
    ]
