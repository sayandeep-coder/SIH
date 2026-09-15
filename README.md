# India Airfare Price Index (APIx)

A backend system that scrapes real airfare prices from Google Flights, cleans and analyzes
that data, and calculates a price index for domestic Indian flight routes — similar to how
a Consumer Price Index tracks inflation, but for airfares.

There's also a Next.js dashboard on top that shows the data live.

This doc explains what the project does, how the pieces fit together, and how to run it
yourself. It's written for a teammate joining the project cold.

---

## 1. What this actually does, in plain words

1. We pick a route (e.g. Kolkata → Mumbai) and a date.
2. A script opens Google Flights in a real browser (via Playwright) and scrapes every
   flight shown — airline, price, times, stops, etc.
3. Those raw prices get cleaned: we throw out broken data, remove duplicates, and flag
   suspiciously high/low prices (but we don't delete them — just flag them).
4. The cleaned prices get saved as "fare observations."
5. We calculate a price index per route: `(today's price / a baseline price) × 100`.
   If the index is 120, fares are 20% more expensive than the baseline.
6. We combine all routes into one overall national index, weighted by how important
   each route is.
7. We do this separately for 5 booking windows: T+1 (tomorrow), T+7, T+15, T+30, T+45
   (i.e. "how much does it cost to book 1 day vs 45 days in advance").
8. All of this is exposed through a REST API, and the dashboard displays it.

Nothing on the dashboard is fake or hardcoded — every number comes from the database via
the API.

---

## 2. Tech stack

| Piece | Tool |
|---|---|
| Backend API | FastAPI (Python) |
| Database | Neon (managed PostgreSQL) — **not run locally**, we connect to a hosted instance |
| ORM | SQLAlchemy 2.x, async, via `asyncpg` |
| Scraper | Playwright (controls a real Chromium browser) |
| Background jobs | Celery, with Redis as the queue |
| Data cleaning / stats | Pandas, NumPy |
| Frontend | Next.js (App Router) + TypeScript, plain CSS (no Tailwind) |

---

## 3. How the pieces talk to each other

```
FastAPI  ──(queues a job)──▶  Redis  ──▶  Celery worker
                                              │
                                              ▼
                                    Playwright opens Chromium
                                              │
                                              ▼
                                   Scrapes Google Flights page
                                              │
                                              ▼
                                    Parses flight cards → raw prices
                                              │
                                              ▼
                              Saved to Neon as "fare_quotes" (raw data)
                                              │
                                              ▼
                        Cleaning pipeline (validate → dedupe → flag outliers)
                                              │
                                              ▼
                             Saved as "fare_observations" (cleaned data)
                                              │
                                              ▼
                              Index calculation reads observations,
                              computes price index, saves "index_values"
                                              │
                                              ▼
                               FastAPI reads all of this and serves it
                                              │
                                              ▼
                                  Next.js dashboard displays it
```

**Important rule we follow:** Playwright never runs directly inside a FastAPI request.
Scraping always goes through Celery (a background job), because it's slow (a few seconds
to tens of seconds) and would block the API otherwise.

The one exception: `POST /api/v1/scraping/quote` runs a scrape synchronously and waits
for the result before responding — useful for "give me live prices right now" but slower
to respond. Everything else queues a background job and you poll for the result.

---

## 4. Project structure

```
app/
  main.py                  # FastAPI app, wires up all the routers
  celery_app.py             # Celery configuration

  api/routes/                # HTTP endpoints (one file per resource)
    scraping.py               # trigger scrapes, check job status, live quotes
    fares.py                   # list raw fare quotes
    routes.py                  # list tracked routes
    airports.py                 # list airports
    index.py                     # the price index endpoints
    quality.py                    # data quality stats

  scrapers/google_flights/    # Everything Google-Flights-specific lives here
    deeplink.py                # builds a Google Flights search URL
    scraper.py                  # drives Playwright, handles retries
    parser.py                    # extracts flight data from the HTML
    selectors.py                  # CSS/ARIA selectors used by the parser
    models.py                      # FlightResult — the parsed-flight shape

  cleaning/                   # Data cleaning pipeline (no DB access — pure functions)
    validator.py                # rejects bad records (missing price, bad currency, etc)
    deduplicator.py              # removes duplicate quotes (vectorized with pandas)
    normalizer.py                 # standardizes currency/price/dates, buckets advance_days
    outlier.py                     # flags statistical outliers (IQR method)

  index_engine/                # Price index math (also pure functions, no DB)
    price_relative.py           # current price ÷ base price × 100
    aggregation.py                # combines many observations into one representative fare
    weights.py                     # normalizes route weights so they sum to 1
    calculator.py                   # combines everything into route + overall index

  services/                    # Orchestration layer — this is what wires DB + logic together
    scraping_service.py          # runs a scrape end-to-end and saves results
    cleaning_service.py           # runs the cleaning pipeline on a scrape's results
    index_service.py               # runs index calculation and saves it

  db/
    models.py                   # SQLAlchemy table definitions
    database.py                   # DB connection/session setup
    repositories/                  # one file per table — all raw SQL queries live here

  tasks/                       # Celery task definitions (the async entry points)
  scheduler/jobs.py             # daily job that queues scrapes for every route/window

  config/settings.py            # reads all the environment variables
  schemas/                      # Pydantic request/response shapes for the API

scripts/
  seed_airports.py              # inserts the list of tracked airports (safe to re-run)
  seed_routes.py                  # inserts the list of tracked routes (safe to re-run)
  seed_index_weights.py            # gives every route an equal weight (safe to re-run)

tests/                        # pytest tests — currently 88 passing

frontend/                     # Next.js dashboard
  app/                          # one folder per page (Overview, Routes, etc.)
  components/Shell.tsx           # shared sidebar/topbar layout
  components/Skeleton.tsx         # loading-skeleton placeholders
  lib/api.ts                       # the only place that calls the backend API
```

