import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const command = name => fileURLToPath(new URL(name, import.meta.url));

function run(input, name = "./buyer-pilot.mjs") {
  return spawnSync(process.execPath, [command(name)], {
    input: input === undefined ? "" : JSON.stringify(input),
    encoding: "utf8",
  });
}

test("empty stdin reports missing actual observations and unevaluated gates", () => {
  const result = run();
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.actual.status, "missing");
  assert.deepEqual(report.actual.participants, { observed: 0, target: 8, remaining: 8 });
  assert.deepEqual(report.actual.gates, {
    supportedChoiceWithinTenMinutes: { observed: 0, target: 6, met: null },
    specificUncertaintyResolved: { observed: 0, target: 5, met: null },
    broughtFollowUp: { observed: 0, target: 3, met: null },
  });
  assert.equal(report.rehearsal, undefined);
});

function fictionalPilot() {
  const intake = run({
    mode: "synthetic",
    interviews: [{
      caseId: "case-001",
      consent: "granted",
      redactionReviewed: true,
      card: {
        task: "Draft generic product descriptions",
        currentHardwareOrAlternative: "Manual drafting",
        budget: "CNY 400 per month",
        deadline: "One week",
        privacyConstraints: "Unpublished catalog data stays local",
        unresolved: "Can the local runner meet the time limit?",
        baselineDecision: "keep",
        successCriterion: "The comparison shows timing for the required workload.",
      },
    }],
  }, "./decision-cases.mjs");
  assert.equal(intake.status, 0, intake.stderr);
  return {
    mode: "synthetic",
    caseIntake: JSON.parse(intake.stdout),
    observations: Array.from({ length: 8 }, (_, index) => ({
      participantId: `participant-00${index + 1}`,
      caseId: "case-001",
      consent: "granted",
      redactionReviewed: true,
      currentAlternative: "Manual drafting",
      baselineDecision: "keep",
      finalDecision: index === 0 ? "upgrade" : "keep",
      elapsedSeconds: index === 6 ? 601 : 600,
      explainedChoice: true,
      citedEvidence: index === 7 ? [] : ["Fictional comparison timing row"],
      resolvedUncertainty: index < 5 ? "The local runner meets the time limit" : null,
      unresolvedUncertainty: "Capacity at twice the usual batch volume",
      followUpCase: index < 3 ? "Choose a setup for the larger batch" : null,
      willingnessToPay: index < 2 ? "yes" : "not_asked",
      privateNotes: "TEST-PRIVATE-NOTES",
    })),
  };
}

test("eight fictional participants hit the thresholds only in the rehearsal report", () => {
  const result = run(fictionalPilot());
  assert.equal(result.status, 0, result.stderr);
  const { actual, rehearsal } = JSON.parse(result.stdout);
  assert.equal(actual.status, "missing");
  assert.equal(actual.participants.observed, 0);
  assert.equal(actual.gates.supportedChoiceWithinTenMinutes.met, null);
  assert.equal(rehearsal.status, "met");
  assert.deepEqual(rehearsal.gates, {
    supportedChoiceWithinTenMinutes: { observed: 6, target: 6, met: true },
    specificUncertaintyResolved: { observed: 5, target: 5, met: true },
    broughtFollowUp: { observed: 3, target: 3, met: true },
  });
  assert.deepEqual(rehearsal.observations[0], {
    participantId: "participant-001",
    caseId: "case-001",
    currentAlternative: "Manual drafting",
    baselineDecision: "keep",
    finalDecision: "upgrade",
    decisionChanged: true,
    elapsedSeconds: 600,
    explainedChoice: true,
    citedEvidence: ["Fictional comparison timing row"],
    resolvedUncertainty: "The local runner meets the time limit",
    unresolvedUncertainty: "Capacity at twice the usual batch volume",
    followUpCase: "Choose a setup for the larger batch",
  });
  assert.equal(rehearsal.observations[1].decisionChanged, false);
  assert.deepEqual(rehearsal.willingnessToPay.counts, { yes: 2, no: 0, undecided: 0, not_asked: 6, unrecorded: 0 });
  assert.deepEqual(rehearsal.willingnessToPay.responses[0], { participantId: "participant-001", response: "yes" });
  assert.doesNotMatch(result.stdout, /TEST-PRIVATE-NOTES/);
});

