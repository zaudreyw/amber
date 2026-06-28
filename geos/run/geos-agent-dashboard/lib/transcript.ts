export type JsonValue =
  | null
  | string
  | number
  | boolean
  | JsonValue[]
  | { [key: string]: JsonValue };

export type TranscriptRecord = Record<string, unknown>;

export type UsageSummary = {
  inputTokens: number | null;
  outputTokens: number | null;
  cacheReadInputTokens: number | null;
  cacheCreationInputTokens: number | null;
  costUsd: number | null;
};

export type ParsedEvent = {
  index: number;
  line: number;
  turnIndex: number | null;
  record: TranscriptRecord;
  type: string;
  role: string;
  subtype: string | null;
  kind: string;
  title: string;
  preview: string;
  model: string | null;
  provider: string | null;
  messageId: string | null;
  sessionId: string | null;
  uuid: string | null;
  toolUseId: string | null;
  parentToolUseId: string | null;
  toolName: string | null;
  isError: boolean;
  usage: UsageSummary;
  apiInputTokens: number | null;
  apiOutputTokens: number | null;
  roughTokens: number;
  pairedEventIndex: number | null;
  filePath: string | null;
};

export type TranscriptTurn = {
  index: number;
  firstEventIndex: number;
  line: number;
  title: string;
  preview: string;
  eventCount: number;
  toolCount: number;
  isError: boolean;
  inputTokens: number | null;
  outputTokens: number | null;
  roughTokens: number;
};

export type FileAccess = {
  path: string;
  reads: number;
  edits: number;
  writes: number;
  firstEventIndex: number;
  eventIndices: number[];
};

export type ParsedTranscript = {
  events: ParsedEvent[];
  records: TranscriptRecord[];
  sourceFormat: "json" | "jsonl";
  summary: {
    cwd: string | null;
    sessionId: string | null;
    model: string | null;
    provider: string | null;
    totalLines: number;
    totalEvents: number;
    numTurns: number | null;
    durationMs: number | null;
    costUsd: number | null;
    countsByType: Record<string, number>;
    countsByKind: Record<string, number>;
    toolCounts: Record<string, number>;
    errorCount: number;
    apiInputTotal: number | null;
    apiOutputTotal: number | null;
    roughTokenTotal: number;
    finalUsage: UsageSummary | null;
    turns: TranscriptTurn[];
    files: FileAccess[];
  };
};

type ContentBlock = Record<string, unknown>;

const FILE_TOOL_NAMES = new Set(["Read", "Edit", "Write", "MultiEdit", "NotebookEdit"]);

export function parseTranscriptSource(text: string): ParsedTranscript {
  const trimmed = text.trim();

  if (!trimmed) {
    throw new Error("The selected file is empty.");
  }

  if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      const records = extractRecords(parsed);

      return buildTranscript(records, "json", records.length);
    } catch (error) {
      if (trimmed.startsWith("[")) {
        throw new Error(jsonErrorMessage(error));
      }
    }
  }

  const lines = text.split(/\r?\n/);
  const records: TranscriptRecord[] = [];

  lines.forEach((line, index) => {
    if (!line.trim()) return;

    try {
      records.push(assertRecord(JSON.parse(line)));
    } catch (error) {
      throw new Error(`Line ${index + 1}: ${jsonErrorMessage(error)}`);
    }
  });

  if (!records.length) {
    throw new Error("No JSON records were found.");
  }

  return buildTranscript(records, "jsonl", lines.length);
}

