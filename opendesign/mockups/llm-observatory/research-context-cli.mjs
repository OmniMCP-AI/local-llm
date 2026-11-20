import { join } from "node:path";
import { createContextReview } from "./research-context.mjs";
import { digest, readJson, readResearchSnapshot } from "./research-released-snapshot.mjs";

const [pages, command, argument, predecessor] = process.argv.slice(2);
const local = (name) => new URL("wiki/" + name, import.meta.url);
const usage = "Usage: node research-context-cli.mjs CURRENT_PAGES evaluate [SPLIT.json] | suggest SOURCE_ID | promote REVIEW.json | rollback CURRENT.json PRIOR.json";

try {
  if (!pages || !["evaluate", "suggest", "promote", "rollback"].includes(command) ||
      (command !== "evaluate" && !argument) || (command === "rollback" && !predecessor)) throw new Error(usage);
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
  const eligible = index.sources.filter(({ id }) => !blocked.has(digest(id)));
  const context = createContextReview({ ...index, sources: eligible }, rules, defaultPlan.crossPosts);
  if (active && command !== "promote") context.useReviewed(active);
  const result = command === "suggest" ? { researchRelease: index.release, proposals: context.suggest(argument) }
    : command === "evaluate" ? context.evaluate(argument ? await readJson(argument) : defaultPlan)
    : command === "promote" ? context.promote({ ...request, plan: request.plan ?? defaultPlan, prior: active })
    : context.rollback(await readJson(argument), await readJson(predecessor));
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
