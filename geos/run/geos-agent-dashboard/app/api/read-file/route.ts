import { readFile } from "node:fs/promises";
import { isAbsolute, normalize, resolve } from "node:path";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => null) as { path?: unknown } | null;
    const rawPath = typeof body?.path === "string" ? body.path.trim() : "";

    if (!rawPath) {
      return Response.json({ error: "Provide a file path." }, { status: 400 });
    }

    const normalizedPath = normalize(isAbsolute(rawPath) ? rawPath : resolve(process.cwd(), rawPath));
    const text = await readFile(normalizedPath, "utf8");

    return new Response(text, {
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "x-source-path": normalizedPath
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);

    return Response.json(
      {
        error: "Unable to read the file path.",
        details: message
      },
      { status: 500 }
    );
  }
}