function buildTranscript(
  records: TranscriptRecord[],
  sourceFormat: "json" | "jsonl",
  totalLines: number
): ParsedTranscript {
  const toolNamesById = new Map<string, string>();
  const keptIndices: number[] = [];

  const rawEvents = records
    .map((record, recordIndex) => {
      if (isPurelyRedactedThinking(record)) return null;

      const event = normalizeEvent(record, keptIndices.length, recordIndex);
      keptIndices.push(recordIndex);

      if (event.toolUseId && event.toolName) {
        toolNamesById.set(event.toolUseId, event.toolName);
      }

      return event;
    })
    .filter((event): event is ParsedEvent => event !== null);

  // Link tool_use ↔ tool_result via toolUseId, and backfill tool names / file paths on results.
  const toolUseEventByToolId = new Map<string, number>();
  rawEvents.forEach((event) => {
    if (event.kind === "tool_use" && event.toolUseId) {
      toolUseEventByToolId.set(event.toolUseId, event.index);
    }
  });

  const toolResultEventByToolId = new Map<string, number>();
  rawEvents.forEach((event) => {
    if (event.kind === "tool_result" && event.toolUseId) {
      toolResultEventByToolId.set(event.toolUseId, event.index);
    }
  });

  const linkedEvents = rawEvents.map((event) => {
    let toolName = event.toolName;
    let filePath = event.filePath;
    let pairedEventIndex: number | null = null;

    if (!toolName && event.toolUseId) {
      toolName = toolNamesById.get(event.toolUseId) ?? null;
    }

    if (event.kind === "tool_use" && event.toolUseId) {
      pairedEventIndex = toolResultEventByToolId.get(event.toolUseId) ?? null;
    } else if (event.kind === "tool_result" && event.toolUseId) {
      pairedEventIndex = toolUseEventByToolId.get(event.toolUseId) ?? null;
    }

    if (toolName && toolName !== event.toolName) {
      // Re-derive title for results that only now got their tool name.
      const newTitle =
        event.kind === "tool_result"
          ? `Tool result: ${toolName}`
          : event.title;

      return { ...event, toolName, pairedEventIndex, filePath, title: newTitle };
    }

    return { ...event, pairedEventIndex, filePath };
  });

  const eventsWithTurns = assignTurns(linkedEvents);

  return {
    events: eventsWithTurns,
    records,
    sourceFormat,
    summary: summarize(records, eventsWithTurns, totalLines)
  };
}

function normalizeEvent(
  record: TranscriptRecord,
  index: number,
  _recordIndex: number
): ParsedEvent {
  const message = getObject(record.message);
  const content = message ? message.content : undefined;
  const blocks = Array.isArray(content)
    ? (content.filter(isObject) as ContentBlock[])
    : [];
  const visibleBlocks = blocks.filter(
    (block) => getString(block.type) !== "redacted_thinking"
  );
  const firstBlock = visibleBlocks[0] ?? blocks[0];
  const blockType = getString(firstBlock?.type);
  const type = getString(record.type) ?? "unknown";
  const role = getString(message?.role) ?? getString(record.role) ?? "none";
  const subtype = getString(record.subtype);
  const toolBlock = visibleBlocks.find(
    (block) => getString(block.type) === "tool_use"
  );
  const toolResultBlock = visibleBlocks.find(
    (block) => getString(block.type) === "tool_result"
  );
  const toolUseId =
    getString(toolBlock?.id) ??
    getString(toolResultBlock?.tool_use_id) ??
    getString(record.tool_use_id);
  const parentToolUseId = getString(record.parent_tool_use_id);
  const toolName = getString(toolBlock?.name);
  const toolInput = getObject(toolBlock?.input);
  const filePath =
    toolName && FILE_TOOL_NAMES.has(toolName)
      ? getString(toolInput?.file_path) ??
        getString(toolInput?.notebook_path) ??
        null
      : null;
  const usage = summarizeUsage(message?.usage);
  const topLevelUsage = summarizeUsage(record.usage);
  const mergedUsage = mergeUsage(usage, topLevelUsage);
  const isError =
    getBoolean(record.is_error) === true ||
    getBoolean(toolResultBlock?.is_error) === true ||
    getBoolean(getObject(record.tool_use_result)?.is_error) === true;
  const kind = eventKind(type, subtype, blockType);

  return {
    index,
    line: index + 1,
    turnIndex: null,
    record,
    type,
    role,
    subtype,
    kind,
    title: eventTitle(type, role, subtype, blockType, toolName),
    preview: eventPreview(record, visibleBlocks, kind),
    model: getString(message?.model) ?? getString(record.model),
    provider: getString(message?.provider) ?? getString(record.provider),
    messageId: getString(message?.id),
    sessionId: getString(record.session_id),
    uuid: getString(record.uuid),
    toolUseId,
    parentToolUseId,
    toolName,
    isError,
    usage: mergedUsage,
    apiInputTokens: mergedUsage.inputTokens,
    apiOutputTokens: mergedUsage.outputTokens,
    roughTokens: roughTokenEstimate(JSON.stringify(message ?? record)),
    pairedEventIndex: null,
    filePath
  };
}

function isPurelyRedactedThinking(record: TranscriptRecord): boolean {
  const message = getObject(record.message);
  const content = message?.content;

  if (!Array.isArray(content) || content.length === 0) return false;

  return content.every(
    (block) => isObject(block) && getString(block.type) === "redacted_thinking"
  );
}

