"""Playwright-driven Google Flights scraper.

Owns browser lifecycle, navigation, waiting for results, and debug-artifact
capture on failure. Contains no database logic and no parsing logic beyond
handing raw HTML to the parser module — see parser.py for extraction.
"""

import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

import structlog
from playwright.async_api import Browser, Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from app.config.settings import settings
from app.scrapers.google_flights.models import FlightResult
from app.scrapers.google_flights.parser import parse_flight_cards
from app.scrapers.google_flights.selectors import FLIGHT_LINK_SELECTOR

logger = structlog.get_logger(__name__)

DEBUG_ARTIFACT_DIR = Path("data/raw")


class GoogleFlightsScraperError(Exception):
    """Raised when the scraper cannot produce results after all retries."""


async def scrape_google_flights(
    deeplink: str,
    origin: str,
    destination: str,
    departure_date: date,
) -> list[FlightResult]:
    """Open a Google Flights deeplink and return parsed flight results.

    Retries up to settings.scraper_max_retries times on timeout or empty
    results, capturing a screenshot + HTML dump to data/raw/ on each failure
    for debugging.
    """
    last_error: Exception | None = None

    for attempt in range(1, settings.scraper_max_retries + 1):
        try:
            html = await _fetch_results_html(deeplink, attempt)
            results = parse_flight_cards(html, origin, destination, departure_date)
            if results:
                logger.info(
                    "google_flights.scraper.success",
                    origin=origin,
                    destination=destination,
                    attempt=attempt,
                    flights=len(results),
                )
                return results

            logger.warning(
                "google_flights.scraper.empty_results",
                origin=origin,
                destination=destination,
                attempt=attempt,
            )
            await _dump_debug_artifacts(html, origin, destination, attempt, reason="empty_results")
            last_error = GoogleFlightsScraperError("No flight results parsed from page")

        except PlaywrightTimeoutError as exc:
            logger.warning(
                "google_flights.scraper.timeout",
                origin=origin,
                destination=destination,
                attempt=attempt,
                error=str(exc),
            )
            last_error = exc
        except Exception as exc:
            logger.error(
                "google_flights.scraper.unexpected_error",
                origin=origin,
                destination=destination,
                attempt=attempt,
                exc_info=True,
            )
            last_error = exc

        if attempt < settings.scraper_max_retries:
            await asyncio.sleep(settings.scraper_rate_limit_seconds)

    raise GoogleFlightsScraperError(
        f"Failed to scrape {origin}->{destination} after {settings.scraper_max_retries} attempts"
    ) from last_error


async def _fetch_results_html(deeplink: str, attempt: int) -> str:
    async with async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=settings.scraper_headless)
        try:
            page: Page = await browser.new_page()
            page.set_default_timeout(settings.scraper_timeout)

            logger.info("google_flights.scraper.navigating", deeplink=deeplink, attempt=attempt)
            await page.goto(deeplink, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector(FLIGHT_LINK_SELECTOR, timeout=settings.scraper_timeout)
            except PlaywrightTimeoutError:
                html = await page.content()
                await _dump_debug_artifacts(
                    html, "unknown", "unknown", attempt, reason="wait_for_results_timeout", page=page
                )
                raise

            html = await page.content()
            return html
        finally:
            await browser.close()


async def _dump_debug_artifacts(
    html: str,
    origin: str,
    destination: str,
    attempt: int,
    reason: str,
    page: Page | None = None,
) -> None:
    try:
        DEBUG_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        stem = f"{origin}-{destination}-{reason}-attempt{attempt}-{timestamp}"

        html_path = DEBUG_ARTIFACT_DIR / f"{stem}.html"
        html_path.write_text(html, encoding="utf-8")

        if page is not None:
            screenshot_path = DEBUG_ARTIFACT_DIR / f"{stem}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

        logger.info("google_flights.scraper.debug_artifacts_saved", stem=stem, reason=reason)
    except Exception:
        logger.error("google_flights.scraper.debug_artifact_failed", exc_info=True)
