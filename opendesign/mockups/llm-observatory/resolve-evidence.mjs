import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { emptyEvidenceState, isPublicIssue, writeEvidenceState } from "./evidence-state.mjs";
import { feedbackId } from "./feedback-policy.mjs";

const directory = fileURLToPath(new URL(".", import.meta.url));
const run = promisify(execFile);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const json = (value) => JSON.stringify(value, null, 2) + "\n";
const readJson = async (name) => JSON.parse(await readFile(name, "utf8"));
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

async function snapshot(root, release) {
  const wiki = await readJson(join(root, "wiki/manifest.json"));
  const pin = release ?? wiki.researchRelease;
  if (!/^v1-[a-f0-9]{16}$/.test(pin)) throw new Error("Invalid research release");
  const index = await readJson(join(root, "research", pin, "index.json"));
  if (index.release !== pin) throw new Error("Research release and wiki manifest disagree");
  return { wiki, index };
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

    const paths = new Set(priorState.paths);
    const history = [];
    if (action === "withdraw") {
      for (const root of [previous, ...archiveRoots]) {
        const { wiki: capturedWiki, index } = await snapshot(root);
        if (!index.sources.some(({ id }) => id === sourceId)) continue;
        const earlier = await hashes(root);
        const staged = await hashes(candidate);
        history.push({ researchRelease: index.release, artifacts: [...earlier].filter(([path, hash]) => staged.get(path) !== hash) });
        paths.add(`/research/${index.release}/*`);
        if (capturedWiki.catalogRelease && capturedWiki.catalogRelease !== wiki.catalogRelease) {
          paths.add(`/catalog/${capturedWiki.catalogRelease}/*`);
          paths.add(`/catalog-data/${capturedWiki.catalogRelease}/*`);
        }
        for (const path of earlier.keys()) {
          if (!staged.has(path)) for (const route of deniedRoutes(path)) paths.add(route);
        }
      }
    }

    const id = digest(json([action, evidenceId, old.release, current.release]));
    const resolutionPath = "/wiki/evidence-updates#" + id;
    const update = { id, action, research: `/research/${current.release}/library`,
      ...(action === "correct" && { source: updatedTarget.url }), ...(intake.issue && { issue: intake.issue }) };
    await writeEvidenceState(candidate, { paths: [...paths], updates: [...priorState.updates, update] });
    const oldHashes = await hashes(previous);
    const newHashes = await hashes(candidate);
    const changes = [...new Set([...oldHashes.keys(), ...newHashes.keys()])].sort().flatMap((path) => {
      const before = oldHashes.get(path) ?? null;
      const after = newHashes.get(path) ?? null;
      return before === after ? [] : [{ path, before, after }];
    });
    const earlierHashes = [...new Set(history.flatMap(({ artifacts }) => artifacts.map(([, hash]) => hash)))].sort();
    const notificationDraft = [
      `Evidence ${evidenceId} has been ${action === "withdraw" ? "withdrawn" : "corrected"} in the staged release.`,
      `Resolution: ${resolutionPath}`,
      "Compare the following SHA-256 digests with earlier exports, and replace matching copies with the current release.",
      ...earlierHashes,
    ].join("\n");
    await writeFile(join(output, "review.json"), json({
      action, evidenceId, sourceId, sourceLocator, previous: { wiki: oldWiki.release, research: old.release },
      candidate: { wiki: wiki.release, research: current.release }, resolutionPath, changes, diffSha256: digest(json(changes)),
      history, notificationDraft, receiptUpdate: receiptUpdate(intake, resolutionPath),
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
