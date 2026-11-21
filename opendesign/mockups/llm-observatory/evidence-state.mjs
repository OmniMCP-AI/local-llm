import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { catalogReleasePattern } from "./catalog-paths.mjs";
import { evidenceUpdatesPath } from "./evidence-public-paths.mjs";
import { digest, readJson, researchReleaseId } from "./research-released-snapshot.mjs";

export const emptyEvidenceState = { paths: [], updates: [], withdrawnSources: [], researchPins: {}, publisherWithdrawals: [] };

const escape = (text) => text.replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);
const localReleasePath = /^\/research\/v1-[a-f0-9]{16}\/library$/;
const projectIssue = /^https:\/\/github\.com\/OmniMCP-AI\/local-llm\/issues\/[1-9]\d*$/;
const safeSource = (link) => /^(?:https:\/\/[^\s<>"()]+|#wiki\/[a-z0-9-]+)$/.test(link);
const isSha256 = (hash) => typeof hash === "string" && hash.length === 64 && /^[a-f0-9]{64}$/.test(hash);
const exportNoticesPath = evidenceUpdatesPath + ".json";
export const isPublicIssue = (link) => typeof link === "string" && projectIssue.test(link);

export async function readEvidenceState(file = process.env.FASTEST_EVIDENCE_STATE) {
  return file ? validateEvidenceState(await readJson(file)) : emptyEvidenceState;
}

export function withdrawnPublisherSource({ publisherWithdrawals }) {
  const sources = new Set(publisherWithdrawals.map(({ sourceSha256 }) => sourceSha256));
  return (source) => sources.size > 0 && typeof source === "string" && sources.has(digest(source));
}

export function validateEvidenceState(state) {
  const { paths, updates, withdrawnSources = [], researchPins = {}, publisherWithdrawals = [] } = state;
  if (!researchPins || Array.isArray(researchPins) || typeof researchPins !== "object" ||
      Object.entries(researchPins).some(([release, hash]) => !researchReleaseId.test(release) || !/^[a-f0-9]{64}$/.test(hash))) {
    throw new Error("Invalid retained research pins");
  }
  if (!Array.isArray(withdrawnSources) || withdrawnSources.some((hash) => !/^[a-f0-9]{64}$/.test(hash))) {
    throw new Error("Invalid withdrawn source digests");
  }
  if (!Array.isArray(paths) || !Array.isArray(updates) || paths.some((path) =>
    typeof path !== "string" || !/^\/[a-z0-9._/-]+(?:\*)?$/i.test(path) ||
    path.includes("//") || path.split("/").some((segment) => [".", ".."].includes(segment)) ||
    (path.includes("*") && !path.endsWith("/*")))) {
    throw new Error("Invalid evidence quarantine paths");
  }
  if (updates.some(({ id, action, research, source, sourceDigest, issue, affectedSha256 = [] }) =>
    !isSha256(id) || !["withdraw", "correct"].includes(action) ||
    !localReleasePath.test(research) || (source && (action !== "correct" || !safeSource(source))) ||
    (sourceDigest && (!source || !/^[a-f0-9]{64}$/.test(sourceDigest))) ||
    (issue && !isPublicIssue(issue)) ||
    !Array.isArray(affectedSha256) || affectedSha256.some((hash) => !isSha256(hash)))) {
    throw new Error("Invalid public evidence update");
  }
  if (!Array.isArray(publisherWithdrawals) || publisherWithdrawals.some((entry) =>
    !entry || typeof entry.sourceSha256 !== "string" || !/^[a-f0-9]{64}$/.test(entry.sourceSha256) || !isPublicIssue(entry.issue) ||
    !Array.isArray(entry.catalogReleases) || !entry.catalogReleases.length ||
    entry.catalogReleases.some((release) => typeof release !== "string" || !catalogReleasePattern.test(release))) ||
    new Set(publisherWithdrawals.map(({ sourceSha256 }) => sourceSha256)).size !== publisherWithdrawals.length) {
    throw new Error("Invalid publisher evaluation withdrawals");
  }
  const retired = publisherWithdrawals.flatMap(({ catalogReleases }) => catalogReleases.flatMap((release) =>
    [`/catalog/${release}/*`, `/catalog-data/${release}/*`]));
  return { paths: [...new Set([...paths, ...retired])], updates, withdrawnSources, researchPins,
    publisherWithdrawals: publisherWithdrawals.map(({ sourceSha256, issue, catalogReleases }) =>
      ({ sourceSha256, issue, catalogReleases: [...new Set(catalogReleases)].sort() })) };
}

export async function writeEvidenceState(output, state = emptyEvidenceState, isWithdrawn = () => false) {
  const { paths, updates, withdrawnSources, researchPins, publisherWithdrawals } = validateEvidenceState(state);
  const blocked = new Set(withdrawnSources);
  const publicUpdates = updates.map(({ id, action, research, source, sourceDigest, issue, affectedSha256 }) => ({
    id, action, research, issue,
    ...(!blocked.has(sourceDigest) && !isWithdrawn(source) && { source, sourceDigest }),
    ...(affectedSha256?.length && { affectedSha256: [...new Set(affectedSha256)].sort() }),
  }));
  const notices = publicUpdates.filter(({ affectedSha256 }) => affectedSha256).map(({ id, action, affectedSha256 }) =>
    ({ action, affectedSha256, resolution: evidenceUpdatesPath + "#" + id }));
  const html = publicUpdates.map(({ id, action, research, source, issue }) => `<section id="${id}">
<h2>${action === "withdraw" ? "Withdrawn evidence" : "Corrected evidence"}</h2>
<p><a href="${research}">Updated research release</a>${source ? ` · <a href="${escape(source.startsWith("#") ? "/" + source : source)}">Reviewed source</a>` : ""}${issue ? ` · <a href="${issue}">Public issue</a>` : ""}</p>
</section>`).concat(publisherWithdrawals.map(({ sourceSha256, issue }) => `<section id="${sourceSha256}">
<h2>Publisher evaluation withdrawn</h2>
<p><a href="/#catalog/models">Current model catalog</a> · <a href="${issue}">Public issue</a></p>
</section>`)).join("\n");
  const markdown = publicUpdates.map(({ id, action, research, source, issue }) =>
    `<a id="${id}"></a>\n\n## ${action === "withdraw" ? "Withdrawn evidence" : "Corrected evidence"}\n\n` +
    `[Updated research release](${research}.md)${source ? ` · [Reviewed source](${source.startsWith("#") ? "/" + source : source})` : ""}${issue ? ` · [Public issue](${issue})` : ""}\n`)
    .concat(publisherWithdrawals.map(({ sourceSha256, issue }) =>
      `<a id="${sourceSha256}"></a>\n\n## Publisher evaluation withdrawn\n\n[Current model catalog](/#catalog/models) · [Public issue](${issue})\n`))
    .join("\n");
  await Promise.all([
    writeFile(join(output, "evidence-quarantine.json"), JSON.stringify({
      paths: paths.slice().sort(), updates: publicUpdates, researchPins, withdrawnSources: [...new Set(withdrawnSources)].sort(),
      ...(publisherWithdrawals.length && { publisherWithdrawals }),
    }, null, 2) + "\n"),
    writeFile(join(output, exportNoticesPath), JSON.stringify({ version: 1, notices }, null, 2) + "\n"),
    writeFile(join(output, evidenceUpdatesPath + ".html"), `<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evidence updates | fastest.ai</title><main><h1>Evidence updates</h1><p><a href="/wiki/">Wiki</a> · <a href="${evidenceUpdatesPath}.md">Markdown</a></p>
<p>Compare the SHA-256 of a saved export with the <a href="${exportNoticesPath}">export notices (JSON)</a> for its resolution.</p>
${html || "<p>No evidence updates have been published.</p>"}</main></html>
`),
    writeFile(join(output, evidenceUpdatesPath + ".md"), "# Evidence updates\n\n[Wiki](/wiki/index.md)\n\n" +
      `Compare the SHA-256 of a saved export with the [export notices (JSON)](${exportNoticesPath}) for its resolution.\n\n` +
      (markdown || "No evidence updates have been published.\n")),
  ]);
}