**Why it's split this way:** `cleaning/` and `index_engine/` contain no database code at
all — they're just functions that take data in and return data out. That makes them easy
to unit test. All the actual database reading/writing happens in `db/repositories/`.
`services/` is the glue that calls repositories and the pure-logic modules together.

---

## 5. Database (Neon PostgreSQL)

We connect to a hosted Neon Postgres instance — nobody runs Postgres locally. The
connection string lives in `.env` as `DATABASE_URL`.

Main tables:

| Table | What it holds |
|---|---|
| `airports` | IATA codes, city, state |
| `routes` | origin/destination airport pairs we track, plus a `weight` |
| `airlines` | airline code + name (auto-created the first time we see a new airline) |
| `scrape_runs` | one row per scrape attempt — status, timing, error message |
| `fare_quotes` | raw scraped prices, **never modified after insert** |
| `fare_observations` | the cleaned version of a quote — this is what the index uses |
| `data_quality_events` | a log of anything the cleaning pipeline rejected or flagged |
| `index_weights` | how much each route counts toward the overall index |
| `index_values` | the calculated index numbers, one row per (date, route, window) |

Two things worth knowing:

- `advance_days` (on `fare_quotes` and `fare_observations`) can **only** be 1, 7, 15, 30,
  or 45 — that's a database constraint. If a route is scraped for some other number of
  days out, we round to the nearest one of those.
- We never delete or edit a `fare_quotes` row. If something's wrong with it, we just don't
  promote it to a `fare_observations` row, and we log why in `data_quality_events`.

---

## 6. Running it locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Neon Postgres connection string (ask a teammate, or create a free one at neon.tech)
- Redis (local install, or a free hosted one like Redis Cloud)

### Backend setup

```bash
# from the project root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# now edit .env and fill in DATABASE_URL, REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
```

