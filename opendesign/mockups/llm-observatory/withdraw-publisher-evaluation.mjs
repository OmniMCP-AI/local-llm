import { readdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { catalogReleasePattern, modelIdPattern, modelShard } from "./catalog-paths.mjs";
import { isPublicIssue, validateEvidenceState } from "./evidence-state.mjs";
import { digest, readJson } from "./research-released-snapshot.mjs";

const matchingSource = (row, source) =>
  row.supplemental?.publisherEvaluations?.some((evaluation) => evaluation.source === source);

async function affectedCatalogs(root, source) {
  const data = join(root, "catalog-data");
  const affected = [];
  for (const release of (await readdir(data)).filter((name) => catalogReleasePattern.test(name)).sort()) {
    const directory = join(data, release);
    const shards = (await readdir(directory)).filter((name) => /^[a-z0-9_][a-z0-9_.-]?\.json$/.test(name));
    for (const shard of shards) {
      if ((await readJson(join(directory, shard))).some((row) => matchingSource(row, source))) {
        affected.push(release);
        break;
      }
    }
  }
  return affected;
}

try {
  const [requestPath, previous, output, ...archives] = process.argv.slice(2);
  if (!requestPath || !previous || !output) {
    throw new Error("Usage: node withdraw-publisher-evaluation.mjs REQUEST.json PREVIOUS_PAGES NEW_POLICY.json [HISTORICAL_PAGES ...]");
  }
  const { action, modelId, source, issue } = await readJson(requestPath);
  const url = typeof source === "string" ? URL.parse(source) : null;
  if (action !== "withdraw" || typeof modelId !== "string" || !modelIdPattern.test(modelId) || !isPublicIssue(issue) ||
      !url || url.protocol !== "https:" || url.username || url.password || url.href !== source) {
    throw new Error("Supply an exact publisher source, model repository, and reviewed project issue");
  }
  const { catalogRelease } = await readJson(join(previous, "wiki/manifest.json"));
  if (!catalogReleasePattern.test(catalogRelease)) throw new Error("Invalid published catalog release");
  const rows = await readJson(join(previous, "catalog-data", catalogRelease, modelShard(modelId) + ".json"))
    .catch((error) => { if (error.code !== "ENOENT") throw error; return []; });
  if (!rows.some((row) => row.id === modelId && matchingSource(row, source))) {
    throw new Error("Model and source do not identify a published publisher evaluation");
  }
  const state = validateEvidenceState(await readJson(join(previous, "evidence-quarantine.json")));
  const sourceSha256 = digest(source);
  const existing = state.publisherWithdrawals.find((entry) => entry.sourceSha256 === sourceSha256);
  if (existing && existing.issue !== issue) throw new Error("Publisher source already has a reviewed withdrawal");
  const affected = await Promise.all([...new Set([previous, ...archives].map((path) => resolve(path)))]
    .map((root) => affectedCatalogs(root, source)));
  const catalogReleases = [...new Set([...(existing?.catalogReleases ?? []), ...affected.flat(), catalogRelease])].sort();
  const next = validateEvidenceState({
    ...state,
    publisherWithdrawals: [
      ...state.publisherWithdrawals.filter((entry) => entry.sourceSha256 !== sourceSha256),
      { sourceSha256, issue, catalogReleases },
    ],
  });
  await writeFile(output, JSON.stringify(next, null, 2) + "\n", { flag: "wx", mode: 0o600 });
  console.log("/wiki/evidence-updates#" + sourceSha256);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
