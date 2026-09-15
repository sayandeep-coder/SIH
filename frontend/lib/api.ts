const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export interface Airport {
  id: string;
  iata_code: string;
  city: string;
  state: string | null;
  is_active: boolean;
}

export interface Route {
  id: string;
  route_code: string;
  weight: string | null;
  is_active: boolean;
  origin: Airport;
  destination: Airport;
}

export interface FareQuote {
  id: string;
  route_id: string;
  route_code: string;
  airline_id: string | null;
  airline_code: string | null;
  airline_name: string | null;
  source: string;
  flight_number: string | null;
  departure_date: string;
  departure_time: string | null;
  advance_days: number;
  total_fare: string;
  currency: string;
  availability: boolean;
  stops: number | null;
  duration_minutes: number | null;
  scraped_at: string;
}

export interface IndexSummary {
  date: string;
  index: string;
  base: string;
  advance_windows: Record<string, string>;
}

export interface RouteIndex {
  route_id: string;
  route_code: string;
  index_value: string;
  base_value: string;
}

export interface ScrapeRun {
  id: string;
  source: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  records_found: number;
  records_valid: number;
  error_message: string | null;
  route_code: string | null;
  departure_date: string | null;
}

export interface QualitySummary {
  total_quotes: number;
  total_observations: number;
  valid_observations: number;
  outlier_observations: number;
  valid_rate: number;
  outlier_rate: number;
  duplicate_events: number;
  validation_failed_events: number;
}

export interface QualityEvent {
  id: string;
  quote_id: string | null;
  event_type: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface ScrapeJobResponse {
  job_id: string;
  status: string;
}

export interface QuoteFlightResult {
  airline_name: string;
  airline_code: string | null;
  flight_number: string | null;
  origin: string;
  destination: string;
  departure_date: string;
  departure_time: string | null;
  arrival_date: string | null;
  arrival_time: string | null;
  duration_minutes: number | null;
  stops: number;
  price: string;
  currency: string;
  emissions_kg: number | null;
  source: string;
}

export interface QuoteResponse {
  route_code: string;
  departure_date: string;
  flights_found: number;
  flights: QuoteFlightResult[];
}

export const api = {
  getAirports: () => apiGet<Airport[]>("/api/v1/airports"),
  getRoutes: () => apiGet<Route[]>("/api/v1/routes"),
  getFares: (params?: {
    origin?: string;
    destination?: string;
    airline?: string;
    departure_date?: string;
    advance_days?: number;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) qs.set(key, String(value));
      }
    }
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiGet<FareQuote[]>(`/api/v1/fares${suffix}`);
  },
  getIndex: (date?: string) =>
    apiGet<IndexSummary>(`/api/v1/index${date ? `?date=${date}` : ""}`),
  getRouteIndexes: (params?: { route_code?: string; advance_days?: number }) => {
    const qs = new URLSearchParams();
    if (params?.route_code) qs.set("route_code", params.route_code);
    if (params?.advance_days !== undefined) qs.set("advance_days", String(params.advance_days));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiGet<RouteIndex[]>(`/api/v1/index/routes${suffix}`);
  },
  getAdvanceWindows: () => apiGet<{ windows: number[] }>("/api/v1/index/advance-windows"),
  getScrapeRuns: (limit = 50) => apiGet<ScrapeRun[]>(`/api/v1/scraping/runs?limit=${limit}`),
  getQualitySummary: () => apiGet<QualitySummary>("/api/v1/quality/summary"),
  getQualityEvents: (limit = 50) => apiGet<QualityEvent[]>(`/api/v1/quality/events?limit=${limit}`),
  triggerScrape: (routeCode: string, departureDate: string) =>
    apiPost<ScrapeJobResponse>(`/api/v1/scraping/route/${routeCode}`, { departure_date: departureDate }),
  getQuote: (origin: string, destination: string, departureDate: string) =>
    apiPost<QuoteResponse>("/api/v1/scraping/quote", {
      origin,
      destination,
      departure_date: departureDate,
    }),
};
