"use client";

import { CheckCircle2, Scale } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { SkeletonText } from "../../components/Skeleton";
import { api, IndexSummary, QualitySummary, Route, ScrapeRun } from "../../lib/api";

// ---- Government figures: sourced from the official MoSPI "FAQs on CPI 2024 Series" PDF ----
// https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf
const GOVT_ONLINE_UPDATES_PER_MONTH = 4.3; // Q8: airfare prices collected weekly via online platforms (~4.3 weeks/month)
const GOVT_PUBLICATION_LAG_DAYS = 12; // official monthly release convention: data for month t released ~12th of month t+1
const GOVT_ROUTES_BROKEN_OUT = 0; // airfare is one COICOP item inside "Transport" division — no route-level publication
const GOVT_BOOKING_WINDOWS = 0; // no lead-time / advance-booking dimension published
const GOVT_ONLINE_TOWNS = 12; // Q7: 12 online markets across 12 towns (population > 25 lakh) — where airfare/telecom/OTT are priced
const GOVT_TRANSPORT_WEIGHT_PCT = 8.796; // Division-wise weight table, Combined, CPI 2024 series — "Transport"
const GOVT_ELEMENTARY_FORMULA = "Jevons index"; // Q20
const GOVT_HIGHER_FORMULA = "Young / Modified Laspeyres"; // Q21

function pctChange(ours: number, govt: number, higherIsBetter = true): number | null {
  if (govt === 0) return null; // undefined multiple when government baseline is 0 — show as n/a, not a fabricated %
  const delta = higherIsBetter ? ours - govt : govt - ours;
  return (delta / govt) * 100;
}

