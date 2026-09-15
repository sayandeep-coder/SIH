"use client";

import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { Skeleton, SkeletonRows } from "../../components/Skeleton";
import { api, FareQuote } from "../../lib/api";

function fmtFare(v: string) {
  return `₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function FareObservations() {
  const [quotes, setQuotes] = useState<FareQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getFares({ limit: 200 }).then(setQuotes).finally(() => setLoading(false));
  }, []);

  const filtered = search
    ? quotes.filter(
        (q) =>
          q.flight_number?.toLowerCase().includes(search.toLowerCase()) ||
          q.route_code.toLowerCase().includes(search.toLowerCase()) ||
          q.airline_name?.toLowerCase().includes(search.toLowerCase())
      )
    : quotes;

  return (
    <Shell active="observations">
      <main className="observations-page">
        <section className="obs-hero">
          <div>
            <div className="obs-kicker"><span>FARE OBSERVATIONS</span></div>
            <h1>Fare Observations Explorer</h1>
            <p>Raw fare quotes captured via automated Playwright/Google Flights scraping.</p>
          </div>
          <div className="obs-actions">
            <span><i /><small>TOTAL RETRIEVED{loading ? <Skeleton width={50} height={12} /> : <b>{quotes.length} quotes</b>}</small></span>
          </div>
        </section>

        <div className="obs-content">
          <section className="card obs-filters">
            <div className="obs-filter-bottom">
              <label>
                <Search size={14} />
                <input
                  placeholder="Search by route, flight number, or airline…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </label>
            </div>
          </section>

          <section className="card quote-matrix">
            <header>
              <div><strong>QUOTE MATRIX</strong><span>•</span><span>Sorted by: scraped_at (desc)</span></div>
            </header>
            <div className="quote-scroll">
              <table>
                <thead>
                  <tr>
                    {["TIMESTAMP", "ROUTE", "CARRIER & FLIGHT", "SCHED. (DEP)", "HORIZON", "STOPS/DUR", "TOTAL FARE"].map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {loading && <SkeletonRows rows={10} cols={7} />}
                  {!loading && filtered.length === 0 && (
                    <tr><td colSpan={7}>No fare observations match your search.</td></tr>
                  )}
                  {!loading && filtered.map((q) => (
                    <tr key={q.id}>
                      <td>{new Date(q.scraped_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</td>
                      <td><b>{q.route_code}</b></td>
                      <td><strong>{q.airline_name || "—"}</strong><small>{q.flight_number || ""}</small></td>
                      <td>{q.departure_time || "—"}</td>
                      <td><span className="horizon">T+{q.advance_days}</span></td>
                      <td>{q.stops === 0 ? "Nonstop" : q.stops ?? "—"}{q.duration_minutes ? ` · ${Math.floor(q.duration_minutes / 60)}h ${q.duration_minutes % 60}m` : ""}</td>
                      <td><b>{fmtFare(q.total_fare)}</b></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <footer><span>Showing <b>{filtered.length}</b> of <b>{quotes.length}</b> observations (most recent 200 fetched)</span></footer>
          </section>
        </div>
      </main>
    </Shell>
  );
}
