"use client";

import { CheckCircle2, Play, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import Shell from "../../components/Shell";
import { SkeletonRows, SkeletonText } from "../../components/Skeleton";
import { api, ScrapeRun } from "../../lib/api";

export default function ScrapeRuns() {
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggerRoute, setTriggerRoute] = useState("CCU-BOM");
  const [triggerDate, setTriggerDate] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      setRuns(await api.getScrapeRuns(50));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleTrigger() {
    if (!triggerDate) {
      setTriggerMsg("Pick a departure date first.");
      return;
    }
    setTriggering(true);
    setTriggerMsg(null);
    try {
      const res = await api.triggerScrape(triggerRoute, triggerDate);
      setTriggerMsg(`Queued job ${res.job_id.slice(0, 8)}… (status: ${res.status})`);
      setTimeout(load, 3000);
    } catch {
      setTriggerMsg("Failed to queue scrape job.");
    } finally {
      setTriggering(false);
    }
  }

  const successCount = runs.filter((r) => r.status === "success").length;
  const failedCount = runs.filter((r) => r.status === "failed").length;
  const runningCount = runs.filter((r) => r.status === "running").length;
  const totalQuotes = runs.reduce((sum, r) => sum + r.records_valid, 0);

  return (
    <Shell active="scrapes">
      <main className="scrapes-page">
        <section className="cluster-strip">
          <span><i />CLUSTER STATUS: <b>{runningCount > 0 ? "RUNNING" : "IDLE"}</b></span>
          <em>|</em>
          <span>ENGINE: <b>Playwright + Chromium</b></span>
          <em>|</em>
          <span>QUEUE: <b>Celery / Redis</b></span>
        </section>
        <div className="scrape-content">
          <section className="card scrape-head">
            <div>
              <div><h1>Scrape Runs</h1></div>
              <p>Distributed Playwright crawler execution history and manual trigger.</p>
            </div>
            <div>
              <span><CheckCircle2 size={14} />{loading ? "Loading…" : `${runs.length} runs loaded`}</span>
              <button onClick={load}><RefreshCw size={14} />Refresh</button>
            </div>
          </section>

          <section className="scrape-kpis">
            {[
              ["SUCCESSFUL RUNS", String(successCount), runs.length ? `${((successCount / runs.length) * 100).toFixed(1)}%` : "—"],
              ["FAILED RUNS", String(failedCount), runs.length ? `${((failedCount / runs.length) * 100).toFixed(1)}% rate` : "—"],
              ["RUNNING NOW", String(runningCount), ""],
              ["QUOTES COLLECTED (loaded runs)", String(totalQuotes), ""],
            ].map((k) => (
              <article className="card" key={k[0]}>
                <header><span>{k[0]}</span></header>
                <div>{loading ? <SkeletonText className="sm" /> : <><strong>{k[1]}</strong><b>{k[2]}</b></>}</div>
              </article>
            ))}
          </section>

          <section className="card jobs">
            <header>
              <div><h2>Trigger a Scrape</h2></div>
              <div>
                <input placeholder="Route code (e.g. CCU-BOM)" value={triggerRoute} onChange={(e) => setTriggerRoute(e.target.value.toUpperCase())} />
                <input type="date" value={triggerDate} onChange={(e) => setTriggerDate(e.target.value)} />
                <button className="trigger" onClick={handleTrigger} disabled={triggering}>
                  <Play size={14} />{triggering ? "Queuing…" : "Trigger Scrape"}
                </button>
              </div>
            </header>
            {triggerMsg && <p style={{ padding: "8px 16px", color: "#334155" }}>{triggerMsg}</p>}
          </section>

          <section className="card jobs">
            <header>
              <div><h2>Recent Execution Jobs</h2></div>
            </header>
            <div className="jobs-scroll">
              <table>
                <thead>
                  <tr>
                    <th>RUN ID</th><th>CORRIDOR</th><th>TARGET DATE</th><th>STARTED</th><th>DURATION</th><th>QUOTES FOUND</th><th>QUOTES VALID</th><th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && <SkeletonRows rows={6} cols={8} />}
                  {!loading && runs.length === 0 && <tr><td colSpan={8}>No scrape runs yet.</td></tr>}
                  {!loading && runs.map((r) => {
                    const durationSec = r.completed_at
                      ? Math.round((new Date(r.completed_at).getTime() - new Date(r.started_at).getTime()) / 1000)
                      : null;
                    return (
                      <tr key={r.id}>
                        <td>{r.id.slice(0, 8)}…</td>
                        <td><b>{r.route_code || "—"}</b></td>
                        <td>{r.departure_date || "—"}</td>
                        <td>{new Date(r.started_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</td>
                        <td>{durationSec !== null ? `${durationSec}s` : "—"}</td>
                        <td>{r.records_found}</td>
                        <td>{r.records_valid}</td>
                        <td><b className={r.status === "success" ? "success" : r.status === "failed" ? "retry" : ""}>{r.status.toUpperCase()}</b></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <footer><span>Showing {runs.length} most recent runs</span></footer>
          </section>
        </div>
      </main>
    </Shell>
  );
}
