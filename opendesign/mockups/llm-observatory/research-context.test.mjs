import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";
import { writeResearchRelease } from "./research-release-build.mjs";

const directory = fileURLToPath(new URL(".", import.meta.url));
const digest = (value) => createHash("sha256").update(value).digest("hex");
const json = async (path) => JSON.parse(await readFile(path, "utf8"));
const run = promisify(execFile);
const noteId = "youtube/09GB4LtXUok";
const forecastId = "youtube/6YMHMU_x4Rc";
const repostId = "youtube/kQKCp7PlVxY";
const chineseId = "youtube/dnk_lPZ0Y-E";
const hongKongId = "youtube/ao6B7GR8tQY";
const taiwanId = "youtube/DEPF8rAprS4";
const wallPowerSourceId = "youtube/MhZABCEOUWY";
const blogId = "together-evaluation-methods";
const frozenRulesFile = join(directory, "wiki/context-suggestion-rules-v1.json");
const plan = { heldOut: [blogId], crossPosts: [] };
const examples = [
  { source: "comparison-methods", subject: "comparison-methods", facet: "topic", tag: "retrieval", expected: true },
  { source: "comparison-methods", subject: "comparison-methods", facet: "topic", tag: "coding", expected: false },
];

async function released(t, fixtureIds = []) {
  const root = await mkdtemp(join(tmpdir(), "fastest-context-test-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const seed = await json(join(directory, "wiki/research-index.json"));
  const approvals = Object.fromEntries(fixtureIds.map((id) => {
    const source = seed.sources.find((item) => item.id === id);
    return [id, { status: "approved-metadata", review: "TEST-ONLY", sha256: digest(JSON.stringify(source)) }];
  }));
  const index = await writeResearchRelease(directory, root, approvals);
  await mkdir(join(root, "wiki"));
  await writeFile(join(root, "wiki/manifest.json"), JSON.stringify({ researchRelease: index.release }));
  await writeFile(join(root, "evidence-quarantine.json"), JSON.stringify({ withdrawnSources: [] }));
  return { root, index };
}

test("suggestions preserve the locator and scope of the annotated note, forecast, and article", async (t) => {
  const { createContextReview } = await import("./research-context.mjs");
  const { index } = await released(t, [noteId, forecastId]);
  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const context = createContextReview(index, rules);
  const slots = context.suggest(noteId);
  const slot = (id, facet) => slots.find((item) => item.subject === id && item.facet === facet);
  const tags = ({ matches }) => matches.map(({ tag }) => tag);
  assert.ok(tags(slot("V024-P009", "task")).includes("coding"));
  assert.ok(tags(slot("V024-P007", "task")).includes("retrieval"));
  assert.deepEqual(tags(slot("V024-P001", "task")), []);
  assert.deepEqual(tags(slot("V024-P001", "dimension")), ["prefill"]);
  assert.match(slot("V024-P009", "task").locator, /09GB4LtXUok&t=327s$/);
  const projections = ["V021-P001", "V021-P011", "V021-P012", "V021-P015", "V021-P017", "V021-P035"];
  const forecast = context.suggest(forecastId).filter(({ subject, facet }) =>
    facet === "dimension" && projections.includes(subject));
  assert.deepEqual(forecast.map(({ subject }) => subject), projections);
  for (const proposal of forecast) assert.deepEqual(tags(proposal), proposal.subject === "V021-P011" ? [] : ["projection"]);
  assert.equal(forecast.find(({ subject }) => subject === "V021-P012").evidence, "explicit forecast,notmeasured");
  const blog = context.suggest(blogId);
  assert.deepEqual(blog.map(({ facet }) => facet), ["topic"]);
  assert.ok(tags(blog[0]).includes("coding"));
});

test("phase-qualified wall power is an energy dimension at the source record", async (t) => {
  const { createContextReview } = await import("./research-context.mjs");
  const { index } = await released(t, [wallPowerSourceId]);
  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const slots = createContextReview(index, rules).suggest(wallPowerSourceId);
  const dimension = (id) => slots.find(({ subject, facet }) => subject === id && facet === "dimension");

  const cachedPrefillPower = dimension("V045-P010");
  assert.deepEqual(cachedPrefillPower.matches, [{ tag: "energy", field: "metric", term: "wall power" }]);
  assert.match(cachedPrefillPower.locator, /MhZABCEOUWY&t=479s$/);
  assert.deepEqual(dimension("V045-P009").matches.map(({ tag }) => tag), ["energy"]);
  assert.deepEqual(dimension("V045-P005").matches.map(({ tag }) => tag), ["prefill"]);
  assert.deepEqual(dimension("V045-P011").matches, []);
});

test("regional video suggestions use scoped phrases from the annotated metadata", async (t) => {
  const { createContextReview } = await import("./research-context.mjs");
  const { index } = await released(t, [hongKongId, taiwanId]);
  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const context = createContextReview(index, rules);
  const hongKong = context.suggest(hongKongId);
  const task = (id) => hongKong.find(({ subject, facet }) => subject === id && facet === "task");

  assert.deepEqual(hongKong[0].matches, [{ tag: "image-generation", field: "context", term: "image generation" }]);
  assert.deepEqual(task("V014-P002").matches, [{ tag: "fine-tuning", field: "metric", term: "fine-tuning" }]);
  assert.match(task("V014-P002").locator, /ao6B7GR8tQY&t=35s$/);
  assert.deepEqual(task("V014-P003").matches, []);
  assert.deepEqual(hongKong.find(({ subject, facet }) => subject === "V014-P003" && facet === "dimension").matches, []);

  const taiwan = context.suggest(taiwanId);
  assert.deepEqual(taiwan[0].matches, [{ tag: "runtime-tuning", field: "context", term: "draft-assisted generation" }]);
  assert.ok(taiwan.filter(({ facet }) => facet === "task").every(({ matches }) => matches.length === 0));
  assert.deepEqual(taiwan.find(({ subject, facet }) => subject === "V042-P003" && facet === "dimension").matches, []);
});

test("calibration holds out whole sources and cross-post families and reports gaps and false transfers", async (t) => {
  const { createContextReview } = await import("./research-context.mjs");
  const { index } = await released(t, [noteId]);
  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const note = index.sources.find(({ id }) => id === noteId);
  const crossPost = { id: "translated-forum", format: "post", language: "zh-TW", publisher: "Another publisher",
    records: [], url: "https://example.org/thread#original", title: "模型评估", context: "本地部署",
    topics: { "model-evaluation": "https://example.org/thread#original" } };
  const changedRules = { ...rules, task: { ...rules.task, coding: [...rules.task.coding, "prefill"] } };
  const context = createContextReview({ ...index, sources: [...index.sources, crossPost] }, changedRules);
  const crossPosts = [[noteId, crossPost.id]];
  assert.throws(() => context.evaluate({ heldOut: [noteId], crossPosts }), /split.*cross-post/i);
  const report = context.evaluate({ heldOut: [noteId, crossPost.id, blogId], crossPosts });
  assert.deepEqual(report.heldOut, [blogId, crossPost.id, noteId]);
  assert.equal(report.coverage.languages.zh.heldOut, 1);
  assert.equal(report.coverage.languages.es.heldOut, 0);
  assert.equal(report.coverage.formats.video.heldOut, 1);
  assert.equal(report.facets.task.subjects, note.records.length);
  assert.ok(report.facets.task.precision < 1);
  assert.ok(report.facets.task.recall > 0);
  assert.ok(report.facets.task.abstentions > 0);
  assert.equal(report.facets.task.wrongScope.articleToCase, 4);
  assert.equal(report.facets.dimension.wrongScope.forecastAsMeasurement, 0);
  assert.ok(report.missingCoverage.languages.includes("es"));
  assert.equal(report.automaticPromotion, false);
});

test("only explicit source-bound decisions enter a reviewed release and rollback checks the predecessor", async (t) => {
  const { createContextReview } = await import("./research-context.mjs");
  const { index } = await released(t);
  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const current = createContextReview(index, rules);
  const slot = current.suggest(blogId)[0];
  const release1 = current.promote({
    review: "editor/review-1", plan, examples, decisions: [
      { proposal: slot.id, action: "accept", review: "editor/decision-1" },
    ],
  });
  assert.deepEqual(release1.assignments[0].tags, ["coding", "model-evaluation"]);
  assert.equal(release1.assignments[0].locator, slot.locator);

  const next = createContextReview(index, { ...rules, version: rules.version + 1 });
  const nextSlot = next.suggest(blogId)[0];
  assert.throws(() => next.promote({ review: "editor/review-2", plan, examples,
    prior: release1, decisions: [{ proposal: slot.id, action: "accept", review: "stale" }] }), /proposal/i);
  const release2 = next.promote({
    review: "editor/review-2", plan, examples, prior: release1, decisions: [
      { proposal: nextSlot.id, action: "correct", tags: ["evidence-research"], review: "editor/decision-2" },
    ],
  });
  assert.deepEqual(release2.assignments[0].tags, ["evidence-research"]);
  const release3 = next.promote({
    review: "editor/review-3", plan, examples, prior: release2, decisions: [
      { proposal: nextSlot.id, action: "unclassified", review: "editor/decision-3" },
    ],
  });
  assert.deepEqual(release3.assignments[0].tags, []);
  assert.throws(() => next.rollback(release3, release1), /predecessor/i);
  assert.equal(next.rollback(release2, release1).id, release1.id);
  assert.equal(next.rollback(release2, release1).rules.version, rules.version);

  const changed = createContextReview({ ...index, sources: index.sources.filter(({ id }) => id !== blogId) }, rules);
  assert.throws(() => changed.rollback(release2, release1), /unavailable|revision/);
  assert.equal(index.sources.find(({ id }) => id === blogId).topics.coding, slot.locator);
});

test("the editor CLI rejects tampered snapshots and screens out current withdrawals", async (t) => {
  const { root, index } = await released(t, [noteId]);
  const runCLI = async (...args) => JSON.parse((await run(process.execPath,
    ["research-context-cli.mjs", root, ...args], { cwd: directory })).stdout);
  const { proposals } = await runCLI("suggest", noteId);
  assert.ok(proposals.some(({ subject }) => subject === "V024-P001"));
  await writeFile(join(root, "evidence-quarantine.json"), JSON.stringify({ withdrawnSources: [digest(noteId)] }));
  await assert.rejects(runCLI("suggest", noteId), /not eligible/);
  const file = join(root, "research", index.release, "index.json");
  await writeFile(file, JSON.stringify(index));
  await assert.rejects(runCLI("suggest", blogId), /manifest disagree/);
});

test("the CLI holds out the annotated Chinese source and both reviewed cross-posts", async (t) => {
  const { root } = await released(t, [forecastId, repostId, chineseId]);
  const split = join(root, "split.json");
  const execute = async () => JSON.parse((await run(process.execPath,
    ["research-context-cli.mjs", root, "evaluate", split], { cwd: directory })).stdout);
  await writeFile(split, JSON.stringify({ heldOut: [forecastId, chineseId], crossPosts: [] }));
  await assert.rejects(execute(), /split.*cross-post/i);
  await writeFile(split, JSON.stringify({ heldOut: [forecastId, repostId, chineseId], crossPosts: [] }));
  const report = await execute();
  assert.equal(report.coverage.languages.zh.heldOut, 1);
  assert.equal(report.coverage.formats.video.heldOut, 3);
  assert.equal(report.heldOutFamilies, 2);
  assert.ok(report.facets.dimension.recall > 0);
});

test("the operator replay scores local annotations without adding them to the released corpus", async (t) => {
  const { root, index } = await released(t);
  const liveState = join(root, "live-state.json");
  await writeFile(liveState, JSON.stringify({ withdrawnSources: [] }));
  const execute = async (...args) => JSON.parse((await run(process.execPath,
    ["research-context-cli.mjs", root, ...args],
    { cwd: directory, env: { ...process.env, FASTEST_EVIDENCE_STATE: liveState } },
  )).stdout);
  const publicReport = await execute("evaluate");
  assert.equal(publicReport.facets.task.subjects, 0);
  await assert.rejects(execute("suggest", noteId), /not eligible/);
  await assert.rejects(execute("suggest", hongKongId), /not eligible/);
  await assert.rejects(execute("suggest", taiwanId), /not eligible/);

  const report = await execute("evaluate-local");
  assert.equal(report.scope, "operator-local-annotations");
  assert.equal(report.researchRelease, index.release);
  assert.match(report.annotationIndexSha256, /^[a-f0-9]{64}$/);
  assert.ok(report.heldOut.includes(hongKongId));
  assert.ok(!report.heldOut.includes(taiwanId));
  assert.equal(report.heldOutFamilies, 9);
  assert.equal(report.unavailableHeldOut, 0);
  assert.equal(report.development, 3);
  assert.deepEqual(report.missingCoverage.formats, []);
  assert.deepEqual(report.coverage.languages.en, { heldOut: 14, development: 2 });
  assert.deepEqual(report.coverage.languages.zh, { heldOut: 3, development: 1 });
  assert.deepEqual(report.coverage.languageTags["zh-HK"], { heldOut: 1, development: 0 });
  assert.deepEqual(report.coverage.languageTags["zh-Hant"], { heldOut: 1, development: 0 });
  assert.deepEqual(report.coverage.languageTags["zh-TW"], { heldOut: 0, development: 1 });
  assert.deepEqual(report.coverage.formats.video, { heldOut: 6, development: 3 });
  assert.equal(report.facets.task.subjects, 108);
  assert.equal(report.facets.task.wrongScope.articleToCase, 0);
  assert.equal(report.facets.dimension.wrongScope.forecastAsMeasurement, 0);
  assert.equal(report.facetsByLanguage.zh.topic.recall, 1 / 9);
  assert.equal(report.facetsByLanguage.zh.task.abstentions, 28);
  assert.equal(report.facetsByLanguage.zh.dimension.subjects, 29);
  const hongKong = report.facetsByLanguageTag["zh-HK"];
  assert.deepEqual(
    ["topic", "task", "dimension"].map((facet) => {
      const { tp, fp, fn, abstentions } = hongKong[facet];
      return [tp, fp, fn, abstentions];
    }),
    [[1, 0, 2, 0], [1, 0, 0, 4], [1, 0, 4, 4]],
  );
  assert.equal(hongKong.topic.precision, 1);
  assert.equal(hongKong.task.precision, 1);
  assert.equal(hongKong.dimension.recall, 1 / 5);
  assert.equal(hongKong.task.wrongScope.articleToCase, 0);
  assert.equal(report.facetsByFormat.blog.topic.tp, 2);
  assert.equal(report.facetsByFormat.blog.task.subjects, 0);
  assert.equal(report.facetsByFormat.video.dimension.subjects, 108);
  assert.equal(report.automaticPromotion, false);

  await writeFile(liveState, JSON.stringify({ withdrawnSources: [digest(chineseId), digest(hongKongId)] }));
  const afterWithdrawal = await execute("evaluate-local");
  assert.equal(afterWithdrawal.unavailableHeldOut, 2);
  assert.ok(!afterWithdrawal.heldOut.includes(hongKongId));
  assert.equal(afterWithdrawal.coverage.languages.zh.heldOut, 1);
  assert.equal(afterWithdrawal.facetsByLanguage.zh.dimension.subjects, 13);
  assert.ok(!Object.hasOwn(afterWithdrawal.facetsByLanguageTag, "zh-HK"));
});

test("the frozen-rules Taiwan replay has its own denominator", async (t) => {
  const { root } = await released(t);
  const report = JSON.parse((await run(process.execPath, [
    "research-context-cli.mjs", root, "evaluate-local", "wiki/context-calibration-zh-tw-regression-split.json",
  ], { cwd: directory, env: { ...process.env, FASTEST_CONTEXT_RULES: frozenRulesFile } })).stdout);
  assert.deepEqual(report.heldOut, [taiwanId]);
  assert.equal(report.rulesVersion, 1);
  assert.equal(report.ruleDigest, "2940be1a7b631482da34a22f35044f7f6a88a99afe43258a17c628cf9471e037");
  assert.equal(report.heldOutFamilies, 1);
  const { topic, task, dimension } = report.facetsByLanguageTag["zh-TW"];
  assert.deepEqual([topic.subjects, topic.fn, topic.abstentions], [1, 2, 1]);
  assert.deepEqual([task.subjects, task.recall, task.abstentions], [3, null, 3]);
  assert.deepEqual([dimension.subjects, dimension.tp, dimension.fp, dimension.fn, dimension.abstentions], [3, 2, 0, 1, 1]);
  assert.equal(report.automaticPromotion, false);
});

test("a reviewed vocabulary rollback restores the prior suggestions through the CLI", async (t) => {
  const { root, index } = await released(t, [wallPowerSourceId]);
  const file = (name) => join(root, name + ".json");
  const put = (name, data) => writeFile(file(name), JSON.stringify(data));
  const execute = async (active, ...args) => JSON.parse((await run(process.execPath,
    ["research-context-cli.mjs", root, ...args],
    { cwd: directory, env: { ...process.env, FASTEST_CONTEXT_RELEASE: active ? file(active) : "" } },
  )).stdout);
  const { createContextReview } = await import("./research-context.mjs");
  const oldRules = await json(frozenRulesFile);
  const frozen = createContextReview(index, oldRules);
  const wallPower = (proposals) => proposals.find(({ subject, facet }) => subject === "V045-P010" && facet === "dimension");
  const original = wallPower(frozen.suggest(wallPowerSourceId));
  assert.deepEqual(original.matches.map(({ tag }) => tag), ["prefill"]);
  await put("first-request", { plan, examples, rules: oldRules, review: "editor/release-1",
    decisions: [{ proposal: original.id, action: "unclassified", review: "editor/decision-1" }] });
  const first = await execute(null, "promote", file("first-request"));
  await put("first", first);
  assert.deepEqual(wallPower((await execute("first", "suggest", wallPowerSourceId)).proposals), original);

  const rules = await json(join(directory, "wiki/context-suggestion-rules.json"));
  const candidate = wallPower((await execute(null, "suggest", wallPowerSourceId)).proposals);
  await put("next-request", { plan, examples, rules, review: "editor/release-2",
    decisions: [{ proposal: candidate.id, action: "accept", review: "editor/decision-2" }] });
  const second = await execute("first", "promote", file("next-request"));
  await put("second", second);
  assert.deepEqual(second.assignments[0].tags, ["energy"]);
  const active = wallPower((await execute("second", "suggest", wallPowerSourceId)).proposals);
  assert.deepEqual(active, candidate);

  const prior = await execute("second", "rollback", file("second"), file("first"));
  await put("rolled-back", prior);
  assert.deepEqual(prior.assignments[0].tags, []);
  assert.deepEqual(wallPower((await execute("rolled-back", "suggest", wallPowerSourceId)).proposals), original);
});
