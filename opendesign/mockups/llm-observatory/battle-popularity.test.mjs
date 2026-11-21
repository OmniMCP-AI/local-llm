import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Client } from "pg";
import { readHardwareCatalog } from "./catalog-hardware-build.mjs";
import { importLocalCatalog } from "./catalog-pg.mjs";
import { withLocalPages } from "./pages-test-server.mjs";

const here = fileURLToPath(new URL(".", import.meta.url));
const testDatabaseUrl = process.env.FASTEST_TEST_DATABASE_URL;
const battlesDatabaseUrl = process.env.FASTEST_TEST_BATTLES_DATABASE_URL;

async function publishPin(output, snapshotId, paths = []) {
  const release = "v1-" + snapshotId.slice(0, 16);
  await mkdir(join(output, "wiki"), { recursive: true });
  await mkdir(join(output, "catalog", release), { recursive: true });
  await writeFile(join(output, "wiki", "manifest.json"), JSON.stringify({ catalogRelease: release }));
  await writeFile(join(output, "catalog", release, "manifest.json"), JSON.stringify({ release, snapshotId }));
  await writeFile(join(output, "evidence-quarantine.json"), JSON.stringify({ paths }));
  return release;
}

test("hosted Pages ranks opt-in comparisons from the exact published PostgreSQL catalog", {
  skip: !testDatabaseUrl || !battlesDatabaseUrl, timeout: 90_000,
}, async (t) => {
  const assets = await mkdtemp(join(tmpdir(), "fastest-battles-test-"));
  t.after(() => rm(assets, { recursive: true, force: true }));
  await writeFile(join(assets, "index.html"), "<title>Battle popularity test</title>");
  await writeFile(join(assets, "_routes.json"), JSON.stringify({
    version: 1, include: ["/api/battle-popularity"], exclude: [],
  }));
  const hardware = await readHardwareCatalog(here);
  hardware.manifest = { ...hardware.manifest, popularityTestRun: randomUUID() };
  const { snapshotId } = await importLocalCatalog(hardware, testDatabaseUrl);
  const release = await publishPin(assets, snapshotId);
  const machineLeft = "V005-HP-TEST";
  const machineRight = "apple-mac-mini-m4-24gb-512gb";
  hardware.catalog.machines.find(({ id }) => id === machineRight).name += " (new snapshot)";
  const { snapshotId: newerSnapshot } = await importLocalCatalog(hardware, testDatabaseUrl);
  const newerRelease = "v1-" + newerSnapshot.slice(0, 16);
  assert.notEqual(newerRelease, release);
  const left = "intel-arc-b580";
  const right = "nvidia-geforce-rtx-4090";
  const comparison = { release, kind: "cards", left, right, requestId: randomUUID() };
  const machineComparison = { release, kind: "machines", left: machineLeft, right: machineRight, requestId: randomUUID() };
  const endpoint = (origin) => origin + "/api/battle-popularity";
  const get = (origin, kind = "cards", pin = release) =>
    fetch(endpoint(origin) + "?" + new URLSearchParams({ release: pin, kind }), { signal: t.signal });
  const post = (origin, selection, headers = {}) => fetch(endpoint(origin), {
    method: "POST",
    headers: { Origin: origin, "Content-Type": "application/json", ...headers },
    body: JSON.stringify(selection),
    signal: t.signal,
  });

  await withLocalPages(assets, t.signal, async (origin) => {
    const empty = await get(origin);
    assert.equal(empty.status, 200);
    assert.equal(empty.headers.get("Cache-Control"), "no-store");
    assert.deepEqual(await empty.json(), { pairs: [] });
    assert.equal((await get(origin, "cards", newerRelease)).status, 404);
    assert.equal((await get(origin, "models")).status, 400);
    assert.equal((await fetch(endpoint(origin) + "?release=" + release + "&kind=cards&kind=machines")).status, 400);
    assert.equal((await fetch(endpoint(origin), { method: "DELETE" })).status, 405);
    assert.equal((await post(origin, comparison, { Origin: "https://elsewhere.example" })).status, 403);
    assert.equal((await fetch(endpoint(origin), {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(comparison),
    })).status, 403);
    assert.equal((await post(origin, comparison, { "Content-Type": "text/plain" })).status, 415);
    assert.equal((await fetch(endpoint(origin), {
      method: "POST", headers: { Origin: origin, "Content-Type": "application/json" }, body: "{",
    })).status, 400);
    for (const invalid of [
      { ...comparison, left: right },
      { ...comparison, left: "no-such-card-in-catalog" },
      { ...comparison, left: left + "\n" },
      { ...comparison, kind: "machines" },
      { ...comparison, requestId: "anonymous" },
      { ...comparison, release: release + "\n" },
      { ...comparison, identity: "person" },
      { ...comparison, left: "a".repeat(1024) },
      { ...machineComparison, left: "V001-HP-G001" },
    ]) {
      assert.equal((await post(origin, invalid)).status, 400);
    }

    const clicks = await Promise.all([
      post(origin, comparison),
      post(origin, { ...comparison, left: right, right: left }),
      post(origin, comparison),
    ]);
    assert.deepEqual(clicks.map(({ status }) => status).sort(), [200, 200, 201]);
    for (const click of clicks) assert.deepEqual(await click.json(), { recorded: true });
    assert.equal((await post(origin, { ...comparison, right: "nvidia-geforce-rtx-3090" })).status, 409);
    assert.equal((await post(origin, machineComparison)).status, 201);
    assert.deepEqual(await (await get(origin, "machines")).json(), {
      pairs: [{ left: machineLeft, right: machineRight, count: 1 }],
    });
    assert.deepEqual(await (await get(origin)).json(), { pairs: [{ left, right, count: 1 }] });
  }, { battlesDatabaseUrl });

  // Set up fixed day offsets so the public-window check does not wait for a clock change.
  const owner = new Client({ connectionString: testDatabaseUrl });
  const pagesRole = new Client({ connectionString: battlesDatabaseUrl });
  try {
    await owner.connect();
    await pagesRole.connect();
    await assert.rejects(pagesRole.query("SELECT * FROM fastest_battles.recorded_request"), { code: "42501" });
    await assert.rejects(pagesRole.query("DELETE FROM fastest_battles.daily_comparison"), { code: "42501" });
    await assert.rejects(pagesRole.query("SELECT id FROM fastest_catalog.gpu"), { code: "42501" });
    await owner.query(`
      INSERT INTO fastest_battles.daily_comparison (snapshot_id, kind, recorded_on, left_id, right_id, count)
      VALUES ($1, 'cards', (now() AT TIME ZONE 'UTC')::date - 29, $2, $3, 2),
             ($1, 'cards', (now() AT TIME ZONE 'UTC')::date - 30, $2, $3, 100)
    `, [snapshotId, left, right]);
  } finally {
    await Promise.all([owner.end(), pagesRole.end()]);
  }

  const tiedIds = [
    "amd-instinct-mi100", "amd-instinct-mi210", "amd-instinct-mi250", "amd-instinct-mi250x",
    "amd-instinct-mi300x", "amd-radeon-ai-pro-r9700", "amd-radeon-instinct-mi50",
    "amd-radeon-instinct-mi50-16gb", "amd-radeon-instinct-mi50-32gb", "amd-radeon-pro-w7800", "amd-radeon-pro-w7900",
  ];
  await withLocalPages(assets, t.signal, async (origin) => {
    assert.deepEqual(await (await get(origin)).json(), { pairs: [{ left, right, count: 3 }] });
    for (const id of tiedIds.toReversed()) {
      assert.equal((await post(origin, { ...comparison, left: id, requestId: randomUUID() })).status, 201);
    }
    assert.deepEqual(await (await get(origin)).json(), {
      pairs: [{ left, right, count: 3 }, ...tiedIds.slice(0, 9).map(id => ({ left: id, right, count: 1 }))],
    });
  }, { battlesDatabaseUrl });

  await publishPin(assets, newerSnapshot);
  const newerComparison = { ...comparison, release: newerRelease };
  await withLocalPages(assets, t.signal, async (origin) => {
    assert.equal((await get(origin)).status, 404);
    assert.deepEqual(await (await get(origin, "cards", newerRelease)).json(), { pairs: [] });
    assert.equal((await post(origin, newerComparison)).status, 409);
    assert.equal((await post(origin, { ...newerComparison, requestId: randomUUID() })).status, 201);
    assert.deepEqual(await (await get(origin, "cards", newerRelease)).json(), { pairs: [{ left, right, count: 1 }] });
  }, { battlesDatabaseUrl });

  await publishPin(assets, snapshotId, ["/catalog-data/" + release + "/*"]);
  await withLocalPages(assets, t.signal, async (origin) => {
    assert.equal((await get(origin)).status, 410);
    assert.equal((await post(origin, comparison)).status, 410);
  }, { battlesDatabaseUrl });

  await publishPin(assets, snapshotId);
  await withLocalPages(assets, t.signal, async (origin) => {
    assert.equal((await get(origin)).status, 503);
    assert.equal((await post(origin, comparison)).status, 503);
  });
});
