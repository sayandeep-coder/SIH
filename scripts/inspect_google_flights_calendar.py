"""One-off investigation script: does Google Flights' tfs= results page expose
a date-wise price calendar we can scrape for T+1/T+7/T+15/T+30/T+45 fare
discovery, and does the calendar's price match what the flight-result cards
show for that same date?

This is a prototype/investigation tool, not production code. It is not
wired into the scraper package and makes no assumptions about calendar
prices being equivalent to detailed fare observations.

Usage:
    python scripts/inspect_google_flights_calendar.py
"""

import asyncio
import re
from datetime import date, timedelta

from playwright.async_api import async_playwright

SCRAPE_DATE = date(2026, 9, 15)
ADVANCE_WINDOWS = (1, 7, 15, 30, 45)
TARGET_DATES = [SCRAPE_DATE + timedelta(days=n) for n in ADVANCE_WINDOWS]

# Known-good tfs= deeplink for CCU -> BOM on 2026-09-16 (one-way), supplied
# as reference. The calendar it renders covers many nearby dates regardless
# of which single date the tfs= param encodes.
REFERENCE_URL = (
    "https://www.google.com/travel/flights/search"
    "?tfs=CBwQAhooEgoyMDI2LTA5LTE2agwIAhIIL20vMGN2dzlyDAgDEggvbS8wNHZtcEABSAFwAYIBCwj___________8BmAEC"
    "&tfu=EgYIABABGAA&hl=en&gl=IN"
)

CALENDAR_GRIDCELL_SELECTOR = "div[role='gridcell'][data-iso]"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Opening: {REFERENCE_URL}\n")
        await page.goto(REFERENCE_URL, wait_until="domcontentloaded")

        # Q1/Q4: is the calendar present without any extra interaction?
        try:
            await page.wait_for_selector(CALENDAR_GRIDCELL_SELECTOR, timeout=10000)
            calendar_present_on_load = True
        except Exception:
            calendar_present_on_load = False

        print(f"Q1. Calendar grid present in DOM on load: {calendar_present_on_load}")

        if not calendar_present_on_load:
            print("Calendar not found without interaction. Trying to click the departure-date field...")
            date_field = page.locator("input[aria-label='Departure']").first
            if await date_field.count() > 0:
                await date_field.click()
                await page.wait_for_selector(CALENDAR_GRIDCELL_SELECTOR, timeout=10000)
                calendar_present_on_load = True
                print("Calendar appeared after clicking the departure-date field.")

                # The grid renders immediately but prices are fetched async
                # and populated into cells afterward; poll until they show up
                # (or give up after a timeout) instead of reading too early.
                print("Waiting for calendar cell prices to populate...")
                for _ in range(20):
                    priced = await page.query_selector("[aria-label*='Cheapest price'], [aria-label*='Indian rupees']")
                    if priced is not None:
                        break
                    await page.wait_for_timeout(500)
                await page.wait_for_timeout(1000)
            else:
                print("Could not locate a departure-date field to open the calendar.")
                await browser.close()
                return

        # Q2/Q3: extract every date -> price pair exposed in gridcells.
        cells = await page.query_selector_all(CALENDAR_GRIDCELL_SELECTOR)
        print(f"\nFound {len(cells)} calendar day cells in the DOM.\n")

        calendar_prices: dict[str, dict] = {}
        for cell in cells:
            iso_date = await cell.get_attribute("data-iso")
            if not iso_date:
                continue

            price_el = await cell.query_selector("[aria-label*='Indian rupees']")
            if price_el is None:
                continue

            price_aria = await price_el.get_attribute("aria-label")
            price_text = (await price_el.inner_text()).strip()

            exact_match = re.search(r"(\d+)\s+Indian rupees", price_aria or "")
            exact_price = int(exact_match.group(1)) if exact_match else None
            is_cheapest = "cheapest price" in (price_aria or "").lower()

            calendar_prices[iso_date] = {
                "exact_price_from_aria": exact_price,
                "displayed_text": price_text,
                "marked_cheapest": is_cheapest,
            }

        print("Calendar prices found (first 15, sorted by date):\n")
        for iso_date in sorted(calendar_prices)[:15]:
            info = calendar_prices[iso_date]
            print(
                f"{iso_date} -> {info['displayed_text']} "
                f"(exact: {info['exact_price_from_aria']}, cheapest_flag={info['marked_cheapest']})"
            )

        # Q6 (part 1): specifically check whether our 5 target advance-window
        # dates are present in the calendar.
        print(f"\n--- Checking target advance-window dates (scrape_date={SCRAPE_DATE}) ---\n")
        for n, target in zip(ADVANCE_WINDOWS, TARGET_DATES):
            iso = target.isoformat()
            info = calendar_prices.get(iso)
            if info is None:
                print(f"T+{n:<3} {iso}: NOT FOUND in rendered calendar range")
            else:
                print(
                    f"T+{n:<3} {iso}: {info['displayed_text']} "
                    f"(exact={info['exact_price_from_aria']}, cheapest={info['marked_cheapest']})"
                )

        await page.screenshot(path="data/raw/calendar_investigation.png", full_page=False)
        print("\nScreenshot saved to data/raw/calendar_investigation.png\n")

        # Q6/Q7: does the calendar price for the currently-selected date
        # (2026-09-16, already loaded as the initial results page before we
        # opened the calendar) match the cheapest flight-card price for that
        # same date? Compare against what our real parser found earlier for
        # this exact route/date rather than re-navigating (re-navigating
        # after opening the calendar risks landing on a different results
        # view, as seen in an earlier run of this script).
        print("--- Q6: does the calendar price match the cheapest flight-card price? ---\n")
        selected_date = date(2026, 9, 16)
        calendar_entry = calendar_prices.get(selected_date.isoformat())
        print(f"Calendar price for {selected_date.isoformat()}: {calendar_entry}")
        print(
            "Compare this against the cheapest flight-card price for the same "
            "route/date obtained via the normal scraper (run separately) to "
            "check for equivalence — see report."
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
