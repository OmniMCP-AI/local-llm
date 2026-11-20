import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const command = fileURLToPath(new URL("./decision-cases.mjs", import.meta.url));

function run(input) {
  return spawnSync(process.execPath, [command], { input, encoding: "utf8" });
}

const syntheticCard = {
  task: "Draft five generic product descriptions per batch",
  currentHardwareOrAlternative: "Laptop with 16 GB RAM",
  budget: "Up to CNY 500 per month",
  deadline: "Within two weeks",
  privacyConstraints: "Catalog descriptions must stay local until published",
  unresolved: "Can the current laptop meet the batch time target?",
  baselineDecision: "keep",
  successCriterion: "Five acceptable descriptions in under ten minutes",
};

const syntheticInterview = {
  caseId: "case-001",
  consent: "granted",
  redactionReviewed: true,
  card: syntheticCard,
};

test("exports only reviewed decision fields from a consented interview", () => {
  const result = run(JSON.stringify({
    mode: "synthetic",
    interviews: [{
      ...syntheticInterview,
      privateNotes: "TEST-RAW-NOTES",
      card: { ...syntheticCard, contact: "TEST-CONTACT" },
    }],
  }));

  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout).caseCards, [
    { caseId: "case-001", ...syntheticCard },
  ]);
});

test("only complete, reviewed cards with granted consent enter the handoff", () => {
  const result = run(JSON.stringify({
    mode: "synthetic",
    interviews: [
      { ...syntheticInterview, caseId: "case-001", consent: "withdrawn" },
      { ...syntheticInterview, caseId: "case-002", redactionReviewed: false },
      { ...syntheticInterview, caseId: "case-003", card: { ...syntheticCard, budget: " " } },
      { ...syntheticInterview, caseId: "case-004", card: { ...syntheticCard, baselineDecision: "maybe" } },
      { ...syntheticInterview, caseId: "case-005", card: { ...syntheticCard, alternative: "Metered cloud API" } },
    ],
  }));

  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.deepEqual(report.caseCards, [
    { caseId: "case-005", ...syntheticCard, alternative: "Metered cloud API" },
  ]);
  assert.deepEqual(report.heldCases, [
    { caseId: "case-001", missing: ["consent"] },
    { caseId: "case-002", missing: ["redactionReviewed"] },
    { caseId: "case-003", missing: ["budget"] },
    { caseId: "case-004", missing: ["baselineDecision"] },
  ]);
});

test("a synthetic rehearsal leaves the actual recruitment and case gaps intact", () => {
  const result = run(JSON.stringify({
    mode: "synthetic",
    interviews: [syntheticInterview],
  }));

  assert.equal(result.status, 0, result.stderr);
  const { mode, review } = JSON.parse(result.stdout);
  assert.equal(mode, "synthetic");
  assert.deepEqual(review, {
    interviews: { actual: 0, synthetic: 1, targetMinimum: 10, targetMaximum: 12, remainingToMinimum: 10 },
    cases: { actual: 0, synthetic: 1, target: 5, remainingToTarget: 5 },
  });
});

test("invalid or duplicate case IDs stop review without echoing input", () => {
  const invalid = run(JSON.stringify({
    mode: "synthetic",
    interviews: [{ ...syntheticInterview, caseId: "TEST-PRIVATE-ID" }],
  }));
  const duplicate = run(JSON.stringify({
    mode: "synthetic",
    interviews: [syntheticInterview, syntheticInterview],
  }));

  assert.equal(invalid.status, 1);
  assert.equal(invalid.stdout, "");
  assert.match(invalid.stderr, /Interview 1 needs a case ID in the format case-001/);
  assert.doesNotMatch(invalid.stderr, /TEST-PRIVATE-ID/);
  assert.equal(duplicate.status, 1);
  assert.equal(duplicate.stdout, "");
  assert.match(duplicate.stderr, /Interview 2 has a duplicate case ID/);
});