test("a short cohort with enough positive results has no gate outcome", () => {
  const pilot = fictionalPilot();
  pilot.observations.pop();
  const result = run(pilot);
  assert.equal(result.status, 0, result.stderr);
  const { rehearsal } = JSON.parse(result.stdout);
  assert.equal(rehearsal.status, "incomplete");
  assert.deepEqual(rehearsal.participants, { observed: 7, target: 8, remaining: 1 });
  assert.deepEqual(Object.values(rehearsal.gates).map(gate => gate.met), [null, null, null]);
});

test("a complete cohort can miss a gate despite positive willingness to pay", () => {
  const pilot = fictionalPilot();
  pilot.observations.forEach(observation => { observation.willingnessToPay = "yes"; });
  pilot.observations[0].elapsedSeconds = 601;
  const result = run(pilot);
  assert.equal(result.status, 0, result.stderr);
  const { rehearsal } = JSON.parse(result.stdout);
  assert.equal(rehearsal.status, "missed");
  assert.deepEqual(rehearsal.gates.supportedChoiceWithinTenMinutes, { observed: 5, target: 6, met: false });
  assert.equal(rehearsal.willingnessToPay.counts.yes, 8);
});

test("withdrawn, unreviewed, unapproved and incomplete observations are held without their contents", () => {
  const pilot = fictionalPilot();
  pilot.observations[0].consent = "withdrawn";
  pilot.observations[0].currentAlternative = "TEST-WITHDRAWN-ALTERNATIVE";
  pilot.observations[1].redactionReviewed = false;
  pilot.observations[1].citedEvidence = ["TEST-UNREVIEWED-EVIDENCE"];
  pilot.observations[2].caseId = "case-002";
  pilot.observations[3].resolvedUncertainty = " ";
  const result = run(pilot);
  assert.equal(result.status, 0, result.stderr);
  const { rehearsal } = JSON.parse(result.stdout);
  assert.equal(rehearsal.participants.observed, 4);
  assert.deepEqual(rehearsal.heldObservations, [
    { participantId: "participant-001", missing: ["consent"] },
    { participantId: "participant-002", missing: ["redactionReviewed"] },
    { participantId: "participant-003", missing: ["caseId"] },
    { participantId: "participant-004", missing: ["resolvedUncertainty"] },
  ]);
  assert.equal(rehearsal.willingnessToPay.responses.length, 4);
  assert.doesNotMatch(result.stdout, /TEST-|case-002/);
});

test("operator errors exit without reporting a cohort or echoing input", () => {
  const pilot = fictionalPilot();
  const cases = [
    { input: { ...pilot, mode: "actual" }, error: /handoff.*same mode/i },
    { input: { ...pilot, caseIntake: undefined }, error: /handoff/i },
    { input: { ...pilot, observations: [pilot.observations[0], pilot.observations[0]] }, error: /duplicate participant/i },
    { input: { ...pilot, observations: [{ ...pilot.observations[0], participantId: "TEST-PRIVATE-ID" }] }, error: /participant ID/i },
    { input: { ...pilot, observations: [...pilot.observations, { ...pilot.observations[0], participantId: "participant-009" }] }, error: /eight/i },
  ];
  for (const { input, error } of cases) {
    const result = run(input);
    assert.equal(result.status, 1);
    assert.equal(result.stdout, "");
    assert.match(result.stderr, error);
    assert.doesNotMatch(result.stderr, /TEST-/);
  }
  const malformed = spawnSync(process.execPath, [command("./buyer-pilot.mjs")], {
    input: "{TEST-MALFORMED-PRIVATE-INPUT}", encoding: "utf8",
  });
  assert.equal(malformed.status, 1);
  assert.equal(malformed.stdout, "");
  assert.doesNotMatch(malformed.stderr, /TEST-/);
});


test("missing willingness-to-pay answers stay separate from decision eligibility", () => {
  const pilot = fictionalPilot();
  delete pilot.observations[0].willingnessToPay;
  pilot.observations[1].willingnessToPay = "TEST-INVALID-WTP";
  const result = run(pilot);
  assert.equal(result.status, 0, result.stderr);
  const { rehearsal } = JSON.parse(result.stdout);
  assert.equal(rehearsal.status, "met");
  assert.equal(rehearsal.willingnessToPay.counts.unrecorded, 2);
  assert.doesNotMatch(result.stdout, /TEST-INVALID-WTP/);
});
