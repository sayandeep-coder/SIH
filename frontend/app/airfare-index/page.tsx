"use client";

import { CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { Skeleton, SkeletonText } from "../../components/Skeleton";
import { api, IndexSummary, RouteIndex } from "../../lib/api";

const ADVANCE_LABELS: Record<string, [string, string]> = {
  "1": ["T+1", "Tomorrow / Spot Horizon"],
  "7": ["T+7", "1 Week Forward"],
  "15": ["T+15", "2 Weeks"],
  "30": ["T+30", "1 Month"],
  "45": ["T+45", "Long Range"],
};

export default function DetailedIndex() {
  const [summary, setSummary] = useState<IndexSummary | null>(null);
  const [routeIndexes, setRouteIndexes] = useState<RouteIndex[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, r] = await Promise.all([api.getIndex(), api.getRouteIndexes()]);
        setSummary(s);
        setRouteIndexes(r);
      } catch {
        setError("Could not load index data from the API.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const windowEntries = summary ? Object.entries(summary.advance_windows) : [];
  const sortedRoutes = [...routeIndexes].sort(
    (a, b) => Math.abs(Number(b.index_value) - 100) - Math.abs(Number(a.index_value) - 100)
  );

  return (
    <Shell active="index">
      <main>
        <div className="detail-ribbon">
          <div><b>● METHODOLOGY:</b> WEIGHTED MODIFIED LASPEYRES <i>/</i> WEIGHTING: index_weights TABLE (equal-weight seed)</div>
          <div>{loading ? "LOADING…" : error ? <strong style={{ color: "#ba1a1a" }}>{error}</strong> : `ROUTES WITH INDEX DATA: ${routeIndexes.length}`}</div>
        </div>
        <div className="detail-content">
          <section className="detail-title">
            <div>
              <div className="detail-tags"><span>PRICE RELATIVE INDEX</span></div>
              <h1>Airfare Price Index</h1>
              <p>Weighted price-relative index across tracked domestic corridors and advance booking windows, computed from real fare observations.</p>
            </div>
            <div className="detail-actions">
              <span><i />Base: <b>{summary ? Number(summary.base).toFixed(1) : "100.0"}</b></span>
              <span>{summary ? summary.date : "—"}</span>
            </div>
          </section>

          <section className="card trajectory">
            <div className="trajectory-head">
              <div>
                <h2><i />Current Airfare Price Index</h2>
                <p>Weighted average of route-level price relatives (current fare ÷ base-period fare × 100).</p>
              </div>
              <div className="metric-legend">
                <span><i className="blue-line" /><small>AIRFARE INDEX{loading ? <Skeleton width={60} height={16} /> : <b>{summary ? Number(summary.index).toFixed(1) : "—"} pts</b>}</small></span>
              </div>
            </div>
          </section>

          <section className="analytics-grid">
            <article className="card analytic horizons">
              <div className="analytic-head">
                <div><h3>Advance Window Index</h3><p>Overall index computed separately per booking window (T+1 to T+45)</p></div>
              </div>
              <div className="horizon-list">
                {["1", "7", "15", "30", "45"].map((n) => {
                  const [label, sub] = ADVANCE_LABELS[n];
                  const found = windowEntries.find(([k]) => k === n);
                  return (
                    <div key={n}>
                      <div>
                        <b>{label}</b>
                        <strong>{sub}</strong>
                        {loading ? <SkeletonText className="sm" /> : <em>{found ? `${Number(found[1]).toFixed(1)} pts` : "No data yet"}</em>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </article>

            <article className="card analytic contribution">
              <div className="analytic-head">
                <div><h3>Route Index Values</h3><p>Individual route price-relative indices (base 100.0)</p></div>
                <span>{routeIndexes.length} ROUTES</span>
              </div>
              <div className="bar-list">
                {loading && Array.from({ length: 6 }).map((_, i) => (
                  <div key={i}><SkeletonText className="sm" /><Skeleton height={9} /><SkeletonText className="sm" /></div>
                ))}
                {!loading && sortedRoutes.length === 0 && <p style={{ padding: "8px 0", color: "#65748a" }}>No route index data yet — run a scrape and index calculation.</p>}
                {!loading && sortedRoutes.map((r) => {
                  const delta = Number(r.index_value) - 100;
                  return (
                    <div key={r.route_id}>
                      <b>{r.route_code}</b>
                      <span><i className={delta < 0 ? "negative" : ""} style={{ width: `${Math.min(100, Math.abs(delta) * 3 + 10)}%` }} /></span>
                      <strong className={delta < 0 ? "negative-text" : ""}>{delta > 0 ? "+" : ""}{delta.toFixed(1)} pts</strong>
                    </div>
                  );
                })}
              </div>
            </article>
          </section>

          <section className="compliance">
            <CheckCircle2 size={16} />
            <p><strong>Methodology:</strong> route_index = (current representative fare / base-period representative fare) × 100, aggregated across routes using weights from the index_weights table, normalized to sum to 1.</p>
          </section>
        </div>
      </main>
    </Shell>
  );
}