Seed the database (safe to run more than once — it won't create duplicates):

```bash
PYTHONPATH=. python scripts/seed_airports.py
PYTHONPATH=. python scripts/seed_routes.py
PYTHONPATH=. python scripts/seed_index_weights.py
```

Run the API:

```bash
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (FastAPI generates this
automatically from the code).

Run a Celery worker (separate terminal — this is what actually does the scraping):

```bash
PYTHONPATH=. celery -A app.celery_app worker --loglevel=info
```

### Frontend setup

```bash
cd frontend
npm install
# create a .env.local file with:
#   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

Visit `http://localhost:3000`.

**You need the backend running for the dashboard to show anything.** If it's down,
each page shows a "could not reach the API" message instead of crashing.

### Running tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

---

## 7. How to actually trigger a scrape

**Option A — via the dashboard:** go to the "Scrape Runs" page, fill in a route code
(e.g. `CCU-BOM`) and a date, click "Trigger Scrape."

**Option B — via the API directly:**

```bash
# Queue a background scrape (returns immediately with a job_id)
curl -X POST http://localhost:8000/api/v1/scraping/route/CCU-BOM \
  -H "Content-Type: application/json" \
  -d '{"departure_date": "2026-09-20"}'

# Check on it
curl http://localhost:8000/api/v1/scraping/jobs/<job_id>
```

**Option C — get live prices immediately (no job polling, but slower to respond):**

```bash
curl -X POST http://localhost:8000/api/v1/scraping/quote \
  -H "Content-Type: application/json" \
  -d '{"origin": "CCU", "destination": "BOM", "departure_date": "2026-09-20"}'
```

For a scrape to work, the route (`CCU-BOM`) has to already exist in the `routes` table —
run the seed scripts first if you haven't.

**Note on the scraper's browser window:** by default `SCRAPER_HEADLESS=false` in
`.env`, meaning it opens a real visible Chromium window while scraping. That's useful for
watching what's happening / debugging, but it's slower to launch than headless mode. Set
it to `true` for faster, invisible scraping (needed anyway if you deploy this on a server
with no display).

After a scrape finishes, the cleaning pipeline and observation-saving happen
automatically — you don't need to trigger those separately.

To (re)calculate the index after scraping, either wait for the daily scheduled job, or
trigger it directly:

```python
# from a Python shell, with the venv active
from app.tasks.index_tasks import calculate_index_windows
calculate_index_windows.delay()
```

---

## 8. The API, at a glance

All endpoints are under `/api/v1/`. Full interactive docs at `/docs` once the server is
running.

| Endpoint | What it does |
|---|---|
| `GET /airports` | list all tracked airports |
| `GET /routes` | list all tracked routes (with weights) |
| `GET /fares` | list raw fare quotes, filterable by origin/destination/airline/date |
| `GET /index` | the overall price index, broken down by T+1/7/15/30/45 |
| `GET /index/routes` | the price index for each individual route |
| `GET /index/advance-windows` | just returns `[1, 7, 15, 30, 45]` |
| `GET /quality/summary` | valid rate, outlier rate, dedup counts |
| `GET /quality/events` | recent things the cleaning pipeline flagged |
| `POST /scraping/route/{route_code}` | queue a background scrape |
| `GET /scraping/jobs/{job_id}` | check on a queued scrape |
| `GET /scraping/runs` | history of all scrape attempts |
| `POST /scraping/quote` | scrape right now and wait for the prices |

---

## 9. Things to know before you touch the code

- **V1 only scrapes Google Flights.** No other airline sites or OTAs — don't add one
  without discussing it first, the whole scraper package is built around Google Flights'
  specific page structure.
- **The Google Flights deep link uses a `q=` natural-language search** (e.g.
  `"Flights from CCU to BOM on 2026-09-16"`), not the `tfs=` parameter you'd see in a
  real Google Flights URL — that param requires internal Google airport IDs we don't
  have a way to look up, so we use the plain-English search instead. It works reliably.
- **We deliberately never use Google Flights' price calendar.** We tested it — its
  displayed prices don't match the real flight-card prices (off by roughly 2x in our
  testing), so we always do 5 separate searches (one per T+1/7/15/30/45) instead of
  trying to read all 5 from one calendar view.
- **Parsing avoids Google's auto-generated CSS class names** (things like `class="gQ6yfe"`)
  since those change whenever Google redeploys their frontend. Instead the parser reads
  `aria-label` text and semantic attributes, which are much more stable. If scraping
  suddenly breaks, check `app/scrapers/google_flights/selectors.py` first — Google
  probably changed their page structure and the selectors need updating.
- **Scraping is genuinely slow and somewhat flaky at volume.** A single route takes
  roughly 2–5 seconds in headless mode, but can take much longer with a visible browser,
  and running many scrapes back-to-back in one process has occasionally hung (we think
  it's a Neon connection-pool issue under rapid reuse — if you hit this, running each
  scrape as its own separate process works around it).
- **The `index_weights` table currently uses equal weighting** across all routes (every
  route counts the same toward the overall index) — this is a placeholder. Real
  passenger-traffic-based weights would replace this later without needing any code
  changes, since the index math reads from the table, not from hardcoded numbers.
- **The index right now mostly reads ~100** for most routes, because we don't have much
  scrape history yet — the "base" price and "current" price are close to the same thing
  when you've only scraped a route once or twice. This isn't a bug — it needs data
  collected over multiple days to show real movement.
- **`frontend/src/`** is an old, unused prototype (Vite-based) that predates the current
  Next.js app in `frontend/app/`. It's not wired up to anything — ignore it.
- **Docker files exist** (`Dockerfile`, `docker-compose.yml`) but have not actually been
  build-tested — treat them as a starting point, not verified working.

---

## 10. Where to look when something breaks

| Symptom | Look here |
|---|---|
| Scraper returns 0 flights | `app/scrapers/google_flights/parser.py` + `selectors.py` — Google probably changed their HTML |
| A scrape hangs forever | Check `scrape_runs` table for a row stuck on `status='running'`; likely a Neon connection issue, see note above |
| Index values look wrong | `app/index_engine/calculator.py` for the math, `app/services/index_service.py` for how base/current fares are picked |
| Dashboard shows "could not reach the API" | Backend isn't running, or `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` doesn't match where the backend actually is |
| Celery task never runs | Make sure a worker is actually running (`celery -A app.celery_app worker`) and check `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` point at a reachable Redis |
| New route/airport not showing up | Run `scripts/seed_airports.py` / `scripts/seed_routes.py` again — they're safe to re-run |
