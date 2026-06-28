"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

type TaskStatus = {
  task: string;
  taskPath: string;
  agent?: string;
  run_name?: string;
  status?: string;
  process_status?: string;
  elapsed_seconds?: number;
  started?: string;
  updated?: string;
  exit_code?: number | null;
  total_tool_calls?: number;
  openrouter_cost_usd?: number;
  latest_agent_response?: string;
  latest_stdout?: string[];
};

type RunGroup = {
  agent: string;
  run_name: string;
  runPath: string;
  tasks: TaskStatus[];
  completedCount: number;
  runningCount: number;
  totalCount: number;
};

type RunsResponse = {
  runs: RunGroup[];
  evalRoot: string;
};

const STATUS_COLORS: Record<string, string> = {
  running: "var(--amber)",
  preflight: "var(--amber)",
  retrying_pseudo_tool: "var(--amber)",
  success: "var(--green)",
  failed: "var(--red)",
  failed_pseudo_tool: "var(--red)",
  failed_rag_unavailable: "var(--red)",
  timeout: "var(--red)",
  interrupted: "var(--muted)",
  error: "var(--red)",
  pending: "var(--muted)",
};

function statusColor(s: string | undefined) {
  return STATUS_COLORS[s ?? "pending"] ?? "var(--muted)";
}

function formatCost(v: number | undefined) {
  if (v == null) return null;
  return `$${v.toFixed(4)}`;
}

function formatElapsed(seconds: number | undefined) {
  if (seconds == null) return null;
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  const r = s % 60;
  return m > 0 ? `${m}m ${r}s` : `${s}s`;
}

function TaskRow({ task }: { task: TaskStatus }) {
  const [expanded, setExpanded] = useState(false);
  const ps = task.process_status ?? task.status ?? "pending";
  const isRunning = ps === "running" || ps === "preflight";
  const cost = formatCost(task.openrouter_cost_usd);
  const elapsed = formatElapsed(task.elapsed_seconds);

  return (
    <div
      className={`task-row ${isRunning ? "task-running" : ""}`}
      style={{ borderLeft: `3px solid ${statusColor(ps)}` }}
    >
      <div className="task-topline" onClick={() => setExpanded((e) => !e)}>
        <span className="task-status-dot" style={{ background: statusColor(ps) }} />
        <span className="task-name">{task.task}</span>
        <span className="task-chips">
          {cost && <span className="chip chip-cost">{cost}</span>}
          {elapsed && <span className="chip chip-elapsed">{elapsed}</span>}
          {task.total_tool_calls != null && (
            <span className="chip">{task.total_tool_calls} tools</span>
          )}
          <span className="chip chip-status">{ps}</span>
        </span>
        <button className="expand-btn" type="button">
          {expanded ? "▲" : "▼"}
        </button>
      </div>

      {expanded && (
        <div className="task-detail">
          {task.latest_agent_response && (
            <div className="task-last-response">
              <span className="detail-label">Last response</span>
              <p>{task.latest_agent_response.slice(0, 500)}{task.latest_agent_response.length > 500 ? "…" : ""}</p>
            </div>
          )}
          {task.latest_stdout && task.latest_stdout.length > 0 && (
            <div className="task-stdout">
              <span className="detail-label">Recent output</span>
              <pre>{task.latest_stdout.slice(-5).join("\n").slice(0, 800)}</pre>
            </div>
          )}
          <div className="task-meta-row">
            {task.started && <span><b>Started:</b> {new Date(task.started).toLocaleTimeString()}</span>}
            {task.updated && <span><b>Updated:</b> {new Date(task.updated).toLocaleTimeString()}</span>}
            {task.exit_code != null && <span><b>Exit:</b> {task.exit_code}</span>}
            <span className="task-path">{task.taskPath}</span>
          </div>
          {task.openrouter_cost_usd != null && (
            <div className="cost-note">
              <span>Cost via OpenRouter API: </span>
              <strong>{cost}</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RunCard({ run }: { run: RunGroup }) {
  const [collapsed, setCollapsed] = useState(run.runningCount === 0);
  const hasRunning = run.runningCount > 0;
  const progress = run.totalCount > 0 ? run.completedCount / run.totalCount : 0;

  return (
    <div className={`run-card ${hasRunning ? "run-active" : ""}`}>
      <div className="run-header" onClick={() => setCollapsed((c) => !c)}>
        <div className="run-title">
          {hasRunning && <span className="live-dot" />}
          <span className="run-agent">{run.agent}</span>
          <span className="run-sep">/</span>
          <span className="run-name">{run.run_name}</span>
        </div>
        <div className="run-stats">
          <span>{run.runningCount > 0 ? `${run.runningCount} running` : ""}</span>
          <span>{run.completedCount}/{run.totalCount} done</span>
        </div>
        <div className="run-progress-bar">
          <div className="run-progress-fill" style={{ width: `${progress * 100}%` }} />
        </div>
        <button className="expand-btn" type="button">{collapsed ? "▼" : "▲"}</button>
      </div>

      {!collapsed && (
        <div className="run-tasks">
          {run.tasks.map((task) => (
            <TaskRow key={`${task.agent}-${task.run_name}-${task.task}`} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SimulationsPage() {
  const [data, setData] = useState<RunsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const resp = await fetch("/api/runs", { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json() as RunsResponse;
      setData(json);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchRuns();
    intervalRef.current = setInterval(() => void fetchRuns(), 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchRuns]);

  const hasRunning = data?.runs.some((r) => r.runningCount > 0) ?? false;
  const totalRunning = data?.runs.reduce((s, r) => s + r.runningCount, 0) ?? 0;

  return (
    <main className="app-shell">
      <div className="nav-tabs">
        <Link href="/" className="nav-tab">Transcript Viewer</Link>
        <span className="nav-tab active">Simulations</span>
      </div>

      <section className="path-band">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <span /><span /><span />
          </div>
          <div>
            <p className="eyebrow">GEOS Agent Dashboard</p>
            <h1>
              {hasRunning ? (
                <>
                  <span className="live-indicator">
                    <span className="live-dot" />
                    {totalRunning} simulation{totalRunning !== 1 ? "s" : ""} running
                  </span>
                </>
              ) : (
                "Simulation runs"
              )}
            </h1>
          </div>
        </div>
        <div className="refresh-info">
          <span>Auto-refresh: 3s</span>
          {lastUpdated && <span>Last: {lastUpdated.toLocaleTimeString()}</span>}
          <button className="secondary-button" type="button" onClick={() => void fetchRuns()}>
            Refresh now
          </button>
        </div>
      </section>

      {error && <p className="error-banner">{error}</p>}

      {loading && !data && (
        <section className="empty-state">
          <p>Loading runs from {"/home/brianliu/data/eval"}…</p>
        </section>
      )}

      {data && data.runs.length === 0 && (
        <section className="empty-state">
          <h2>No runs found.</h2>
          <p>No status.json files found under {data.evalRoot}.</p>
        </section>
      )}

      {data && data.runs.length > 0 && (
        <section className="runs-list">
          {data.runs.map((run) => (
            <RunCard key={`${run.agent}/${run.run_name}`} run={run} />
          ))}
        </section>
      )}
    </main>
  );
}
