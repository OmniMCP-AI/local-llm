import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const evaluatorRevision = "4f82ca83fd799880119172ee55f11e745c83c1f0";
const annotationRevision = "c8e87f8776b3c75f71b0f3db4d2d7a36e5a707d9";
const repo = new URL("../../", import.meta.url);
const observatory = "opendesign/mockups/llm-observatory/";
const fromGit = (commit, path) => execFileSync("git", ["show", commit + ":" + path], { cwd: fileURLToPath(repo) });
const frozen = (path) => fromGit(evaluatorRevision, observatory + path);

for (const path of ["research-context.mjs", "research-released-snapshot.mjs"]) {
  if (!readFileSync(new URL(observatory + path, repo)).equals(frozen(path))) {
    throw new Error("Replay requires the evaluator modules from " + evaluatorRevision + ": " + path);
  }
}

const { createContextReview } = await import(new URL(observatory + "research-context.mjs", repo));
const annotationBytes = fromGit(annotationRevision, "docs/context-holdout/annotations.json");
const sources = JSON.parse(annotationBytes).map(({ annotation, records, ...source }) => ({
  ...source,
  topics: annotation.topics,
  records: records.map(({ annotation: labels, ...record }) => ({ ...record, ...labels })),
}));
const { taxonomyVersion } = JSON.parse(frozen("wiki/research-index.json"));
const vocabulary = JSON.parse(frozen("wiki/context-vocabulary.json"));
const plan = { heldOut: sources.map(({ id }) => id), crossPosts: [] };
const index = { taxonomyVersion, vocabulary, sources, release: null };

const versions = ["context-suggestion-rules-v1.json", "context-suggestion-rules.json"].map((name) => {
  const review = createContextReview(index, JSON.parse(frozen("wiki/" + name)));
  const calibration = review.evaluate(plan, { includeBreakdowns: true });
  const predictions = sources.flatMap((source) => {
    const expected = new Map(source.records.map(({ id, dimension, topics }) => [id, { dimension: [dimension], task: topics }]));
    expected.set(source.id, { topic: Object.keys(source.topics) });
    return review.suggest(source.id).map((proposal) => ({
      ...proposal,
      expected: expected.get(proposal.subject)[proposal.facet],
    }));
  });
  return { calibration, predictions };
});

const annotationSha256 = createHash("sha256").update(annotationBytes).digest("hex");
console.log(JSON.stringify({ scope: "operator-only-holdout", evaluatorRevision, annotationRevision, annotationSha256, versions }, null, 2));
