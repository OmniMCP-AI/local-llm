import { execFile } from "node:child_process";
import { cp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { emptyEvidenceState, isPublicIssue, writeEvidenceState } from "./evidence-state.mjs";
import { withdrawnReference } from "./evidence-provenance.mjs";
import { feedbackId } from "./feedback-policy.mjs";
import { digest, readJson, readResearchSnapshot as snapshot } from "./research-released-snapshot.mjs";

const directory = fileURLToPath(new URL(".", import.meta.url));
const run = promisify(execFile);
const json = (value) => JSON.stringify(value, null, 2) + "\n";
const optionalState = async (root) => readJson(join(root, "evidence-quarantine.json")).catch((error) => {
  if (error.code === "ENOENT") return emptyEvidenceState;
  throw error;
});

async function publicFiles(root, folder = "") {
  const entries = await readdir(join(root, folder), { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name, "en"))) {
    const name = join(folder, entry.name);
    if (entry.isDirectory()) files.push(...await publicFiles(root, name));
    else if (entry.isFile()) files.push(name);
    else throw new Error("Expected a regular public build file: " + name);
  }
  return files;
}

async function hashes(root) {
  return new Map(await Promise.all((await publicFiles(root)).map(async (name) =>
    ["/" + name, digest(await readFile(join(root, name)))])));
}

function intakeRecord(intake, evidenceId, release) {
  if (isPublicIssue(intake?.issue)) return { issue: intake.issue };
  if (!feedbackId.test(intake?.id ?? "") || intake.category !== "correction" ||
      !["queued", "reviewed"].includes(intake.status) || typeof intake.context_json !== "string") {
    throw new Error("A project issue or an opted-in correction receipt is required");
  }
  const shared = JSON.parse(intake.context_json);
  if (!shared?.page || (shared.entity !== evidenceId &&
      !(shared.release === release && ["Wiki", "Research", "Research library", "/wiki/research/"].includes(shared.page)))) {
    throw new Error("Feedback receipt did not share the evidence or prior research release");
  }
  return { id: intake.id, shared: intake.context_json };
}

function receiptUpdate(intake, resolution) {
  if (!intake.id) return null;
  const sql = (text) => "'" + text.replaceAll("'", "''") + "'";
  return `INSERT INTO feedback_resolution (receipt_id, public_path) SELECT id, ${sql(resolution)} FROM feedback_submission
WHERE id = ${sql(intake.id)} AND category = 'correction' AND context_json = ${sql(intake.shared)}
ON CONFLICT(receipt_id) DO UPDATE SET public_path = excluded.public_path;\n`;
}

function containsSource(index, source) {
  return index.sources.some(({ id }) => id === source.id) ||
    index.methods.some(({ url }) => source.id === "youtube/" + new URL(url).searchParams.get("v"));
}

async function resolveBenchmark(benchmark, action, sourceLocator, output) {
  if (!benchmark) return null;
  const decision = join(output, "benchmark-decision.json");
  await writeFile(decision, json({ ...benchmark, action, sourceLocator }), { mode: 0o600 });
  try {
    const { stdout } = await run("python3", ["-B", "-m", "fastest_release.resolution", decision], {
      cwd: resolve(directory, "../../../production"),
    });
    return JSON.parse(stdout);
  } finally {
    await rm(decision, { force: true });
  }
}

function deniedRoutes(path) {
  const routes = [path];
  if (path.endsWith("/index.html")) routes.push(path.slice(0, -"/index.html".length), path.slice(0, -"index.html".length));
  else if (path.endsWith(".html")) routes.push(path.slice(0, -".html".length));
  return routes;
}

