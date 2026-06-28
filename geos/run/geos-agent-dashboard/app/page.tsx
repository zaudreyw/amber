"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import {
  FileAccess,
  ParsedEvent,
  ParsedTranscript,
  TranscriptTurn,
  UsageSummary,
  formatCost,
  formatDuration,
  formatNumber,
  parseTranscriptSource
} from "../lib/transcript";

type Filter = "all" | "messages" | "tools" | "results" | "errors";

const exampleName = "/data/shared/geophysics_agent_data/cc_convo_ex.jsonl";

export default function Home() {
  const [transcript, setTranscript] = useState<ParsedTranscript | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isLoadingPath, setIsLoadingPath] = useState(false);
  const [path, setPath] = useState(exampleName);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [filePathFilter, setFilePathFilter] = useState<string | null>(null);
  const [pulseIndex, setPulseIndex] = useState<number | null>(null);

  const filteredEvents = useMemo(() => {
    if (!transcript) return [];

    const normalizedQuery = query.trim().toLowerCase();

    return transcript.events.filter((event) => {
      if (filePathFilter && event.filePath !== filePathFilter) return false;

      const filterMatch =
        filter === "all" ||
        (filter === "messages" &&
          ["text", "thinking", "assistant", "user"].includes(event.kind)) ||
        (filter === "tools" &&
          (event.kind === "tool_use" || event.kind === "tool_result")) ||
        (filter === "results" && event.type === "result") ||
        (filter === "errors" && event.isError);

      if (!filterMatch) return false;
      if (!normalizedQuery) return true;

      return [
        event.title,
        event.preview,
        event.type,
        event.role,
        event.kind,
        event.model,
        event.provider,
        event.toolName,
        event.toolUseId,
        event.uuid,
        event.filePath
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [filter, query, filePathFilter, transcript]);

  const scrollToEvent = useCallback((targetIndex: number) => {
    const element = document.getElementById(`event-${targetIndex}`);
    if (!element) return;
    element.scrollIntoView({ behavior: "smooth", block: "center" });
    setPulseIndex(targetIndex);
    window.setTimeout(() => setPulseIndex((curr) => (curr === targetIndex ? null : curr)), 1400);
  }, []);

  function parseAndLoad(text: string, name: string) {
    try {
      const parsed = parseTranscriptSource(text);
      setTranscript(parsed);
      setFileName(name);
      setError(null);
      setFilter("all");
      setQuery("");
      setFilePathFilter(null);
    } catch (parseError) {
      setTranscript(null);
      setFileName(name);
      setError(parseError instanceof Error ? parseError.message : String(parseError));
    }
  }

  async function loadPath(nextPath = path) {
    setIsLoadingPath(true);
    setError(null);

    try {
      const response = await fetch("/api/read-file", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ path: nextPath }),
        cache: "no-store"
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          error?: string;
          details?: string;
        } | null;
        throw new Error(
          body?.details ?? body?.error ?? `File request failed with ${response.status}`
        );
      }

      const resolvedPath = response.headers.get("x-source-path") ?? nextPath;
      parseAndLoad(await response.text(), resolvedPath);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : String(loadError));
    } finally {
      setIsLoadingPath(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="topbar-title">
          <span className="topbar-badge">trace</span>
          <h1>Agent Trace Viewer</h1>
        </div>
        <nav className="topbar-nav">
          <span className="nav-link active">Transcript</span>
          <Link href="/simulations" className="nav-link">
            Simulations
          </Link>
        </nav>
      </header>

      <section className="path-bar">
        <form
          className="path-form"
          onSubmit={(event) => {
            event.preventDefault();
            void loadPath();
          }}
        >
          <input
            type="text"
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="/absolute/path/to/transcript.jsonl"
            spellCheck={false}
          />
          <button className="btn primary" type="submit" disabled={isLoadingPath}>
            {isLoadingPath ? "Loading..." : "Load"}
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => {
              setPath(exampleName);
              void loadPath(exampleName);
            }}
          >
            Sample
          </button>
        </form>
        <p className="path-hint">
          JSON or JSONL. Claude Code event logs, tool_use / tool_result pairs, and trailing
          usage records are handled.
        </p>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}

      {transcript ? (
        <>
          <section className="summary-band">
            <div className="loaded-file" title={fileName}>
              <span>loaded</span>
              <strong>{fileName}</strong>
            </div>
            <div className="stat-grid">
              <Stat label="Events" value={formatNumber(transcript.summary.totalEvents)} />
              <Stat
                label="Turns"
                value={formatNumber(
                  transcript.summary.numTurns ?? transcript.summary.turns.length
                )}
              />
              <Stat label="Cost" value={formatCost(transcript.summary.costUsd)} />
              <Stat label="Duration" value={formatDuration(transcript.summary.durationMs)} />
              <Stat
                label="Input tok"
                value={formatNumber(transcript.summary.finalUsage?.inputTokens)}
              />
              <Stat
                label="Output tok"
                value={formatNumber(transcript.summary.finalUsage?.outputTokens)}
              />
              <Stat label="Files touched" value={formatNumber(transcript.summary.files.length)} />
              <Stat label="Errors" value={formatNumber(transcript.summary.errorCount)} />
            </div>
          </section>

          <section className="context-strip">
            <ContextItem label="Session" value={transcript.summary.sessionId} mono />
            <ContextItem label="Model" value={transcript.summary.model} />
            <ContextItem label="Provider" value={transcript.summary.provider} />
            <ContextItem label="Cwd" value={transcript.summary.cwd} mono wide />
          </section>

          <section className="workspace">
            <aside className="side-panel">
              <Panel title="Files">
                <FileList
                  files={transcript.summary.files}
                  activePath={filePathFilter}
                  onSelect={(path) =>
                    setFilePathFilter((curr) => (curr === path ? null : path))
                  }
                />
              </Panel>
              <Panel title="Tools">
                <KeyValueList
                  values={transcript.summary.toolCounts}
                  empty="No tool calls found."
                />
              </Panel>
              <Panel title="Event kinds">
                <KeyValueList values={transcript.summary.countsByKind} />
              </Panel>
              <Panel title="Turns">
                <TurnNavigation turns={transcript.summary.turns} />
              </Panel>
            </aside>

            <section className="event-panel">
              <div className="toolbar">
                <input
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search text, id, command, path..."
                />
                <select
                  value={filter}
                  onChange={(event) => setFilter(event.target.value as Filter)}
                >
                  <option value="all">All events</option>
                  <option value="messages">Messages</option>
                  <option value="tools">Tool flow</option>
                  <option value="results">Results</option>
                  <option value="errors">Errors</option>
                </select>
                {filePathFilter ? (
                  <button
                    className="chip active"
                    type="button"
                    onClick={() => setFilePathFilter(null)}
                    title="Clear file filter"
                  >
                    file: {shortPath(filePathFilter)} <span aria-hidden>×</span>
                  </button>
                ) : null}
              </div>

              <div className="event-count">
                {formatNumber(filteredEvents.length)} of{" "}
                {formatNumber(transcript.summary.totalEvents)} events
              </div>

              <div className="event-list">
                {filteredEvents.map((event) => (
                  <EventRow
                    key={`${event.line}-${event.uuid ?? event.kind}`}
                    event={event}
                    pulse={pulseIndex === event.index}
                    onJumpToPair={scrollToEvent}
                  />
                ))}
              </div>
            </section>
          </section>
        </>
      ) : (
        <section className="empty-state">
          <h2>Load a transcript.</h2>
          <p>
            Enter a <code>.jsonl</code> or <code>.json</code> path above, or click Sample.
          </p>
        </section>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ContextItem({
  label,
  value,
  wide = false,
  mono = false
}: {
  label: string;
  value: string | null;
  wide?: boolean;
  mono?: boolean;
}) {
  const classes = ["context-item"];
  if (wide) classes.push("wide");
  if (mono) classes.push("mono");

  return (
    <div className={classes.join(" ")}>
      <span>{label}</span>
      <strong title={value ?? undefined}>{value ?? "-"}</strong>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

function KeyValueList({
  values,
  empty = "None"
}: {
  values: Record<string, number>;
  empty?: string;
}) {
  const entries = Object.entries(values).sort(
    (a, b) => b[1] - a[1] || a[0].localeCompare(b[0])
  );

  if (!entries.length) return <p className="muted">{empty}</p>;

  return (
    <dl className="kv-list">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{formatNumber(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function FileList({
  files,
  activePath,
  onSelect
}: {
  files: FileAccess[];
  activePath: string | null;
  onSelect: (path: string) => void;
}) {
  if (!files.length) return <p className="muted">No file tools invoked.</p>;

  return (
    <ul className="file-list">
      {files.map((file) => {
        const total = file.reads + file.edits + file.writes;
        const isActive = activePath === file.path;
        return (
          <li key={file.path}>
            <button
              type="button"
              className={isActive ? "file-item active" : "file-item"}
              onClick={() => onSelect(file.path)}
              title={file.path}
            >
              <span className="file-path">{shortPath(file.path)}</span>
              <span className="file-meta">
                {file.reads ? <span className="tag r">R {file.reads}</span> : null}
                {file.edits ? <span className="tag e">E {file.edits}</span> : null}
                {file.writes ? <span className="tag w">W {file.writes}</span> : null}
                {total > 1 && !file.reads && !file.edits && !file.writes ? (
                  <span className="tag">{total}</span>
                ) : null}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function TurnNavigation({ turns }: { turns: TranscriptTurn[] }) {
  if (!turns.length) return <p className="muted">No turns found.</p>;

  return (
    <nav className="turn-nav" aria-label="Turn navigation">
      {turns.map((turn) => (
        <a
          key={turn.index}
          className={turn.isError ? "turn-link has-error" : "turn-link"}
          href={`#event-${turn.firstEventIndex}`}
        >
          <span className="turn-link-top">
            <strong>Turn {turn.index}</strong>
            <span>L{turn.line}</span>
          </span>
          <span className="turn-link-preview">{turn.preview || "No preview"}</span>
          <span className="turn-link-meta">
            {formatNumber(turn.eventCount)}e
            {turn.toolCount ? ` · ${formatNumber(turn.toolCount)}t` : ""}
            {turn.inputTokens != null || turn.outputTokens != null
              ? ` · ${formatNumber(turn.inputTokens)}/${formatNumber(turn.outputTokens)}`
              : ` · ~${formatNumber(turn.roughTokens)}`}
          </span>
        </a>
      ))}
    </nav>
  );
}

function EventRow({
  event,
  pulse,
  onJumpToPair
}: {
  event: ParsedEvent;
  pulse: boolean;
  onJumpToPair: (index: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const raw = useMemo(() => JSON.stringify(event.record, null, 2), [event.record]);

  const gutterKind = gutterForEvent(event);
  const classes = [
    "event-row",
    `gutter-${gutterKind}`,
    event.isError ? "has-error" : "",
    expanded ? "is-expanded" : "is-collapsed",
    pulse ? "is-pulsing" : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article id={`event-${event.index}`} className={classes}>
      <div className="event-topline">
        <span className={`kind-pill kind-${gutterKind}`}>{gutterLabel(event)}</span>
        {event.turnIndex ? <span className="event-line">T{event.turnIndex}</span> : null}
        <span className="event-line">L{event.line}</span>
        <strong className="event-title">{event.title}</strong>
        <button
          className="btn ghost sm"
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? "collapse" : "expand"}
        </button>
      </div>
      <p className="event-preview">{event.preview || "No text preview available."}</p>
      <div className="event-meta">
        {event.toolName ? <span className="meta-tag">tool: {event.toolName}</span> : null}
        {event.filePath ? (
          <span className="meta-tag mono" title={event.filePath}>
            {shortPath(event.filePath)}
          </span>
        ) : null}
        {event.toolUseId ? (
          <button
            type="button"
            className="meta-tag link mono"
            title={
              event.pairedEventIndex != null
                ? `Jump to paired ${event.kind === "tool_use" ? "result" : "call"}`
                : event.toolUseId
            }
            onClick={() =>
              event.pairedEventIndex != null
                ? onJumpToPair(event.pairedEventIndex)
                : undefined
            }
            disabled={event.pairedEventIndex == null}
          >
            {event.kind === "tool_use" ? "→" : event.kind === "tool_result" ? "←" : ""}
            id {shortId(event.toolUseId)}
          </button>
        ) : null}
        {event.messageId ? (
          <span className="meta-tag mono" title={event.messageId}>
            msg {shortId(event.messageId)}
          </span>
        ) : null}
      </div>
      <UsagePills usage={event.usage} roughTokens={event.roughTokens} />
      {expanded ? (
        <div className="event-expanded">
          <MessageContent event={event} />
          <details>
            <summary>raw json</summary>
            <pre>{raw}</pre>
          </details>
        </div>
      ) : null}
    </article>
  );
}

function UsagePills({
  usage,
  roughTokens
}: {
  usage: UsageSummary;
  roughTokens: number;
}) {
  const hasUsage = Object.values(usage).some((value) => typeof value === "number");

  if (!hasUsage) {
    return (
      <div className="usage-row">
        <span>~{formatNumber(roughTokens)} tok</span>
      </div>
    );
  }

  return (
    <div className="usage-row">
      <span>{formatNumber(usage.inputTokens)} in</span>
      <span>{formatNumber(usage.outputTokens)} out</span>
      {usage.cacheReadInputTokens != null ? (
        <span>{formatNumber(usage.cacheReadInputTokens)} cache r</span>
      ) : null}
      {usage.cacheCreationInputTokens != null ? (
        <span>{formatNumber(usage.cacheCreationInputTokens)} cache w</span>
      ) : null}
      {usage.costUsd != null ? <span>{formatCost(usage.costUsd)}</span> : null}
    </div>
  );
}

function MessageContent({ event }: { event: ParsedEvent }) {
  const message = asObject(event.record.message);
  const content = message?.content;

  if (typeof content === "string") {
    return (
      <section className="content-section">
        <h3>Message</h3>
        <pre className="content-pre">{content}</pre>
      </section>
    );
  }

  if (Array.isArray(content) && content.length) {
    const visible = content.filter(
      (block) => !isRedactedThinking(block)
    );
    if (!visible.length) {
      return (
        <section className="content-section">
          <h3>Record</h3>
          <pre className="content-pre">{JSON.stringify(event.record, null, 2)}</pre>
        </section>
      );
    }
    return (
      <section className="content-section">
        <h3>Blocks</h3>
        <div className="content-blocks">
          {visible.map((block, index) => (
            <ContentBlock key={index} block={block} index={index} />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="content-section">
      <h3>Record</h3>
      <pre className="content-pre">{JSON.stringify(event.record, null, 2)}</pre>
    </section>
  );
}

function ContentBlock({ block, index }: { block: unknown; index: number }) {
  const object = asObject(block);
  const type = typeof object?.type === "string" ? object.type : "block";

  if (!object) {
    return (
      <article className="content-block">
        <h4>Block {index + 1}</h4>
        <pre className="content-pre">{String(block)}</pre>
      </article>
    );
  }

  if (type === "tool_use") {
    const name = typeof object.name === "string" ? object.name : "tool";

    return (
      <article className="content-block">
        <h4>Tool call: {name}</h4>
        <pre className="content-pre">{JSON.stringify(object.input ?? object, null, 2)}</pre>
      </article>
    );
  }

  if (type === "tool_result") {
    return (
      <article className="content-block">
        <h4>Tool result</h4>
        <pre className="content-pre">
          {String(object.content ?? JSON.stringify(object, null, 2))}
        </pre>
      </article>
    );
  }

  if (type === "text" || type === "thinking") {
    const text = type === "text" ? object.text : object.thinking;

    return (
      <article className="content-block">
        <h4>{type === "text" ? "Text" : "Reasoning"}</h4>
        <pre className="content-pre">{String(text ?? "")}</pre>
      </article>
    );
  }

  // redacted_thinking is filtered upstream, but keep a fallback for defensive rendering
  return (
    <article className="content-block">
      <h4>{titleCase(type)}</h4>
      <pre className="content-pre">{JSON.stringify(object, null, 2)}</pre>
    </article>
  );
}

function isRedactedThinking(block: unknown) {
  const obj = asObject(block);
  return obj && typeof obj.type === "string" && obj.type === "redacted_thinking";
}

function asObject(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function gutterForEvent(event: ParsedEvent): string {
  if (event.isError) return "error";
  if (event.kind === "tool_use") return "tool-use";
  if (event.kind === "tool_result") return "tool-result";
  if (event.kind === "thinking") return "thinking";
  if (event.kind === "text") return event.role === "user" ? "user" : "assistant";
  if (event.type === "system") return "system";
  if (event.type === "result") return "result";
  if (event.type === "user") return "user";
  if (event.type === "assistant") return "assistant";
  return "other";
}

function gutterLabel(event: ParsedEvent): string {
  const k = gutterForEvent(event);
  switch (k) {
    case "tool-use":
      return "tool→";
    case "tool-result":
      return "←result";
    case "thinking":
      return "think";
    case "assistant":
      return "asst";
    case "user":
      return "user";
    case "system":
      return "sys";
    case "result":
      return "end";
    case "error":
      return "error";
    default:
      return event.type;
  }
}

function shortId(value: string) {
  return value.length > 10 ? `${value.slice(0, 10)}…` : value;
}

function shortPath(value: string) {
  if (value.length <= 48) return value;
  const parts = value.split("/");
  if (parts.length <= 3) return `…${value.slice(-45)}`;
  return `…/${parts.slice(-3).join("/")}`;
}

function titleCase(value: string) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}