function assignTurns(events: ParsedEvent[]) {
  let turnIndex = 0;
  let currentTurn: number | null = null;
  let currentAssistantMessageId: string | null = null;

  return events.map((event) => {
    if (event.type === "system" || event.type === "result") {
      return { ...event, turnIndex: null };
    }

    const startsUserTurn = event.type === "user" && !isToolResultEvent(event.record);
    const startsAssistantStep =
      event.type === "assistant" &&
      Boolean(event.messageId) &&
      currentAssistantMessageId !== null &&
      currentAssistantMessageId !== event.messageId;

    if (startsUserTurn || currentTurn === null || startsAssistantStep) {
      turnIndex += 1;
      currentTurn = turnIndex;
    }

    if (event.type === "assistant" && event.messageId) {
      currentAssistantMessageId = event.messageId;
    }

    return { ...event, turnIndex: currentTurn };
  });
}

function summarize(
  records: TranscriptRecord[],
  events: ParsedEvent[],
  totalLines: number
): ParsedTranscript["summary"] {
  const countsByType: Record<string, number> = {};
  const countsByKind: Record<string, number> = {};
  const toolCounts: Record<string, number> = {};
  let apiInputTotal = 0;
  let apiOutputTotal = 0;
  let hasInputTotal = false;
  let hasOutputTotal = false;
  let roughTokenTotal = 0;

  events.forEach((event) => {
    countsByType[event.type] = (countsByType[event.type] ?? 0) + 1;
    countsByKind[event.kind] = (countsByKind[event.kind] ?? 0) + 1;
    roughTokenTotal += event.roughTokens;

    if (event.toolName && event.kind === "tool_use") {
      toolCounts[event.toolName] = (toolCounts[event.toolName] ?? 0) + 1;
    }

    if (typeof event.apiInputTokens === "number") {
      apiInputTotal += event.apiInputTokens;
      hasInputTotal = true;
    }

    if (typeof event.apiOutputTokens === "number") {
      apiOutputTotal += event.apiOutputTokens;
      hasOutputTotal = true;
    }
  });

  const init = records.find((record) => record.type === "system") ?? {};
  const result = records.findLast((record) => record.type === "result") ?? null;
  const resultUsage = result ? summarizeUsage(result.usage) : null;
  const firstModelEvent = events.find((event) => event.model);
  const firstProviderEvent = events.find((event) => event.provider);
  const turns = summarizeTurns(events);
  const files = summarizeFileAccess(events);

  return {
    cwd: getString(init.cwd),
    sessionId:
      getString(init.session_id) ??
      events.find((event) => event.sessionId)?.sessionId ??
      null,
    model: getString(init.model) ?? firstModelEvent?.model ?? null,
    provider: firstProviderEvent?.provider ?? null,
    totalLines,
    totalEvents: events.length,
    numTurns: result ? getNumber(result.num_turns) : null,
    durationMs: result ? getNumber(result.duration_ms) : null,
    costUsd: result
      ? getNumber(result.openrouter_cost_usd) ?? getNumber(result.total_cost_usd)
      : null,
    countsByType,
    countsByKind,
    toolCounts,
    errorCount: events.filter((event) => event.isError).length,
    apiInputTotal: hasInputTotal ? apiInputTotal : null,
    apiOutputTotal: hasOutputTotal ? apiOutputTotal : null,
    roughTokenTotal,
    finalUsage: resultUsage && hasAnyUsage(resultUsage) ? resultUsage : null,
    turns,
    files
  };
}

function summarizeFileAccess(events: ParsedEvent[]): FileAccess[] {
  const map = new Map<string, FileAccess>();

  events.forEach((event) => {
    if (event.kind !== "tool_use" || !event.filePath || !event.toolName) return;

    const existing = map.get(event.filePath);

    if (!existing) {
      map.set(event.filePath, {
        path: event.filePath,
        reads: event.toolName === "Read" ? 1 : 0,
        edits:
          event.toolName === "Edit" || event.toolName === "MultiEdit"
            ? 1
            : 0,
        writes:
          event.toolName === "Write" || event.toolName === "NotebookEdit"
            ? 1
            : 0,
        firstEventIndex: event.index,
        eventIndices: [event.index]
      });
      return;
    }

    if (event.toolName === "Read") existing.reads += 1;
    else if (event.toolName === "Edit" || event.toolName === "MultiEdit")
      existing.edits += 1;
    else if (event.toolName === "Write" || event.toolName === "NotebookEdit")
      existing.writes += 1;
    existing.eventIndices.push(event.index);
  });

  return Array.from(map.values()).sort((a, b) => {
    const totalA = a.reads + a.edits + a.writes;
    const totalB = b.reads + b.edits + b.writes;
    return totalB - totalA || a.path.localeCompare(b.path);
  });
}

