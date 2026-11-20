import assert from "node:assert/strict";
import { execFile, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { once } from "node:events";
import { mkdtemp, readFile, readdir, rm, stat, symlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import { createInterface } from "node:readline";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const run = promisify(execFile);
const here = fileURLToPath(new URL(".", import.meta.url));
const origin = "https://fastest.ai";

async function releaseDigest(directory) {
  const files = [];
  for (const entry of await readdir(directory, { recursive: true, withFileTypes: true })) {
    if (entry.isFile()) files.push(relative(directory, join(entry.parentPath, entry.name)));
  }
  assert.ok(files.length <= 20_000, "Pages free-tier asset limit");
  const hash = createHash("sha256");
  for (const file of files.sort()) {
    const path = join(directory, file);
    assert.ok((await stat(path)).size <= 25 * 1024 ** 2, `Pages asset limit: ${file}`);
    hash.update(file + "\0");
    hash.update(createHash("sha256").update(await readFile(path)).digest());
  }
  return hash.digest("hex");
}

test("a date-pinned Pages build is reproducible and serves crawler discovery through Wrangler", { timeout: 60_000 }, async (t) => {
  const scratch = await mkdtemp(join(tmpdir(), "fastest-pages-"));
  const output = join(scratch, "pages");
  let worker;
  let workerExit;
  function stopWorker() {
    if (!worker?.pid) return;
    try { process.kill(-worker.pid, "SIGTERM"); }
    catch (error) { if (error.code !== "ESRCH") throw error; }
  }
  const interrupted = () => stopWorker();
  process.once("SIGINT", interrupted);
  process.once("SIGTERM", interrupted);
  t.after(async () => {
    process.removeListener("SIGINT", interrupted);
    process.removeListener("SIGTERM", interrupted);
    try {
      stopWorker();
      await workerExit;
    } finally {
      await rm(scratch, { recursive: true, force: true });
    }
  });

  const env = {
    ...process.env,
    FASTEST_PUBLIC_ORIGIN: origin,
    FASTEST_RELEASE_DATE: "2026-12-21",
    WRANGLER_SEND_METRICS: "false",
    WRANGLER_LOG_PATH: join(scratch, "wrangler.log"),
  };
  for (const name of ["FASTEST_RELEASE_ORIGIN", "FASTEST_RESEARCH_METADATA_APPROVALS",
    "FASTEST_EVIDENCE_STATE", "FASTEST_RESEARCH_ARCHIVE"]) delete env[name];
  const build = (directory) => run(process.execPath, ["build.mjs", "--pages", "--output", directory], {
    cwd: here, env, signal: t.signal,
  });
  const rebuilt = join(scratch, "rebuilt");
  await build(output);
  await build(rebuilt);
  assert.equal(await releaseDigest(output), await releaseDigest(rebuilt));
  const manifest = JSON.parse(await readFile(join(output, "wiki/manifest.json"), "utf8"));
  assert.deepEqual(manifest.highlights.map(({ id }) => id), ["dual-rtx-2080-ti-nvlink", "open-benchmark-requests"]);
  const research = JSON.parse(await readFile(join(output, "research", manifest.researchRelease, "index.json"), "utf8"));
  const example = research.sources.find(({ id }) => id === "llama-bench-jsonl-example");
  assert.deepEqual(example?.records.map(({ dimension }) => dimension), ["prefill", "generation"]);
  assert.ok(!research.sources.some(({ format }) => format === "video"));

  await symlink(join(here, "functions"), join(scratch, "functions"), "dir");
  worker = spawn(process.execPath, [
    join(here, "node_modules/wrangler/bin/wrangler.js"), "pages", "dev", output, "--ip", "127.0.0.1",
    "--port", "0", "--persist-to", join(scratch, "persist"), "--compatibility-date", "2026-11-20",
    "--show-interactive-dev-session=false",
  ], { cwd: scratch, env, stdio: ["ignore", "pipe", "pipe"], detached: true });
  workerExit = once(worker, "exit");
  let errors = "";
  worker.stderr.on("data", (chunk) => { errors += chunk; });
  const lines = createInterface({ input: worker.stdout });
  t.signal.addEventListener("abort", () => lines.close(), { once: true });
  for await (const line of lines) {
    const ready = line.match(/Ready on (http:\/\/127\.0\.0\.1:\d+)/);
    if (!ready) continue;
    try {
      const { stdout } = await run(process.execPath, ["verify-pages.mjs", ready[1], origin], {
        cwd: here, signal: t.signal,
      });
      t.diagnostic(stdout.trim());
    } finally {
      lines.close();
    }
    return;
  }
  assert.fail("Wrangler did not start\n" + errors);
});
