/**
 * Thin CLI: discover files, build ScanRequest, POST /scan, stream WS events.
 * No local LLM — server runs analysis.
 */
import * as fs from "node:fs/promises";
import * as path from "node:path";
const DEFAULT_API = "http://127.0.0.1:8000";

type CodeChunk = {
  id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  code: string;
  language: string;
};

function guessLanguage(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const map: Record<string, string> = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
  };
  return map[ext] ?? "unknown";
}

async function collectFiles(root: string, acc: string[] = []): Promise<string[]> {
  const st = await fs.stat(root);
  if (st.isFile()) {
    acc.push(root);
    return acc;
  }
  const entries = await fs.readdir(root, { withFileTypes: true });
  for (const e of entries) {
    if (e.name.startsWith(".") || e.name === "node_modules") continue;
    const full = path.join(root, e.name);
    if (e.isDirectory()) await collectFiles(full, acc);
    else acc.push(full);
  }
  return acc;
}

function fileToChunk(absPath: string, root: string, code: string): CodeChunk {
  const rel = path.relative(root, absPath) || path.basename(absPath);
  const lines = code.split(/\r?\n/);
  return {
    id: rel.replace(/[^\w.-]+/g, "_"),
    file_path: rel,
    start_line: 1,
    end_line: Math.max(1, lines.length),
    code,
    language: guessLanguage(absPath),
  };
}

function httpToWs(scanUrl: string): string {
  return scanUrl.replace(/^http/, "ws");
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node scan.js <path-to-file-or-dir> [apiBase]");
    process.exit(1);
  }
  const target = path.resolve(args[0]!);
  const apiBase = (args[1] ?? DEFAULT_API).replace(/\/$/, "");
  const scanUrl = `${apiBase}/api/v1/scan`;
  const root = (await fs.stat(target)).isDirectory() ? target : path.dirname(target);
  const files = (await collectFiles(target)).filter((f) => {
    const skip = [".png", ".jpg", ".gif", ".woff", ".zip", ".pyc"];
    return !skip.some((s) => f.endsWith(s));
  });

  const chunks: CodeChunk[] = [];
  for (const f of files) {
    const code = await fs.readFile(f, "utf8");
    if (code.length > 500_000) continue;
    chunks.push(fileToChunk(f, root, code));
  }

  const res = await fetch(scanUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chunks,
      metadata: { repo_root: root, mode: "local_only" },
    }),
  });
  if (!res.ok) {
    console.error(await res.text());
    process.exit(1);
  }
  const { id } = (await res.json()) as { id: string };
  console.error(`Scan ${id} submitted; streaming events…`);

  const wsUrl = `${httpToWs(apiBase)}/api/v1/scan/${id}/stream`;
  const WebSocketImpl =
    (globalThis as unknown as { WebSocket?: typeof WebSocket }).WebSocket;
  if (!WebSocketImpl) {
    console.error("WebSocket not available in this runtime.");
    process.exit(1);
  }
  const ws = new WebSocketImpl(wsUrl);
  ws.addEventListener("message", (ev) => {
    console.log(String((ev as MessageEvent).data));
  });
  ws.addEventListener("open", () => {
    ws.send("ping");
  });
  await new Promise<void>((resolve, reject) => {
    ws.addEventListener("close", () => resolve());
    ws.addEventListener("error", () => reject(new Error("ws error")));
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
