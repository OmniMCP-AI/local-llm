import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { createContextReview } from "./research-context.mjs";
import { digest, readJson, readResearchSnapshot } from "./research-released-snapshot.mjs";

const [pages, command, argument, predecessor] = process.argv.slice(2);
const local = (name) => new URL("wiki/" + name, import.meta.url);
const usage = "Usage: node research-context-cli.mjs CURRENT_PAGES evaluate [SPLIT.json] | evaluate-local [SPLIT.json] | suggest SOURCE_ID | promote REVIEW.json | rollback CURRENT.json PRIOR.json";

async function evaluateLocal(index, rules, knownCrossPosts, isEligible) {
  const [plan, annotations, graph] = await Promise.all([
    readJson(argument ?? local("context-calibration-local-split.json")),
    readFile(local("research-index.json")),
    readJson(local("graphify.json")),
  ]);
  const annotationIndexSha256 = digest(annotations);
  const annotatedIndex = JSON.parse(annotations);
  if (graph.graph.research_index_sha256 !== annotationIndexSha256 || annotatedIndex.taxonomyVersion !== index.taxonomyVersion) {
    throw new Error("Local annotations disagree with Graphify or the released taxonomy");
  }
  if (!Array.isArray(plan.annotatedSources)) throw new Error("Local calibration requires an annotatedSources allowlist");
  const annotated = new Map(annotatedIndex.sources.map((source) => [source.id, source]));
  const sources = new Map(index.sources.map((source) => [source.id, source]));
  for (const id of plan.annotatedSources) {
    if (!annotated.has(id)) throw new Error("Local calibration refers to an unknown annotated source");
    if (!sources.has(id)) sources.set(id, annotated.get(id));
  }
  const context = createContextReview({ ...index, sources: [...sources.values()].filter(isEligible) }, rules, knownCrossPosts);
  return {
    scope: "operator-local-annotations", annotationIndexSha256,
    ...context.evaluate(plan, { includeBreakdowns: true }),
  };
}

try {
  const evaluating = ["evaluate", "evaluate-local"].includes(command);
  if (!pages || (!evaluating && !["suggest", "promote", "rollback"].includes(command)) ||
      (!evaluating && !argument) || (command === "rollback" && !predecessor)) throw new Error(usage);
  const [snapshot, state, currentState, request, active, defaultPlan] = await Promise.all([
    readResearchSnapshot(pages),
    readJson(join(pages, "evidence-quarantine.json")),
    process.env.FASTEST_EVIDENCE_STATE ? readJson(process.env.FASTEST_EVIDENCE_STATE) : null,
    command === "promote" ? readJson(argument) : null,
    process.env.FASTEST_CONTEXT_RELEASE ? readJson(process.env.FASTEST_CONTEXT_RELEASE) : null,
    readJson(local("context-calibration-split.json")),
  ]);
  const blocked = new Set();
  for (const stateFile of [state, currentState].filter(Boolean)) {
    if (!Array.isArray(stateFile.withdrawnSources) || stateFile.withdrawnSources.some((id) => !/^[a-f0-9]{64}$/.test(id))) {
      throw new Error("Invalid withdrawn source digests");
    }
    for (const id of stateFile.withdrawnSources) blocked.add(id);
  }
  const { index } = snapshot;
  const draft = process.env.FASTEST_CONTEXT_RULES;
  if (draft && active) throw new Error("Select either a draft rules file or a reviewed context release");
  const rules = request?.rules ?? active?.rules ?? await readJson(draft ?? local("context-suggestion-rules.json"));
  const isEligible = ({ id }) => !blocked.has(digest(id));
  const context = createContextReview({ ...index, sources: index.sources.filter(isEligible) }, rules, defaultPlan.crossPosts);
  if (active && command !== "promote") context.useReviewed(active);
  const result = command === "suggest" ? { researchRelease: index.release, proposals: context.suggest(argument) }
    : command === "evaluate" ? context.evaluate(argument ? await readJson(argument) : defaultPlan)
    : command === "evaluate-local" ? await evaluateLocal(index, rules, defaultPlan.crossPosts, isEligible)
    : command === "promote" ? context.promote({ ...request, plan: request.plan ?? defaultPlan, prior: active })
    : context.rollback(await readJson(argument), await readJson(predecessor));
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
