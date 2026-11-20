import assert from "node:assert/strict";
import { checkedPagesFile, pagesFileRoutes } from "./evidence-public-paths.mjs";
import { validateEvidenceState } from "./evidence-state.mjs";
import { languages } from "./locale-settings.mjs";
import { digest, readJson } from "./research-released-snapshot.mjs";
import { releaseOrigin } from "./release-origin.mjs";

const sha256 = /^[a-f0-9]{64}$/;
const routePattern = /^\/(?:[a-z0-9._/-]*)(?:\?(?:evidence_id|release)=[a-f0-9-]+)?$/i;
const uuid = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const benchmarkFiles = ["benchmark.html", "benchmark.md", "chart.json", "table.json", "manifest.json"];
const runLimit = AbortSignal.timeout(120_000);
const conditional = { "If-None-Match": "*", Range: "bytes=0-63" };

function originFor(value) {
  const https = releaseOrigin(value);
  if (https) return https;
  const url = new URL(value);
  assert.ok(/^http:\/\/127\.0\.0\.1(?::\d+)?\/$/.test(url.href), "Supply an HTTPS origin or a loopback test origin");
  return url.origin;
}

function checkedRoute(path) {
  assert.ok(typeof path === "string" && routePattern.test(path) && !path.includes("//") &&
    !path.split(/[/?]/).some((part) => part === "." || part === ".."), "Invalid route in the review");
  return path;
}

async function read(origin, path, headers, { html = false } = {}) {
  const response = await fetch(new URL(checkedRoute(path), origin), {
    headers, redirect: "manual", signal: AbortSignal.any([runLimit, AbortSignal.timeout(15_000)]),
  });
  let bytes = Buffer.from(await response.arrayBuffer());
  const control = response.headers.get("cache-control") ?? "";
  assert.match(control, /(?:^|,)\s*no-store\s*(?:,|$)/i, `${path} must be no-store`);
  for (const validator of ["etag", "last-modified", "cdn-cache-control", "cloudflare-cdn-cache-control"]) {
    assert.equal(response.headers.get(validator), null, `${path} returned ${validator}`);
  }
  assert.ok(!(Number(response.headers.get("age")) > 0) &&
    !/^(HIT|STALE|UPDATING|REVALIDATED|EXPIRED)$/i.test(response.headers.get("cf-cache-status") ?? ""),
  `${path} returned a cached response`);
  if (html && response.headers.get("content-type")?.startsWith("text/html")) {
    // Cloudflare may insert the visitor's language on the root HTML element.
    const body = bytes.toString("utf8").replace(/^(\s*<!doctype html>\s*<html\b[^>]*?) data-visitor-language="([^"]+)"(?=[\s>])/i,
      (match, tag, language) => Object.hasOwn(languages, language) ? tag : match);
    bytes = Buffer.from(body);
  }
  return { status: response.status, bytes, location: response.headers.get("location") };
}

async function probe(origin, path, status, hash, earlier = []) {
  let bytes;
  for (const headers of [undefined, conditional]) {
    const reply = await read(origin, path, headers, { html: status === 200 && !path.startsWith("/releases/") });
    assert.equal(reply.status, status, `${path} status`);
    const actual = digest(reply.bytes);
    if (hash) assert.equal(actual, hash, `${path} differs from reviewed bytes`);
    else assert.ok(!earlier.includes(actual), `${path} still serves earlier evidence`);
    bytes = reply.bytes;
  }
  return bytes;
}

function pageFiles(review) {
  const files = new Map();
  const entries = [...review.changes, ...review.history.flatMap(({ artifacts }) => artifacts)];
  for (const { path, before, after } of entries) {
    checkedRoute(path);
    if (!checkedPagesFile(path)) continue;
    assert.ok([before, after].every((hash) => hash === null || sha256.test(hash)), "Invalid artifact digest in the review");
    const file = files.get(path) ?? { hash: after, earlier: [] };
    assert.equal(after, file.hash, `${path} has inconsistent reviewed digests`);
    if (before) file.earlier.push(before);
    files.set(path, file);
  }
  return files;
}