async function stageResolution(request, previous, output, approvalPath, archiveRoots) {
  const { action, evidenceId, sourceId, sourceLocator } = request;
  if (!["withdraw", "correct"].includes(action)) throw new Error("Unknown evidence resolution action");
  const { wiki: oldWiki, index: old } = await snapshot(previous);
  const source = old.sources.find(({ id }) => id === sourceId);
  const target = evidenceId === sourceId ? source : source?.records.find(({ id }) => id === evidenceId);
  if (!target || target.url !== sourceLocator) throw new Error("Evidence ID and locator do not identify a published source or record");
  const intake = intakeRecord(request.intake, evidenceId, old.release);
  const priorState = await optionalState(previous);
  const approvals = approvalPath ? await readJson(approvalPath) : {};
  if (action === "withdraw") approvals[sourceId] = { status: "withdrawn" };
  const withdrawnSources = Object.keys(approvals).filter((id) => approvals[id].status === "withdrawn").map(digest);
  if (priorState.withdrawnSources?.some((hash) => !withdrawnSources.includes(hash))) {
    throw new Error("Review approvals would restore a withdrawn research source");
  }

  await mkdir(output, { mode: 0o700 });
  let completed = false;
  try {
    const candidate = join(output, "pages");
    const trackedApprovals = join(output, "approvals.json");
    await writeFile(trackedApprovals, json(approvals), { mode: 0o600 });
    await run(process.execPath, ["build.mjs", "--pages", "--output", candidate], {
      cwd: directory,
      env: { ...process.env, FASTEST_RESEARCH_METADATA_APPROVALS: trackedApprovals, FASTEST_EVIDENCE_STATE: "" },
    });
    const { wiki, index: current } = await snapshot(candidate);
    const updatedSource = current.sources.find(({ id }) => id === sourceId);
    const updatedTarget = evidenceId === sourceId ? updatedSource : updatedSource?.records.find(({ id }) => id === evidenceId);
    if (action === "correct" && (!updatedTarget || JSON.stringify(updatedTarget) === JSON.stringify(target))) {
      throw new Error("Correction requires a changed, reviewed revision of the same evidence ID");
    }
    if (action === "withdraw" && updatedSource) throw new Error("Withdrawn source survived the Pages rebuild");

    const outsideCase = (sources) => sources.filter(({ id }) => id !== sourceId);
    if (JSON.stringify(outsideCase(old.sources)) !== JSON.stringify(outsideCase(current.sources))) {
      throw new Error("Evidence review also changes other published research sources");
    }
    const stagedHashes = await hashes(candidate);
    const paths = new Set(priorState.paths);
    const history = [];
    const protectedPaths = [];
    if (action === "withdraw") {
      const withdrawn = withdrawnReference(old, approvals);
      for (const path of stagedHashes.keys()) {
        if (withdrawn(await readFile(join(candidate, path.slice(1)), "utf8"))) {
          throw new Error("Withdrawn source still referenced by " + path);
        }
      }
    }
    for (const root of new Set([previous, ...archiveRoots])) {
      const { wiki: capturedWiki, index } = await snapshot(root);
      if (!containsSource(index, source)) continue;
      const earlier = await hashes(root);
      const prefix = `/research/${index.release}`;
      const items = [...earlier].filter(([path, hash]) => stagedHashes.get(path) !== hash);
      history.push({ researchRelease: index.release, artifacts: items.map(([path, before]) => ({ path, before })) });
      if (action === "withdraw") {
        paths.add(prefix + "/*");
        if (capturedWiki.catalogRelease && capturedWiki.catalogRelease !== wiki.catalogRelease) {
          paths.add(`/catalog/${capturedWiki.catalogRelease}/*`);
          paths.add(`/catalog-data/${capturedWiki.catalogRelease}/*`);
        }
        for (const path of earlier.keys()) {
          if (!stagedHashes.has(path)) for (const route of deniedRoutes(path)) paths.add(route);
        }
      } else if (!paths.has(prefix + "/*") && index.release !== current.release &&
          !index.sources.some(({ id }) => approvals[id]?.status === "withdrawn") &&
          !index.methods.some(({ url }) => approvals["youtube/" + new URL(url).searchParams.get("v")]?.status === "withdrawn")) {
        const folder = join("research", index.release);
        await cp(join(root, folder), join(candidate, folder), { recursive: true, errorOnExist: false, force: false });
        protectedPaths.push(prefix + "/*");
      }
    }

    const id = digest(json([action, evidenceId, old.release, current.release]));
    const resolutionPath = "/wiki/evidence-updates#" + id;
    const update = { id, action, research: `/research/${current.release}/library`,
      ...(action === "correct" && { source: updatedTarget.url }), ...(intake.issue && { issue: intake.issue }) };
    await writeEvidenceState(candidate, { paths: [...paths], withdrawnSources, updates: [...priorState.updates, update] });
    const oldHashes = await hashes(previous);
    const newHashes = await hashes(candidate);
    const pagesChanges = [...new Set([...oldHashes.keys(), ...newHashes.keys()])].sort().flatMap((path) => {
      const before = oldHashes.get(path) ?? null;
      const after = newHashes.get(path) ?? null;
      return before === after ? [] : [{ path, before, after }];
    });
    const benchmark = await resolveBenchmark(request.benchmark, action, sourceLocator, output);
    const changes = [...pagesChanges, ...(benchmark?.changes ?? [])];
    const earlierHashes = [...new Set([
      ...history.flatMap(({ artifacts }) => artifacts.map(({ before }) => before)),
      ...Object.values(benchmark?.earlierExports ?? {}),
    ])].sort();
    const notificationDraft = [
      `Evidence ${evidenceId} has been ${action === "withdraw" ? "withdrawn" : "corrected"} in the staged release.`,
      `Resolution: ${resolutionPath}`,
      "Compare the following SHA-256 digests with earlier exports, and replace matching copies with the current release.",
      ...earlierHashes,
    ].join("\n");
    const cachePurgePaths = new Set([...changes, ...history.flatMap(({ artifacts }) => artifacts)]
      .flatMap(({ path, before }) => before ? deniedRoutes(path) : []));
    if (benchmark) {
      cachePurgePaths.add("/api/v1/evidence?evidence_id=" + request.benchmark.evidenceId);
      for (const path of Object.keys(benchmark.earlierExports)) {
        const [, , release, file] = path.split("/");
        cachePurgePaths.add("/api/v1/evidence?release=" + release);
        cachePurgePaths.add("/releases/current/" + file);
      }
    }
    await writeFile(join(output, "review.json"), json({
      action, evidenceId, sourceId, sourceLocator, previous: { wiki: oldWiki.release, research: old.release },
      candidate: { wiki: wiki.release, research: current.release }, resolutionPath, changes, diffSha256: digest(json(changes)),
      history, historicalResearch: [...new Set(protectedPaths)].sort(),
      cachePurgePaths: [...cachePurgePaths].sort(),
      ...(benchmark && { benchmarkRelease: benchmark.release }),
      notificationDraft, receiptUpdate: receiptUpdate(intake, resolutionPath),
    }), { mode: 0o600 });
    completed = true;
  } finally {
    if (!completed) await rm(output, { recursive: true, force: true });
  }
}

try {
  const [request, previous, output, approvals, ...archives] = process.argv.slice(2);
  if (!request || !previous || !output) {
    throw new Error("Usage: node resolve-evidence.mjs REQUEST.json PREVIOUS_PAGES NEW_REVIEW_DIR [APPROVALS.json] [HISTORICAL_PAGES ...]");
  }
  await stageResolution(await readJson(request), resolve(previous), resolve(output), approvals, archives.map((path) => resolve(path)));
} catch (error) {
  console.error(error.stderr || error.message);
  process.exitCode = 1;
}