function fmtSigned(v: number | null, digits = 0): string {
  if (v === null) return "n/a";
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(digits)}%`;
}

function fmtNum(v: number, digits = 0): string {
  return v.toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

/** Thin horizontal bar pair for one metric — govt vs ours, same scale, labelled ends. */
function BarRow({
  label,
  govt,
  ours,
  unit,
  loading,
  maxOverride,
}: {
  label: string;
  govt: number;
  ours: number | null;
  unit: string;
  loading: boolean;
  maxOverride?: number;
}) {
  const safeOurs = ours ?? 0;
  const max = maxOverride ?? Math.max(govt, safeOurs, 1);
  const govtPct = Math.min(100, (govt / max) * 100);
  const oursPct = Math.min(100, (safeOurs / max) * 100);
  return (
    <div className="compare-bar-row">
      <div className="compare-bar-label">{label}</div>
      <div className="compare-bar-track">
        <div className="compare-bar-fill govt" style={{ width: `${govtPct}%` }} />
        <span className="compare-bar-value govt-value">
          {fmtNum(govt, govt < 10 ? 1 : 0)} {unit}
        </span>
      </div>
      <div className="compare-bar-track">
        {loading ? (
          <SkeletonText className="sm" />
        ) : (
          <>
            <div className="compare-bar-fill ours" style={{ width: `${oursPct}%` }} />
            <span className="compare-bar-value ours-value">
              {ours === null ? "—" : `${fmtNum(ours, ours < 10 ? 1 : 0)} ${unit}`}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

export default function Solution() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [summary, setSummary] = useState<IndexSummary | null>(null);
  const [quality, setQuality] = useState<QualitySummary | null>(null);
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getRoutes(),
      api.getIndex().catch(() => null),
      api.getQualitySummary().catch(() => null),
      api.getScrapeRuns(50).catch(() => []),
    ])
      .then(([r, s, q, ru]) => {
        setRoutes(r);
        setSummary(s);
        setQuality(q);
        setRuns(ru);
      })
      .finally(() => setLoading(false));
  }, []);

  const activeRoutes = routes.filter((r) => r.is_active).length;
  const successRuns = runs.filter((r) => r.status === "success").length;
  const successRatePct = runs.length ? (successRuns / runs.length) * 100 : null;
  const lastRunAt = runs[0]?.completed_at || runs[0]?.started_at || null;
  const freshnessHours = lastRunAt
    ? Math.max(0, (Date.now() - new Date(lastRunAt).getTime()) / 3600000)
    : null;
  const rawQuoteCount = quality?.total_quotes ?? null;
  const windowCount = summary ? Object.keys(summary.advance_windows).length : 0;
  const indexValue = summary ? Number(summary.index) : null;

  // Scrape runs actually observed in this window, used as a live proxy for "updates".
  const runsInWindow = runs.length;

  type Metric = {
    key: string;
    label: string;
    unit: string;
    govt: number;
    ours: number | null;
    higherIsBetter: boolean;
    note?: string;
  };

  const metrics: Metric[] = [
    { key: "routes", label: "Routes tracked individually", unit: "routes", govt: GOVT_ROUTES_BROKEN_OUT, ours: activeRoutes, higherIsBetter: true },
    { key: "windows", label: "Booking-lead-time windows / route", unit: "windows", govt: GOVT_BOOKING_WINDOWS, ours: windowCount, higherIsBetter: true },
    { key: "lag", label: "Publication lag", unit: "days", govt: GOVT_PUBLICATION_LAG_DAYS, ours: freshnessHours === null ? null : Number((freshnessHours / 24).toFixed(2)), higherIsBetter: false },
    { key: "updates", label: "Price updates / month", unit: "updates", govt: GOVT_ONLINE_UPDATES_PER_MONTH, ours: runsInWindow, higherIsBetter: true, note: "govt figure = weekly online collection (~4.3×/month) per MoSPI FAQ Q8" },
    { key: "obs", label: "Raw price observations logged", unit: "records", govt: 0, ours: rawQuoteCount, higherIsBetter: true, note: "not published at item level by MoSPI" },
    { key: "success", label: "Pipeline success rate", unit: "%", govt: 0, ours: successRatePct === null ? null : Number(successRatePct.toFixed(1)), higherIsBetter: true, note: "not published by MoSPI" },
  ];

  return (
    <Shell active="solution">
      <main className="method-page">
        <div className="method-ribbon">
          <span><Scale size={13} />GOVERNMENT DATA VS OUR DATA</span>
          <span>Government cells: MoSPI CPI 2024 FAQ (public PDF) · Our cells: live from this dashboard&apos;s own API</span>
          <b>{loading ? "…" : `${activeRoutes} routes · index ${indexValue !== null ? indexValue.toFixed(2) : "—"}`}</b>
        </div>
        <div className="method-content">
          <section className="method-title">
            <div>
              <span>THE SOLUTION, SIDE BY SIDE</span>
              <h1>Government CPI vs APIx — sourced, number for number</h1>
              <p>
                Government-side numbers are quoted verbatim from MoSPI&apos;s own &quot;FAQs on CPI 2024
                Series&quot; document and its published division-weight table — not paraphrased, not
                estimated. Our-side numbers are fetched live from this project&apos;s own backend on every
                page load. Where MoSPI does not publish a figure at item level, that cell reads 0 / not
                published rather than a guess.
              </p>
            </div>
          </section>

          <section className="card method-section executive">
            <header><b>01</b><h2>Headline figures</h2><span>AT A GLANCE</span></header>
            <div className="executive-body">
              <div>
                <div className="mandate-stats" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                  <span>
                    <small>ROUTES, GOVT VS OURS</small>
                    {loading ? <SkeletonText className="sm" /> : <b>0 vs {activeRoutes}</b>}
                    <p>MoSPI publishes one national airfare figure inside &quot;Transport&quot;; we index every route.</p>
                  </span>
                  <span>
                    <small>BOOKING WINDOWS, GOVT VS OURS</small>
                    {loading ? <SkeletonText className="sm" /> : <b>0 vs {windowCount}</b>}
                    <p>No lead-time dimension in CPI vs T+1…T+{windowCount ? [1, 7, 15, 30, 45][windowCount - 1] ?? 45 : 45} here.</p>
                  </span>
                  <span>
                    <small>PUBLICATION LAG, GOVT VS OURS</small>
                    {loading ? (
                      <SkeletonText className="sm" />
                    ) : (
                      <b>{GOVT_PUBLICATION_LAG_DAYS}d vs {freshnessHours === null ? "—" : `${freshnessHours.toFixed(1)}h`}</b>
                    )}
                    <p>Govt: released ~12th of the following month. Ours: since the last completed scrape.</p>
                  </span>
                  <span>
                    <small>TRANSPORT DIVISION WEIGHT (GOVT)</small>
                    <b>{GOVT_TRANSPORT_WEIGHT_PCT}%</b>
                    <p>Airfare is one item inside this — not isolated in the public weight table.</p>
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section className="card method-section governance">
            <header><b>02</b><h2>Metric by metric</h2><span>BAR COMPARISON — SAME SCALE, GOVERNMENT VS OURS</span></header>
            <div className="compare-bars">
              {metrics.map((m) => (
                <BarRow
                  key={m.key}
                  label={m.label}
                  govt={m.govt}
                  ours={m.ours}
                  unit={m.unit}
                  loading={loading}
                />
              ))}
            </div>
            <div className="compare-legend">
              <span><i className="dot govt" />Government CPI (MoSPI, published)</span>
              <span><i className="dot ours" />Our APIx (live)</span>
            </div>
          </section>

          <section className="card method-section governance">
            <header><b>03</b><h2>Full table</h2><span>EVERY METRIC, EVERY NUMBER, EVERY SOURCE</span></header>
            <div className="method-table">
              <table>
                <thead>
                  <tr>
                    <th>METRIC</th>
                    <th className="tone0">GOVERNMENT CPI</th>
                    <th className="tone3">OUR APIx (live)</th>
                    <th>CHANGE</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m) => {
                    const change = m.ours === null ? null : pctChange(m.ours, m.govt, m.higherIsBetter);
                    return (
                      <tr key={m.key}>
                        <td>
                          <b>{m.label}</b>
                          {m.note && <div style={{ fontSize: "7px", color: "#94a3b8", marginTop: 2 }}>{m.note}</div>}
                        </td>
                        <td><b>{fmtNum(m.govt, m.govt < 10 ? 2 : 0)}</b> {m.unit}</td>
                        <td>
                          {loading ? (
                            <SkeletonText className="sm" />
                          ) : (
                            <>
                              <b>{m.ours === null ? "—" : fmtNum(m.ours, m.ours < 10 ? 2 : 0)}</b> {m.ours !== null && m.unit}
                            </>
                          )}
                        </td>
                        <td className="tone3"><b>{loading ? "…" : fmtSigned(change)}</b></td>
                      </tr>
                    );
                  })}
                  <tr>
                    <td><b>Elementary index formula</b></td>
                    <td>{GOVT_ELEMENTARY_FORMULA}</td>
                    <td>Median of cleaned, non-outlier fares</td>
                    <td>—</td>
                  </tr>
                  <tr>
                    <td><b>Higher-level index formula</b></td>
                    <td>{GOVT_HIGHER_FORMULA}</td>
                    <td>Weighted average of route indices</td>
                    <td>—</td>
                  </tr>
                  <tr>
                    <td><b>Online price-collection towns</b></td>
                    <td>{GOVT_ONLINE_TOWNS} towns (population &gt; 25 lakh)</td>
                    <td>{loading ? <SkeletonText className="sm" /> : `${activeRoutes} routes, nationwide`}</td>
                    <td>—</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <footer>
              <span>Government source: MoSPI &quot;Frequently Asked Questions (FAQs) on CPI 2024 Series&quot; (Q7, Q8, Q14, Q20, Q21, Q27) and the CPI 2024 Division-wise weight table — mospi.gov.in</span>
              <b>Our source: GET /api/v1/index, /api/v1/routes, /api/v1/quality/summary, /api/v1/scraping/runs — fetched live on this page load</b>
            </footer>
          </section>

          <section className="method-legal">
            <CheckCircle2 size={15} />
            <span>
              MoSPI&apos;s CPI 2024 series already collects airfare weekly via online platforms (Q27) —
              a real modernisation from the old paper survey. What it still does not publish is
              route-level or booking-window-level detail: one national airfare figure, inside one
              division, once a month. That is the specific gap this project targets, not a claim that
              official CPI collection is manual or outdated end-to-end.
            </span>
          </section>
        </div>
      </main>
    </Shell>
  );
}