async function verifyPages(review, origin) {
  const files = pageFiles(review);
  const expected = (path) => {
    const hash = files.get(path)?.hash;
    assert.match(hash ?? "", sha256, `${path} has no reviewed digest`);
    return hash;
  };
  const manifest = JSON.parse(await probe(origin, "/wiki/manifest.json", 200, expected("/wiki/manifest.json")));
  assert.equal(manifest.release, review.candidate.wiki, "Wrong wiki release");
  assert.equal(manifest.researchRelease, review.candidate.research, "Wrong research release");
  const policyPath = "/evidence-quarantine.json";
  const state = validateEvidenceState(JSON.parse(await probe(origin, policyPath, 200, expected(policyPath))));
  assert.ok(state.updates.some(({ id, action, research }) =>
    review.resolutionPath === "/wiki/evidence-updates#" + id && action === review.action &&
    research === "/research/" + manifest.researchRelease + "/library"), "Missing reviewed resolution");
  const denied = new Set(state.paths);
  const prefixes = state.paths.filter((path) => path.endsWith("/*")).map((path) => path.slice(0, -2));
  const probes = new Map();
  for (const path of prefixes) {
    probes.set(path, { status: 410 });
    probes.set(path + "/", { status: 410 });
  }
  for (const [file, { hash, earlier }] of files) {
    if (file === policyPath || file === "/wiki/manifest.json") continue;
    const [url, ...aliases] = pagesFileRoutes(file);
    if (hash) probes.set(url, { status: 200, hash });
    else {
      for (const path of [url, ...aliases]) {
        const blocked = denied.has(path) || prefixes.some((prefix) => path === prefix || path.startsWith(prefix + "/"));
        probes.set(path, { status: blocked ? 410 : 404, earlier });
      }
    }
  }
  const items = [...probes];
  for (let offset = 0; offset < items.length; offset += 8) {
    await Promise.all(items.slice(offset, offset + 8).map(([path, { status, hash, earlier }]) =>
      probe(origin, path, status, hash, earlier)));
  }
  return items.length + 2;
}

const evidenceApi = "/api/v1/evidence?";
const benchmarkPath = (release, file) => `/releases/${release}/${file}`;

