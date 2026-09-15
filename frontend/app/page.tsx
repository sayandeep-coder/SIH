"use client";

import { Database, GitBranch, RefreshCw, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../components/Shell";
import { Skeleton, SkeletonRows, SkeletonText } from "../components/Skeleton";
import { api, FareQuote, IndexSummary, Route, ScrapeRun } from "../lib/api";

function fmtFare(v: string) {
  return `₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function Overview() {
  const [spin, setSpin] = useState(false);
  const [index, setIndex] = useState<IndexSummary | null>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [fares, setFares] = useState<FareQuote[]>([]);
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [indexRes, routesRes, faresRes, runsRes] = await Promise.all([
        api.getIndex().catch(() => null),
        api.getRoutes(),
        api.getFares({ limit: 5 }),
        api.getScrapeRuns(7),
      ]);
      setIndex(indexRes);
      setRoutes(routesRes);
      setFares(faresRes);
      setRuns(runsRes);
      setError(null);
    } catch {
      setError("Could not reach the API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const observedRoutes = new Set(fares.map((f) => f.route_id)).size;
  const activeRoutes = routes.filter((r) => r.is_active).length;
  const successRuns = runs.filter((r) => r.status === "success").length;
  const successRate = runs.length ? ((successRuns / runs.length) * 100).toFixed(1) : "—";
  const lastScrapeAt = runs[0]?.completed_at || runs[0]?.started_at;
  const freshnessMinutes = lastScrapeAt
    ? Math.max(0, Math.round((Date.now() - new Date(lastScrapeAt).getTime()) / 60000))
    : null;

  const stats = [
    ["Current Airfare Index", index ? Number(index.index).toFixed(1) : "—", `Base ${index ? Number(index.base).toFixed(1) : "100.0"}`, "T+1 window (latest)", index ? `Base: ${Number(index.base).toFixed(1)}` : ""],
    ["Routes Tracked", String(activeRoutes), `${observedRoutes} with data`, "Active domestic city pairs", ""],
    ["Fare Quotes (recent sample)", String(fares.length), "", "Latest observations returned", ""],
    ["Scrape Success Rate", successRate === "—" ? "—" : `${successRate}%`, "", `Last ${runs.length} runs`, ""],
    ["Data Freshness", freshnessMinutes === null ? "—" : `${freshnessMinutes} min`, freshnessMinutes !== null && freshnessMinutes < 15 ? "LIVE" : "", "Since last completed scrape", ""],
  ];

  return (
    <Shell active="overview">
      <main>
        <div className="telemetry">
          <div>
            <span><i />SOVEREIGN PIPELINE: ACTIVE SURVEILLANCE</span>
            <em>/</em>
            <span>BASE PERIOD: {index ? `INDEX = ${Number(index.base).toFixed(1)}` : "—"}</span>
          </div>
          <div>
            <span>CORRIDORS: <b>{activeRoutes} tracked</b></span>
            {error && <strong style={{ color: "#ba1a1a" }}>{error}</strong>}
          </div>
        </div>
        <div className="content">
          <section className="card hero">
            <div>
              <div className="eyebrow"><span>MoSPI CP-AV09</span><b>NATIONAL DOMESTIC CIVIL AVIATION BASKET</b></div>
              <h1>Airfare Price Index</h1>
              <p>Real-time monitoring of domestic airfare movements across India<br /> (MoSPI CPI Augmentation Module)</p>
            </div>
            <div className="hero-actions">
              <span><RefreshCw size={14} />{new Date().toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
              <button className="refresh" onClick={() => { setSpin(true); load().finally(() => setTimeout(() => setSpin(false), 600)); }}>
                <RefreshCw className={spin ? "spin" : ""} size={16} />Refresh Data
              </button>
            </div>
          </section>

          <section className="kpi-grid">
            {stats.map((s, i) => (
              <article className="card kpi" key={s[0]}>
                <div className="kpi-title">
                  <span>{s[0]}</span>
                  {i === 3 ? <Zap size={14} /> : i === 2 ? <Database size={14} /> : i === 1 ? <GitBranch size={14} /> : <i />}
                </div>
                <div className="kpi-value">
                  {loading ? <Skeleton width={70} height={27} /> : <strong>{s[1]}</strong>}
                  {!loading && s[2] && <b className={i === 1 || i === 2 ? "blue" : "green"}>{s[2]}</b>}
                </div>
                <div className="kpi-foot"><span>{s[3]}</span><b>{s[4]}</b></div>
              </article>
            ))}
          </section>

          <section className="lower-grid">
            <article className="card routes-card">
              <div className="card-heading">
                <div><h2>Latest Fare Quotes</h2><p>Most recently scraped observations across tracked corridors</p></div>
                <span className="pill subtle">Live from API</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>CORRIDOR</th><th>AIRLINE</th><th>FARE</th><th>ADVANCE WINDOW</th></tr></thead>
                  <tbody>
                    {loading && <SkeletonRows rows={5} cols={4} />}
                    {fares.length === 0 && !loading && (
                      <tr><td colSpan={4}>No fare data yet — trigger a scrape to populate this.</td></tr>
                    )}
                    {fares.map((f) => (
                      <tr key={f.id}>
                        <td><b>{f.route_code}</b></td>
                        <td>{f.airline_name || "—"}</td>
                        <td>{fmtFare(f.total_fare)}</td>
                        <td>T+{f.advance_days}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
            <article className="card pipeline">
              <div className="card-heading">
                <div><h2>Recent Scrape Runs</h2><p>Latest Playwright/Celery execution history</p></div>
                <span className={runs.some((r) => r.status === "failed") ? "" : "healthy"}>
                  {runs.length ? `${successRuns}/${runs.length} SUCCESS` : "NO RUNS YET"}
                </span>
              </div>
              <div className="steps">
                {loading && Array.from({ length: 4 }).map((_, i) => (
                  <div className="step" key={i}>
                    <i />
                    <div>
                      <div><SkeletonText /><SkeletonText className="sm" /></div>
                    </div>
                  </div>
                ))}
                {!loading && runs.map((r) => (
                  <div className={`step ${r.status === "failed" ? "" : ""}`} key={r.id}>
                    <i />
                    <div>
                      <div>
                        <strong>{r.route_code || r.id.slice(0, 8)}</strong>
                        <span>{new Date(r.started_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
                      </div>
                      <small>
                        <span>{r.status === "success" ? `${r.records_valid} quotes ingested` : r.error_message || r.status}</span>
                        <b>{r.status.toUpperCase()}</b>
                      </small>
                    </div>
                  </div>
                ))}
                {!loading && runs.length === 0 && <p style={{ padding: "12px 0", color: "#65748a" }}>No scrape runs recorded yet.</p>}
              </div>
            </article>
          </section>
        </div>
      </main>
    </Shell>
  );
}