function summarizeTurns(events: ParsedEvent[]): TranscriptTurn[] {
  const turns = new Map<
    number,
    TranscriptTurn & { hasInput: boolean; hasOutput: boolean }
  >();

  events.forEach((event) => {
    if (event.turnIndex === null) return;

    const existing = turns.get(event.turnIndex);
    const inputTokens = event.apiInputTokens ?? 0;
    const outputTokens = event.apiOutputTokens ?? 0;

    if (!existing) {
      turns.set(event.turnIndex, {
        index: event.turnIndex,
        firstEventIndex: event.index,
        line: event.line,
        title: `Turn ${event.turnIndex}`,
        preview: turnPreview(event),
        eventCount: 1,
        toolCount: event.kind === "tool_use" ? 1 : 0,
        isError: event.isError,
        inputTokens,
        outputTokens,
        roughTokens: event.roughTokens,
        hasInput: typeof event.apiInputTokens === "number",
        hasOutput: typeof event.apiOutputTokens === "number"
      });
      return;
    }

    existing.eventCount += 1;
    existing.toolCount += event.kind === "tool_use" ? 1 : 0;
    existing.isError = existing.isError || event.isError;
    existing.roughTokens += event.roughTokens;

    if (typeof event.apiInputTokens === "number") {
      existing.inputTokens = (existing.inputTokens ?? 0) + inputTokens;
      existing.hasInput = true;
    }

    if (typeof event.apiOutputTokens === "number") {
      existing.outputTokens = (existing.outputTokens ?? 0) + outputTokens;
      existing.hasOutput = true;
    }

    if (!existing.preview && event.preview) {
      existing.preview = turnPreview(event);
    }
  });

  return Array.from(turns.values()).map(({ hasInput, hasOutput, ...turn }) => ({
    ...turn,
    inputTokens: hasInput ? turn.inputTokens : null,
    outputTokens: hasOutput ? turn.outputTokens : null
  }));
}

function eventKind(type: string, subtype: string | null, blockType: string | null) {
  if (type === "system") return subtype ? `system.${subtype}` : "system";
  if (type === "result") return subtype ? `result.${subtype}` : "result";
  if (blockType) return blockType;
  return type;
}

function eventTitle(
  type: string,
  role: string,
  subtype: string | null,
  blockType: string | null,
  toolName: string | null
) {
  if (type === "system") return subtype ? `System ${subtype}` : "System";
  if (type === "result") return subtype ? `Result ${subtype}` : "Result";
  if (blockType === "tool_use") return toolName ? `Tool call: ${toolName}` : "Tool call";
  if (blockType === "tool_result")
    return toolName ? `Tool result: ${toolName}` : "Tool result";
  if (blockType === "thinking") return "Reasoning";
  if (blockType === "text") return `${titleCase(role)} response`;
  return titleCase(role === "none" ? type : role);
}

function eventPreview(record: TranscriptRecord, blocks: ContentBlock[], kind: string) {
  if (record.type === "system") {
    const cwd = getString(record.cwd);
    const model = getString(record.model);
    const tools = Array.isArray(record.tools) ? `${record.tools.length} tools` : null;

    return compact([cwd, model, tools]).join(" | ");
  }

  if (record.type === "result") {
    const turns = getNumber(record.num_turns);
    const orCost = getNumber(record.openrouter_cost_usd);
    const ccCost = getNumber(record.total_cost_usd);
    const cost = orCost ?? ccCost;
    const costLabel =
      cost == null
        ? null
        : orCost != null
        ? `$${cost.toFixed(4)} (OR)`
        : `$${cost.toFixed(4)} (CC)`;
    const duration = getNumber(record.duration_ms);

    return compact([
      turns == null ? null : `${turns} turns`,
      costLabel,
      duration == null ? null : formatDuration(duration)
    ]).join(" | ");
  }

  if (kind === "tool_use") {
    const toolBlock = blocks.find((block) => getString(block.type) === "tool_use");
    const input = getObject(toolBlock?.input);
    const filePath = getString(input?.file_path);
    const description = getString(input?.description);
    const command = getString(input?.command);

    return truncate(
      filePath ?? description ?? command ?? JSON.stringify(input ?? toolBlock),
      280
    );
  }

  if (kind === "tool_result") {
    const toolResultBlock = blocks.find((block) => getString(block.type) === "tool_result");
    const topLevelResult = getObject(record.tool_use_result);
    const content = getString(toolResultBlock?.content);
    const stdout = getString(topLevelResult?.stdout);
    const stderr = getString(topLevelResult?.stderr);

    return truncate(content ?? stdout ?? stderr ?? "Tool completed.", 280);
  }

  if (typeof record.message === "object" && record.message !== null) {
    const message = record.message as Record<string, unknown>;
    const content = getString(message.content);

    if (content) return truncate(content, 280);
  }

  const text = blocks
    .map((block) => {
      if (getString(block.type) === "text") return getString(block.text);
      if (getString(block.type) === "thinking") return getString(block.thinking);
      return JSON.stringify(block);
    })
    .filter(Boolean)
    .join("\n\n");

  return truncate(text || JSON.stringify(record), 280);
}

