"use client";

import { Activity, BookOpen, Database, FileCode2, Gauge, Menu, PlaneTakeoff, RefreshCw, Route, Search, ShieldCheck, SquareTerminal, UserCircle, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

const links = [
  ["Overview", "/", Gauge], ["Airfare Index", "/airfare-index", Activity], ["Routes", "/routes", Route],
  ["Fare Observations", "/fare-observations", Database], ["Scrape Runs", "/scrape-runs", RefreshCw], ["Data Quality", "/data-quality", ShieldCheck],
  ["Methodology", "#", BookOpen], ["API", "#", FileCode2],
] as const;

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export default function Shell({ active, children }: { active: "overview" | "index" | "routes" | "observations" | "scrapes" | "quality"; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const [scrapingActive, setScrapingActive] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const runs = await api.getScrapeRuns(5);
        if (cancelled) return;
        setLastRunAt(runs[0]?.completed_at || runs[0]?.started_at || null);
        setScrapingActive(runs.some((r) => r.status === "running"));
      } catch {
        // leave previous state on transient failure
      } finally {
        if (!cancelled) setLoaded(true);
      }
    }
    poll();
    const interval = setInterval(poll, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return <div className="app-shell">
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div><div className="brand"><button className="close-menu" onClick={()=>setOpen(false)} aria-label="Close navigation"><X size={18}/></button><div className="brand-row"><div className="brand-icon"><PlaneTakeoff size={20}/></div><div><strong>India Airfare Index</strong><small>Real-time airfare intelligence</small></div></div><span className="baseline"><i/>MoSPI / GoI CPI Baseline</span></div>
      <nav>{links.map(([label,href,Icon],i)=><a key={label} href={href} className={(active==="overview"&&i===0)||(active==="index"&&i===1)||(active==="routes"&&i===2)||(active==="observations"&&i===3)||(active==="scrapes"&&i===4)||(active==="quality"&&i===5)?"active":""}><Icon size={17}/><span>{label}</span></a>)}</nav></div>
      <div className="sidebar-status"><div><span>SOURCE</span><b>Google Flights</b></div><div><span>LAST SCRAPE</span><b>{loaded ? timeAgo(lastRunAt) : "…"}</b></div><hr/><p><i className={loaded ? "pulse" : ""}/>{loaded ? "System operational" : "Connecting…"}</p><small><i/>FastAPI / Celery / Neon PG</small></div>
    </aside>
    {open&&<button className="backdrop" onClick={()=>setOpen(false)} aria-label="Close navigation"/>}
    <div className="page"><header className="topbar"><button className="menu-button" onClick={()=>setOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div className="crumb"><strong>NATIONAL SURVEILLANCE</strong><span>/</span><b>CIVIL AVIATION BASKET</b></div><label className="search"><Search size={16}/><input placeholder="Route (DEL-BOM), airport (BLR), carrier..."/><kbd>⌘K</kbd></label><div className="top-actions">{scrapingActive&&<span className="scraping"><i/>SCRAPING ACTIVE</span>}<span className="sync"><RefreshCw size={13}/>{loaded ? timeAgo(lastRunAt) : "…"}</span><button><SquareTerminal size={14}/>API Docs</button><UserCircle className="avatar" size={30}/></div></header>{children}</div>
  </div>;
}
