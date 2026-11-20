import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, readdir, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { withLocalPages } from "./pages-test-server.mjs";

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
  t.after(() => rm(scratch, { recursive: true, force: true }));

  const env = {
    ...process.env,
    FASTEST_PUBLIC_ORIGIN: origin,
    FASTEST_RELEASE_DATE: "2026-12-21",
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

  await withLocalPages(output, t.signal, async (origin) => {
    const { stdout } = await run(process.execPath, ["verify-pages.mjs", origin, env.FASTEST_PUBLIC_ORIGIN], {
      cwd: here, signal: t.signal,
    });
    t.diagnostic(stdout.trim());
  });
});
