"use client";

import { ArrowRightLeft, CheckCircle2, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { SkeletonRows, SkeletonText } from "../../components/Skeleton";
import { api, FareQuote, Route, RouteIndex } from "../../lib/api";

function fmtFare(v: string) {
  return `₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function RoutesPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [routeIndexes, setRouteIndexes] = useState<RouteIndex[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [selectedFares, setSelectedFares] = useState<FareQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [faresLoading, setFaresLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [routesRes, indexesRes] = await Promise.all([
          api.getRoutes(),
          api.getRouteIndexes().catch(() => []),
        ]);
        setRoutes(routesRes);
        setRouteIndexes(indexesRes);
        const routeWithData = routesRes.find((r) => indexesRes.some((ix) => ix.route_id === r.id));
        setSelectedRoute((routeWithData || routesRes[0])?.route_code || null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedRoute) return;
    setFaresLoading(true);
    const [origin, destination] = selectedRoute.split("-");
    api.getFares({ origin, destination, limit: 10 })
      .then(setSelectedFares)
      .catch(() => setSelectedFares([]))
      .finally(() => setFaresLoading(false));
  }, [selectedRoute]);

  const indexByRoute = new Map(routeIndexes.map((r) => [r.route_id, r]));
  const selected = routes.find((r) => r.route_code === selectedRoute);

  return (
    <Shell active="routes">
      <main className="routes-page">
        <div className="route-content">
          <section className="route-title">
            <div>
              <div><span>REGULATORY CORE</span> DGCA / MoSPI CORRIDOR MONITOR</div>
              <h1>Domestic Route Coverage Basket</h1>
              <p>{routes.length} tracked domestic city pairs. Advance purchase indexing (T+1 through T+45) computed from live Google Flights observations.</p>
            </div>
            <div>
              <span><RefreshCw size={13} />{routes.length} routes loaded</span>
              <button className="basket"><CheckCircle2 size={13} />{routeIndexes.length} with index data</button>
            </div>
          </section>

          <section className="route-kpis">
            {[
              ["MONITORED CORRIDORS", `${routes.length}`, "TRACKED"],
              ["CORRIDORS WITH INDEX DATA", `${routeIndexes.length}`, `${routes.length ? ((routeIndexes.length / routes.length) * 100).toFixed(1) : 0}% coverage`],
              ["WEIGHTED BASKET WEIGHT (each)", routes[0]?.weight ? `${(Number(routes[0].weight) * 100).toFixed(2)}%` : "—", "equal-weight seed"],
            ].map((k) => (
              <article className="card" key={k[0]}>
                <span>{k[0]}<i /></span>
                <div>{loading ? <SkeletonText className="sm" /> : <><strong>{k[1]}</strong><b>{k[2]}</b></>}</div>
              </article>
            ))}
          </section>

          <section className="card corridor-table">
            <div className="corridor-toolbar">
              <span>{loading ? "Loading…" : `Showing all ${routes.length} active routes`}</span>
            </div>
            <div className="corridor-scroll">
              <table>
                <thead>
                  <tr>
                    <th>CORRIDOR CODE</th><th>ORIGIN</th><th>DESTINATION</th><th>WEIGHT</th><th>INDEX VALUE</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && <SkeletonRows rows={8} cols={5} />}
                  {!loading && routes.map((r) => {
                    const ix = indexByRoute.get(r.id);
                    return (
                      <tr
                        key={r.id}
                        className={r.route_code === selectedRoute ? "selected-row" : ""}
                        onClick={() => setSelectedRoute(r.route_code)}
                        style={{ cursor: "pointer" }}
                      >
                        <td><b>{r.route_code}</b></td>
                        <td><strong>{r.origin.iata_code}</strong><small>{r.origin.city}</small></td>
                        <td><strong>{r.destination.iata_code}</strong><small>{r.destination.city}</small></td>
                        <td>{r.weight ? `${(Number(r.weight) * 100).toFixed(2)}%` : "—"}</td>
                        <td>{ix ? Number(ix.index_value).toFixed(1) : "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {selected && (
            <section className="card selected-corridor">
              <header>
                <div className="airport-code">{selected.origin.iata_code}</div>
                <ArrowRightLeft size={18} />
                <div>
                  <small>Selected Corridor: {selected.route_code}</small>
                  <h2>{selected.origin.city} ({selected.origin.iata_code}) → {selected.destination.city} ({selected.destination.iata_code})</h2>
                </div>
                <span>{selectedFares.length ? "ACTIVE DEEP DIVE" : "NO DATA YET"}</span>
              </header>

              <div className="latest">
                <h3>Latest Verified Flight Observations ({selected.route_code})</h3>
                <p>Real scraped quotes from Google Flights via Playwright.</p>
                <table>
                  <thead>
                    <tr><th>CARRIER & FLIGHT</th><th>SCHEDULE</th><th>DURATION</th><th>STOPS</th><th>TOTAL FARE</th><th>ADVANCE</th></tr>
                  </thead>
                  <tbody>
                    {faresLoading && <SkeletonRows rows={5} cols={6} />}
                    {!faresLoading && selectedFares.length === 0 && (
                      <tr><td colSpan={6}>No scraped quotes for this route yet.</td></tr>
                    )}
                    {!faresLoading && selectedFares.map((f) => (
                      <tr key={f.id}>
                        <td><b>{f.airline_name || "—"}</b><small>{f.flight_number || ""}</small></td>
                        <td><b>{f.departure_time || "—"}</b></td>
                        <td><b>{f.duration_minutes ? `${Math.floor(f.duration_minutes / 60)}h ${f.duration_minutes % 60}m` : "—"}</b></td>
                        <td>{f.stops === 0 ? "Nonstop" : f.stops ?? "—"}</td>
                        <td><strong>{fmtFare(f.total_fare)}</strong></td>
                        <td>T+{f.advance_days}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </main>
    </Shell>
  );
}