async function verifyBenchmark(review, origin) {
  const { benchmarkRelease, benchmarkEvidenceId, benchmarkEarlierExports } = review;
  const withdrawn = review.action === "withdraw";
  assert.match(benchmarkRelease, uuid);
  assert.match(benchmarkEvidenceId, uuid);
  const changes = new Map(review.changes.map(({ path, after }) => [path, after]));
  const earlier = new Set();
  for (const [path, hash] of Object.entries(benchmarkEarlierExports)) {
    const [, prefix, pin, file, extra] = path.split("/");
    assert.ok(prefix === "releases" && uuid.test(pin) && benchmarkFiles.includes(file) && extra === undefined &&
      sha256.test(hash), "Invalid earlier benchmark export");
    earlier.add(pin);
  }
  assert.ok(earlier.size && (withdrawn === earlier.has(benchmarkRelease)), "Inconsistent benchmark release history");

  async function verifyApi(path, pin, table) {
    const row = table.rows[0];
    const published = row && ["measured", "contributor"].includes(row.kind);
    const result = JSON.parse(await probe(origin, path, withdrawn ? 410 : published ? 200 : 404));
    if (withdrawn) {
      assert.equal(result.release_id, pin, path);
      assert.equal(result.status, "withdrawn", path);
      assert.ok(Object.keys(result).every((key) =>
        ["api_version", "status", "error", "release_id", "revision"].includes(key)), `${path} exposed withdrawn fields`);
    } else if (published) {
      assert.equal(result.release_id, pin, path);
      assert.equal(result.evidence_id, benchmarkEvidenceId, path);
      assert.deepEqual(result.metric, row.metric, path);
      assert.deepEqual(result.citations, [row.source], path);
    }
  }

  const tables = new Map();
  for (const pin of new Set([...earlier, benchmarkRelease])) {
    const status = withdrawn ? 410 : 200;
    for (const file of benchmarkFiles) {
      const path = benchmarkPath(pin, file);
      const before = benchmarkEarlierExports[path];
      const hash = withdrawn || pin === benchmarkRelease ? changes.get(path) : before;
      assert.ok(sha256.test(hash) && (!earlier.has(pin) || sha256.test(before)) &&
        (!withdrawn || before !== hash), `${path} has no reviewed benchmark digest`);
      const bytes = await probe(origin, path, status, hash);
      if (file === "table.json") tables.set(pin, JSON.parse(bytes));
    }
    await verifyApi(evidenceApi + "release=" + pin, pin, tables.get(pin));
  }
  const latest = withdrawn ? [...earlier].reduce((selected, pin) =>
    tables.get(pin).revision > tables.get(selected).revision ? pin : selected) : benchmarkRelease;
  await verifyApi(evidenceApi + "evidence_id=" + benchmarkEvidenceId, latest, tables.get(latest));

  // The global current alias may still point to an unrelated release after withdrawal.
  let current;
  for (const file of benchmarkFiles) {
    const path = benchmarkPath("current", file);
    for (const headers of [undefined, conditional]) {
      const { status, bytes, location } = await read(origin, path, headers);
      if (withdrawn && status === 410) {
        const pin = [...earlier].find((id) => changes.get(benchmarkPath(id, file)) === digest(bytes));
        assert.ok(pin, `${path} differs from all reviewed withdrawal notices`);
        current ??= pin;
        assert.equal(current, pin, `${path} changed the current release`);
        continue;
      }
      assert.equal(status, 307, `${path} status`);
      assert.ok(location, `${path} missing current release link`);
      const redirect = new URL(location, origin);
      const pin = redirect.pathname.split("/")[2];
      assert.ok(uuid.test(pin) && redirect.href === origin + benchmarkPath(pin, file) &&
        (withdrawn ? !earlier.has(pin) : pin === benchmarkRelease), `${path} points to an unexpected release`);
      current ??= pin;
      assert.equal(current, pin, `${path} changed the current release`);
      if (withdrawn && !headers) {
        await probe(origin, benchmarkPath(pin, file), 200, null, [...earlier].map((id) => benchmarkEarlierExports[benchmarkPath(id, file)]));
      }
    }
  }
}

try {
  const args = process.argv.slice(2);
  const plan = args[0] === "--purge-plan";
  if (plan) args.shift();
  const [file, pages, release, ...extra] = args;
  assert.ok(file && pages && !extra.length,
    "Usage: node verify-evidence-resolution.mjs [--purge-plan] REVIEW.json PAGES_ORIGIN [RELEASE_ORIGIN]");
  const review = await readJson(file);
  assert.ok(["withdraw", "correct"].includes(review.action), "Unknown review action");
  assert.equal(digest(JSON.stringify(review.changes, null, 2) + "\n"), review.diffSha256, "Review diff digest mismatch");
  const pagesOrigin = originFor(pages);
  const benchmarkOrigin = release && originFor(release);
  assert.equal(Boolean(benchmarkOrigin), Boolean(review.benchmarkRelease),
    "Supply the benchmark release origin when the staged review includes a benchmark");
  if (plan) {
    const urls = [...new Set(review.cachePurgePaths)].map((path) => {
      const origin = path.startsWith("/releases/") || path.startsWith(evidenceApi) ? benchmarkOrigin : pagesOrigin;
      assert.ok(origin, "Missing origin for reviewed cache path");
      return origin + checkedRoute(path);
    });
    console.log(urls.join("\n"));
  } else {
    const count = await verifyPages(review, pagesOrigin);
    if (benchmarkOrigin) await verifyBenchmark(review, benchmarkOrigin);
    console.log(`Verified ${review.action === "withdraw" ? "withdrawal" : "correction"} across ${count} Pages routes` +
      (benchmarkOrigin ? " and the benchmark release origin." : "."));
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