function turnPreview(event: ParsedEvent) {
  return truncate(event.preview || event.title, 130);
}

function summarizeUsage(value: unknown): UsageSummary {
  const usage = getObject(value);

  return {
    inputTokens: getNumber(usage?.input_tokens) ?? getNumber(usage?.inputTokens),
    outputTokens: getNumber(usage?.output_tokens) ?? getNumber(usage?.outputTokens),
    cacheReadInputTokens:
      getNumber(usage?.cache_read_input_tokens) ?? getNumber(usage?.cacheReadInputTokens),
    cacheCreationInputTokens:
      getNumber(usage?.cache_creation_input_tokens) ??
      getNumber(usage?.cacheCreationInputTokens),
    costUsd: getNumber(usage?.costUSD) ?? getNumber(usage?.cost_usd)
  };
}

function mergeUsage(primary: UsageSummary, fallback: UsageSummary): UsageSummary {
  return {
    inputTokens: primary.inputTokens ?? fallback.inputTokens,
    outputTokens: primary.outputTokens ?? fallback.outputTokens,
    cacheReadInputTokens: primary.cacheReadInputTokens ?? fallback.cacheReadInputTokens,
    cacheCreationInputTokens:
      primary.cacheCreationInputTokens ?? fallback.cacheCreationInputTokens,
    costUsd: primary.costUsd ?? fallback.costUsd
  };
}

function hasAnyUsage(usage: UsageSummary) {
  return Object.values(usage).some((value) => typeof value === "number");
}

function roughTokenEstimate(value: string) {
  return Math.ceil(value.length / 4);
}

function assertRecord(value: unknown): TranscriptRecord {
  if (!isObject(value)) {
    throw new Error("Expected each transcript entry to be a JSON object.");
  }

  return value;
}

function extractRecords(value: unknown): TranscriptRecord[] {
  if (Array.isArray(value)) {
    return value.map(assertRecord);
  }

  const record = assertRecord(value);
  const arrayKeys = ["events", "records", "messages", "transcript", "conversation", "items"];

  for (const key of arrayKeys) {
    const nested = record[key];

    if (Array.isArray(nested) && nested.every(isObject)) {
      return nested.map(assertRecord);
    }
  }

  return [record];
}

function isToolResultEvent(record: TranscriptRecord) {
  const message = getObject(record.message);
  const content = message?.content;

  if (!Array.isArray(content)) return false;

  return content.some(
    (block) => isObject(block) && getString(block.type) === "tool_result"
  );
}

function getObject(value: unknown): Record<string, unknown> | null {
  return isObject(value) ? value : null;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getString(value: unknown) {
  return typeof value === "string" ? value : null;
}

function getNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getBoolean(value: unknown) {
  return typeof value === "boolean" ? value : null;
}

function compact(values: Array<string | null | undefined>) {
  return values.filter((value): value is string => Boolean(value));
}

function titleCase(value: string) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

function truncate(value: string, maxLength: number) {
  const normalized = value.replace(/\s+/g, " ").trim();

  if (normalized.length <= maxLength) return normalized;

  return `${normalized.slice(0, maxLength - 1)}...`;
}

function jsonErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function formatNumber(value: number | null | undefined) {
  return typeof value === "number" ? new Intl.NumberFormat("en-US").format(value) : "-";
}

export function formatCost(value: number | null | undefined) {
  return typeof value === "number" ? `$${value.toFixed(4)}` : "-";
}

export function formatDuration(value: number | null | undefined) {
  if (typeof value !== "number") return "-";

  const seconds = Math.round(value / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) return `${remainingSeconds}s`;

  return `${minutes}m ${remainingSeconds}s`;
}
