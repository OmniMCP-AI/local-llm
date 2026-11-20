import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { researchReleaseId } from "./research-released-snapshot.mjs";

export const emptyEvidenceState = { paths: [], updates: [], withdrawnSources: [], researchPins: {} };

const escape = (text) => text.replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);
const localReleasePath = /^\/research\/v1-[a-f0-9]{16}\/library$/;
const projectIssue = /^https:\/\/github\.com\/OmniMCP-AI\/local-llm\/issues\/[1-9]\d*$/;
const safeSource = (link) => /^(?:https:\/\/[^\s<>"()]+|#wiki\/[a-z0-9-]+)$/.test(link);
export const isPublicIssue = (link) => typeof link === "string" && projectIssue.test(link);

export function validateEvidenceState(state) {
  const { paths, updates, withdrawnSources = [], researchPins = {} } = state;
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
  if (updates.some(({ id, action, research, source, sourceDigest, issue }) =>
    !/^[a-f0-9]{64}$/.test(id) || !["withdraw", "correct"].includes(action) ||
    !localReleasePath.test(research) || (source && (action !== "correct" || !safeSource(source))) ||
    (sourceDigest && (!source || !/^[a-f0-9]{64}$/.test(sourceDigest))) ||
    (issue && !isPublicIssue(issue)))) {
    throw new Error("Invalid public evidence update");
  }
  return { paths, updates, withdrawnSources, researchPins };
}

export async function writeEvidenceState(output, state = emptyEvidenceState, isWithdrawn = () => false) {
  const { paths, updates, withdrawnSources, researchPins } = validateEvidenceState(state);
  const blocked = new Set(withdrawnSources);
  const publicUpdates = updates.map(({ id, action, research, source, sourceDigest, issue }) => ({
    id, action, research, issue,
    ...(!blocked.has(sourceDigest) && !isWithdrawn(source) && { source, sourceDigest }),
  }));
  const html = publicUpdates.map(({ id, action, research, source, issue }) => `<section id="${id}">
<h2>${action === "withdraw" ? "Withdrawn evidence" : "Corrected evidence"}</h2>
<p><a href="${research}">Updated research release</a>${source ? ` · <a href="${escape(source.startsWith("#") ? "/" + source : source)}">Reviewed source</a>` : ""}${issue ? ` · <a href="${issue}">Public issue</a>` : ""}</p>
</section>`).join("\n");
  const markdown = publicUpdates.map(({ id, action, research, source, issue }) =>
    `<a id="${id}"></a>\n\n## ${action === "withdraw" ? "Withdrawn evidence" : "Corrected evidence"}\n\n` +
    `[Updated research release](${research}.md)${source ? ` · [Reviewed source](${source.startsWith("#") ? "/" + source : source})` : ""}${issue ? ` · [Public issue](${issue})` : ""}\n`).join("\n");
  await Promise.all([
    writeFile(join(output, "evidence-quarantine.json"), JSON.stringify({
      paths: [...new Set(paths)].sort(), updates: publicUpdates, researchPins, withdrawnSources: [...new Set(withdrawnSources)].sort(),
    }, null, 2) + "\n"),
    writeFile(join(output, "wiki/evidence-updates.html"), `<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evidence updates | fastest.ai</title><main><h1>Evidence updates</h1><p><a href="/wiki/">Wiki</a> · <a href="/wiki/evidence-updates.md">Markdown</a></p>
${html || "<p>No evidence updates have been published.</p>"}</main></html>
`),
    writeFile(join(output, "wiki/evidence-updates.md"), "# Evidence updates\n\n[Wiki](/wiki/index.md)\n\n" +
      (markdown || "No evidence updates have been published.\n")),
  ]);
}
