"use client";

import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { SkeletonRows, SkeletonText } from "../../components/Skeleton";
import { api, QualityEvent, QualitySummary } from "../../lib/api";

export default function DataQuality() {
  const [summary, setSummary] = useState<QualitySummary | null>(null);
  const [events, setEvents] = useState<QualityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getQualitySummary(), api.getQualityEvents(30)])
      .then(([s, e]) => {
        setSummary(s);
        setEvents(e);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <Shell active="quality">
      <main className="quality-page">
        <div className="quality-content">
          <section className="card quality-head">
            <div>
              <div>
                <h1>Data Quality & Statistical Governance</h1>
                <span><ShieldCheck size={13} />IQR outlier detection · dedup · validation</span>
              </div>
              <p>Cleaning pipeline: validation → normalization → deduplication → IQR outlier flagging → fare_observations.</p>
            </div>
          </section>

          <section className="quality-kpis">
            {[
              ["VALID OBSERVATIONS RATE", summary ? `${(summary.valid_rate * 100).toFixed(1)}%` : "—", `${summary?.valid_observations ?? 0} of ${summary?.total_observations ?? 0}`],
              ["STATISTICAL OUTLIERS (IQR)", summary ? `${(summary.outlier_rate * 100).toFixed(1)}%` : "—", `${summary?.outlier_observations ?? 0} flagged`],
              ["DUPLICATE QUOTES SCRUBBED", String(summary?.duplicate_events ?? 0), "dropped before observation"],
              ["VALIDATION FAILURES", String(summary?.validation_failed_events ?? 0), "rejected quotes"],
            ].map((k) => (
              <article className="card" key={k[0]}>
                <header>{k[0]}<i /></header>
                <div>{loading ? <SkeletonText /> : <strong>{k[1]}</strong>}</div>
                <footer><span>{loading ? "" : k[2]}</span></footer>
              </article>
            ))}
          </section>

          <section className="quality-grid">
            <article className="card checks">
              <header><h2>Pipeline Stages</h2></header>
              {[
                ["Validation", "Rejects missing route, invalid price/currency/date, implausible duration/stops.", `${summary?.total_quotes ?? 0} quotes checked`],
                ["Deduplication", "Vectorized pandas dedup on route/airline/flight/departure/fare key, first-seen wins.", `${summary?.duplicate_events ?? 0} duplicates dropped`],
                ["Outlier Detection", "IQR (Tukey fence, 1.5×IQR) within each (route, advance_days) group.", `${summary?.outlier_observations ?? 0} flagged, not removed`],
                ["Fare Observations", "Clean, deduplicated, flagged records used for index calculation.", `${summary?.total_observations ?? 0} observations`],
              ].map((c) => (
                <div key={c[0]}>
                  <span><b>{c[0]}</b><small>{c[1]}</small></span>
                  {loading ? <SkeletonText className="sm" /> : <strong>{c[2]}</strong>}
                </div>
              ))}
            </article>
            <article className="card exceptions">
              <header>
                <div><h2>Recent Quality Events</h2><p>Non-conformant records flagged during cleaning</p></div>
                <span>{loading ? "…" : `${events.length} SHOWN`}</span>
              </header>
              <table>
                <thead><tr><th>TIMESTAMP</th><th>EVENT</th><th>SEVERITY</th><th>MESSAGE</th></tr></thead>
                <tbody>
                  {loading && <SkeletonRows rows={6} cols={4} />}
                  {!loading && events.length === 0 && <tr><td colSpan={4}>No quality events recorded yet.</td></tr>}
                  {!loading && events.map((e) => (
                    <tr key={e.id}>
                      <td>{new Date(e.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</td>
                      <td><b>{e.event_type}</b></td>
                      <td><span className={e.severity}>{e.severity.toUpperCase()}</span></td>
                      <td>{e.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </article>
          </section>
        </div>
      </main>
    </Shell>
  );
}
