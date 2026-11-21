import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));

export async function withLocalPages(output, signal, verify, { feedbackDatabaseUrl, battlesDatabaseUrl, staticOnly = false } = {}) {
  const scratch = await mkdtemp(join(tmpdir(), "fastest-pages-worker-"));
  let worker;
  let closed;
  function stopWorker() {
    if (!worker?.pid) return;
    try { process.kill(-worker.pid, "SIGTERM"); }
    catch (error) { if (error.code !== "ESRCH") throw error; }
  }
  process.once("SIGINT", stopWorker);
  process.once("SIGTERM", stopWorker);
  try {
    if (!staticOnly) await symlink(join(here, "functions"), join(scratch, "functions"), "dir");
    const bindings = {
      ...(feedbackDatabaseUrl && { FEEDBACK_PG: feedbackDatabaseUrl }),
      ...(battlesDatabaseUrl && { BATTLES_PG: battlesDatabaseUrl }),
    };
    if (Object.keys(bindings).length) {
      await writeFile(join(scratch, "wrangler.json"), JSON.stringify({
        name: "fastest-pages-test",
        pages_build_output_dir: output,
        hyperdrive: Object.keys(bindings).map(binding => ({ binding, id: "00000000000000000000000000000000" })),
      }));
    }
    worker = spawn(process.execPath, [
      join(here, "node_modules/wrangler/bin/wrangler.js"), "pages", "dev", output, "--ip", "127.0.0.1",
      "--port", "0", "--inspector-port", "0", "--persist-to", join(scratch, "persist"), "--compatibility-date", "2026-11-20",
      "--show-interactive-dev-session=false",
    ], {
      cwd: scratch, stdio: ["ignore", "pipe", "pipe"], detached: true,
      env: {
        ...process.env,
        WRANGLER_SEND_METRICS: "false",
        WRANGLER_LOG_PATH: join(scratch, "wrangler.log"),
        ...Object.fromEntries(Object.entries(bindings).map(([binding, url]) => [
          "CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_" + binding, url,
        ])),
      },
    });
    closed = once(worker, "close");
    closed.catch(() => {});
    let errors = "";
    worker.stderr.on("data", (chunk) => { errors += chunk; });
    const lines = createInterface({ input: worker.stdout });
    const startup = AbortSignal.any([signal, AbortSignal.timeout(30_000)]);
    startup.addEventListener("abort", stopWorker, { once: true });
    for await (const line of lines) {
      const ready = line.match(/Ready on (http:\/\/127\.0\.0\.1:\d+)/);
      if (!ready) continue;
      startup.removeEventListener("abort", stopWorker);
      signal.addEventListener("abort", stopWorker, { once: true });
      return await verify(ready[1]);
    }
    throw new Error("Wrangler did not start\n" + errors);
  } finally {
    process.removeListener("SIGINT", stopWorker);
    process.removeListener("SIGTERM", stopWorker);
    signal.removeEventListener("abort", stopWorker);
    try {
      stopWorker();
      await closed;
    } finally {
      await rm(scratch, { recursive: true, force: true });
    }
  }
}
