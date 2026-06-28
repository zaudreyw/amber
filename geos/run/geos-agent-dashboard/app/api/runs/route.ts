import { readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";

export const dynamic = "force-dynamic";

const EVAL_ROOT = "/home/brianliu/data/eval";

// Directories that contain run_name subdirs with task subdirs
const AGENT_DIRS = [
  "claude_code_repo3_plugin",
  "claude_code",
  "cursor_composer2",
];

async function readJsonFile(path: string): Promise<Record<string, unknown> | null> {
  try {
    const text = await readFile(path, "utf8");
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function safeReaddir(path: string): Promise<string[]> {
  try {
    const entries = await readdir(path);
    return entries;
  } catch {
    return [];
  }
}

async function isDir(path: string): Promise<boolean> {
  try {
    const s = await stat(path);
    return s.isDirectory();
  } catch {
    return false;
  }
}

export async function GET() {
  const runs: Record<string, unknown>[] = [];

  for (const agent of AGENT_DIRS) {
    const agentPath = join(EVAL_ROOT, agent);
    const runNames = await safeReaddir(agentPath);

    for (const runName of runNames) {
      const runPath = join(agentPath, runName);
      if (!(await isDir(runPath))) continue;

      const taskNames = await safeReaddir(runPath);
      const tasks: Record<string, unknown>[] = [];

      for (const taskName of taskNames) {
        const taskPath = join(runPath, taskName);
        if (!(await isDir(taskPath))) continue;

        const statusPath = join(taskPath, "status.json");
        const status = await readJsonFile(statusPath);

        if (status) {
          tasks.push({
            task: taskName,
            taskPath,
            ...status,
          });
        } else {
          tasks.push({
            task: taskName,
            taskPath,
            agent,
            run_name: runName,
            status: "pending",
            process_status: "pending",
          });
        }
      }

      if (tasks.length > 0) {
        // Sort tasks alphabetically
        tasks.sort((a, b) => String(a.task).localeCompare(String(b.task)));

        const completedCount = tasks.filter((t) =>
          ["success", "failed", "timeout", "interrupted", "error"].includes(String(t.process_status))
        ).length;
        const runningCount = tasks.filter((t) =>
          String(t.process_status) === "running"
        ).length;

        runs.push({
          agent,
          run_name: runName,
          runPath,
          tasks,
          completedCount,
          runningCount,
          totalCount: tasks.length,
        });
      }
    }
  }

  // Sort: runs with running tasks first, then by agent+run_name
  runs.sort((a, b) => {
    const aRunning = Number(a.runningCount) > 0 ? 0 : 1;
    const bRunning = Number(b.runningCount) > 0 ? 0 : 1;
    if (aRunning !== bRunning) return aRunning - bRunning;
    return `${a.agent}/${a.run_name}`.localeCompare(`${b.agent}/${b.run_name}`);
  });

  return Response.json({ runs, evalRoot: EVAL_ROOT });
}
