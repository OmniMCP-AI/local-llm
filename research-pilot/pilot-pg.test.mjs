import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const command = name => fileURLToPath(new URL(name, import.meta.url));
const hasPostgres = ["initdb", "pg_ctl", "psql"].every(tool =>
  spawnSync(tool, ["--version"], { encoding: "utf8" }).status === 0);

function runTool(tool, args, options = {}) {
  return spawnSync(tool, args, { encoding: "utf8", timeout: 30_000, ...options });
}

function successful(result) {
  assert.equal(result.status, 0, result.error?.message ?? result.stderr);
  return result.stdout;
}

function disposableDatabase(t) {
  // A short path leaves room for the Unix socket on platforms with a small sun_path.
  const directory = mkdtempSync(join(tmpdir(), "pilot-pg-"));
  const cluster = join(directory, "data");
  const cleanup = () => {
    const status = () => runTool("pg_ctl", ["status", "-D", cluster]).status;
    if (status() === 0) successful(runTool("pg_ctl", ["stop", "-D", cluster, "-m", "immediate", "-w"]));
    assert.notEqual(status(), 0, `PostgreSQL is still running in ${directory}`);
    rmSync(directory, { recursive: true, force: true });
    assert.equal(existsSync(directory), false);
  };
  const interrupt = () => {
    cleanup();
    process.exit(1);
  };
  process.once("SIGINT", interrupt);
  process.once("SIGTERM", interrupt);
  t.after(() => {
    process.off("SIGINT", interrupt);
    process.off("SIGTERM", interrupt);
    cleanup();
  });
  successful(runTool("initdb", ["-D", cluster, "--auth=trust", "--encoding=UTF8", "--no-locale", "-U", "pilot_operator"]));
  successful(runTool("pg_ctl", ["start", "-D", cluster, "-l", join(directory, "postgres.log"), "-w",
    "-o", `-c listen_addresses='' -c unix_socket_directories='${directory}'`]));
  return `host='${directory}' dbname=postgres user=pilot_operator`;
}

function pilot(database, action, payload) {
  return runTool(process.execPath, [command("./pilot-pg.mjs"), action], {
    env: { ...process.env, FASTEST_PILOT_DATABASE_URL: database },
    input: payload === undefined ? undefined : JSON.stringify(payload),
  });
}

const card = {
  task: "Draft product summaries",
  currentHardwareOrAlternative: "Manual drafting",
  budget: "CNY 400 per month",
  deadline: "One week",
  privacyConstraints: "Unpublished catalog stays local",
  unresolved: "Can a local system finish the batch in time?",
  baselineDecision: "keep",
  successCriterion: "Finish a generic batch in ten minutes",
};
const interview = (caseId = "case-001", overrides = {}) => ({ caseId, consent: "granted", redactionReviewed: true, card, ...overrides });
const actualIntake = interviews => ({ mode: "actual", interviews });
const actualBuyers = observations => ({ mode: "actual", observations });

const observation = (index = 0, overrides = {}) => ({
  participantId: `participant-${String(index + 1).padStart(3, "0")}`,
  caseId: "case-001",
  consent: "granted",
  redactionReviewed: true,
  currentAlternative: "Manual drafting",
  baselineDecision: "keep",
  finalDecision: index === 0 ? "upgrade" : "keep",
  elapsedSeconds: index === 6 ? 601 : 600,
  explainedChoice: true,
  citedEvidence: index === 7 ? [] : ["Comparison timing row"],
  resolvedUncertainty: index < 5 ? "The local system meets the deadline" : null,
  unresolvedUncertainty: "Capacity at double volume",
  followUpCase: index < 3 ? "Choose a setup for a larger batch" : null,
  willingnessToPay: ["yes", "yes", "no", "undecided", "not_asked", undefined, "unrecognized", "not_asked"][index],
  ...overrides,
});

const readReport = database => JSON.parse(successful(pilot(database, "report")));

test("a repeatable PostgreSQL import produces the current actual report", { skip: !hasPostgres }, t => {
  const database = disposableDatabase(t);
  successful(pilot(database, "init"));
  const intake = actualIntake([
    interview(), interview("case-002"), interview("case-003", { consent: "pending" }),
  ]);
  const buyers = Array.from({ length: 8 }, (_, index) => observation(index));
  for (let attempt = 0; attempt < 2; attempt += 1) {
    successful(pilot(database, "import-intake", intake));
    successful(pilot(database, "import-buyers", actualBuyers(buyers.slice(0, 4))));
    successful(pilot(database, "import-buyers", actualBuyers(buyers.slice(4))));
  }
  const { caseIntake, buyerPilot } = readReport(database);
  assert.deepEqual(caseIntake.review, {
    interviews: { actual: 3, synthetic: 0, targetMinimum: 10, targetMaximum: 12, remainingToMinimum: 7 },
    cases: { actual: 2, synthetic: 0, target: 5, remainingToTarget: 3 },
  });
  assert.deepEqual(caseIntake.caseCards, [{ caseId: "case-001", ...card }, { caseId: "case-002", ...card }]);
  assert.deepEqual(caseIntake.heldCases, [{ caseId: "case-003", missing: ["consent"] }]);
  assert.deepEqual(buyerPilot.actual.participants, { observed: 8, target: 8, remaining: 0 });
  assert.equal(buyerPilot.actual.status, "met");
  assert.deepEqual(buyerPilot.actual.gates, {
    supportedChoiceWithinTenMinutes: { observed: 6, target: 6, met: true },
    specificUncertaintyResolved: { observed: 5, target: 5, met: true },
    broughtFollowUp: { observed: 3, target: 3, met: true },
  });
  assert.deepEqual(buyerPilot.actual.willingnessToPay.counts, { yes: 2, no: 1, undecided: 1, not_asked: 2, unrecorded: 2 });
  assert.equal(buyerPilot.actual.observations[0].decisionChanged, true);
  assert.equal(buyerPilot.actual.observations[1].decisionChanged, false);
  assert.equal(buyerPilot.rehearsal, undefined);
  const catalogStats = fileURLToPath(new URL("../opendesign/mockups/llm-observatory/catalog-stats.sql", import.meta.url));
  const counts = successful(runTool("psql", ["-X", "-qAt", "--dbname", database, "-f", catalogStats]));
  assert.equal(counts.trim(), "fastest_decision_pilot.buyer_observation|8\nfastest_decision_pilot.decision_case|3");
});

function snapshot(database) {
  return successful(runTool("psql", ["-X", "-qAt", "--dbname", database, "--set=ON_ERROR_STOP=1"], {
    input: `SELECT row_to_json(decision_case) FROM fastest_decision_pilot.decision_case ORDER BY case_id;
      SELECT row_to_json(buyer_observation) FROM fastest_decision_pilot.buyer_observation ORDER BY participant_id;`,
  }));
}

test("withdrawn cases and participants lose stored details and stay held on replay", { skip: !hasPostgres }, t => {
  const database = disposableDatabase(t);
  successful(pilot(database, "init"));
  const intake = actualIntake([
    interview("case-001", { card: { ...card, unresolved: "TEST-PURGE-CASE" } }), interview("case-002"),
  ]);
  const cohort = actualBuyers([
    observation(0, { resolvedUncertainty: "TEST-PURGE-LINKED-OBSERVATION" }),
    observation(1, { caseId: "case-002", resolvedUncertainty: "TEST-PURGE-WITHDRAWN-OBSERVATION" }),
    observation(2, { caseId: "case-002" }),
  ]);
  successful(pilot(database, "import-intake", intake));
  successful(pilot(database, "import-buyers", cohort));
  assert.equal(readReport(database).buyerPilot.actual.participants.observed, 3);

  successful(pilot(database, "import-intake", actualIntake([{ caseId: "case-001", consent: "withdrawn" }])));
  successful(pilot(database, "import-buyers", actualBuyers([{ participantId: "participant-002", consent: "withdrawn" }])));
  for (const replay of [false, true]) {
    if (replay) {
      successful(pilot(database, "import-intake", intake));
      successful(pilot(database, "import-buyers", cohort));
    }
    const rawReport = successful(pilot(database, "report"));
    const stored = snapshot(database);
    const { caseIntake, buyerPilot } = JSON.parse(rawReport);
    assert.equal(caseIntake.review.interviews.actual, 2);
    assert.deepEqual(caseIntake.caseCards, [{ caseId: "case-002", ...card }]);
    assert.deepEqual(caseIntake.heldCases, [{ caseId: "case-001", missing: ["consent"] }]);
    assert.deepEqual(buyerPilot.actual.heldObservations, [
      { participantId: "participant-001", missing: ["caseId"] },
      { participantId: "participant-002", missing: ["consent"] },
    ]);
    assert.deepEqual(buyerPilot.actual.participants, { observed: 1, target: 8, remaining: 7 });
    assert.equal(buyerPilot.actual.status, "incomplete");
    assert.deepEqual(Object.values(buyerPilot.actual.gates).map(({ met }) => met), [null, null, null]);
    assert.deepEqual(buyerPilot.actual.willingnessToPay.responses, [{ participantId: "participant-003", response: "no" }]);
    assert.doesNotMatch(rawReport + stored, /TEST-PURGE/);
    assert.match(stored, /"case_id":"case-001","consent":"withdrawn","missing":\["consent"\],"details":null/);
    assert.match(stored, /"participant_id":"participant-001","case_id":null,"consent":"granted","missing":\["caseId"\],"details":null/);
    assert.match(stored, /"participant_id":"participant-002","case_id":null,"consent":"withdrawn","missing":\["consent"\],"details":null/);
  }
});

test("the private store retains only reviewed fields and held dispositions from actual intake", { skip: !hasPostgres }, t => {
  const database = disposableDatabase(t);
  successful(pilot(database, "init"));
  successful(pilot(database, "init"));
  const intake = actualIntake([
    interview("case-001", { sourceInterview: "TEST-INTERVIEW", card: { ...card, email: "TEST-CONTACT" } }),
    interview("case-002", { consent: "declined", card: { ...card, task: "TEST-DECLINED" } }),
    interview("case-003", { redactionReviewed: false, card: { ...card, task: "TEST-UNREVIEWED-CASE" } }),
    interview("case-004", { card: { ...card, budget: " ", task: "TEST-INCOMPLETE-CASE" } }),
    interview("case-005", { consent: "TEST-UNRECOGNIZED-CONSENT" }),
  ]);
  const observations = actualBuyers([
    observation(0, { privateNotes: "TEST-BUYER-NOTES", willingnessToPay: "TEST-UNRECOGNIZED-WTP" }),
    observation(1, { consent: "pending", resolvedUncertainty: "TEST-PENDING" }),
    observation(2, { redactionReviewed: false, resolvedUncertainty: "TEST-UNREVIEWED-OBSERVATION" }),
    observation(3, { resolvedUncertainty: " ", currentAlternative: "TEST-INCOMPLETE-OBSERVATION" }),
    observation(4, { caseId: "case-999", currentAlternative: "TEST-UNAPPROVED-OBSERVATION" }),
  ]);
  for (const [action, input] of [["import-intake", intake], ["import-buyers", observations]]) {
    const rejected = pilot(database, action, { ...input, mode: "synthetic" });
    assert.equal(rejected.status, 1);
    assert.equal(rejected.stdout, "");
    assert.match(rejected.stderr, /mode "actual"/);
    assert.doesNotMatch(rejected.stderr, /TEST-/);
  }
  assert.equal(snapshot(database), "");
  assert.equal(readReport(database).buyerPilot.actual.status, "missing");

  successful(pilot(database, "import-intake", intake));
  // A stale handoff cannot grant permission to a case missing from the current PostgreSQL intake.
  successful(pilot(database, "import-buyers", {
    ...observations, caseIntake: { mode: "actual", caseCards: [{ caseId: "case-999" }] },
  }));
  const rawReport = successful(pilot(database, "report"));
  const { caseIntake, buyerPilot } = JSON.parse(rawReport);
  assert.deepEqual(caseIntake.heldCases, [
    { caseId: "case-002", missing: ["consent"] },
    { caseId: "case-003", missing: ["redactionReviewed"] },
    { caseId: "case-004", missing: ["budget"] },
    { caseId: "case-005", missing: ["consent"] },
  ]);
  assert.deepEqual(buyerPilot.actual.heldObservations, [
    { participantId: "participant-002", missing: ["consent"] },
    { participantId: "participant-003", missing: ["redactionReviewed"] },
    { participantId: "participant-004", missing: ["resolvedUncertainty"] },
    { participantId: "participant-005", missing: ["caseId"] },
  ]);
  assert.deepEqual(buyerPilot.actual.willingnessToPay.responses, [{ participantId: "participant-001", response: "unrecorded" }]);
  assert.doesNotMatch(rawReport + snapshot(database), /TEST-|case-999/);

  const permissions = successful(runTool("psql", ["-X", "-qAt", "--dbname", database, "--set=ON_ERROR_STOP=1"], {
    input: `CREATE ROLE pilot_reader;
      SELECT has_schema_privilege('pilot_reader', 'fastest_decision_pilot', 'USAGE'),
        has_table_privilege('pilot_reader', 'fastest_decision_pilot.decision_case', 'SELECT'),
        has_table_privilege('pilot_reader', 'fastest_decision_pilot.buyer_observation', 'SELECT');`,
  }));
  assert.equal(permissions.trim(), "f|f|f");
});

test("invalid or oversized PostgreSQL batches preserve the current cohort", { skip: !hasPostgres }, t => {
  const database = disposableDatabase(t);
  successful(pilot(database, "init"));
  successful(pilot(database, "import-intake", actualIntake([interview()])));
  successful(pilot(database, "import-buyers", actualBuyers(Array.from({ length: 8 }, (_, index) => observation(index)))));
  const before = snapshot(database);
  const cases = [
    { action: "import-intake", input: actualIntake([interview(), interview()]), error: /duplicate case ID/ },
    { action: "import-buyers", input: actualBuyers([observation(0), observation(0)]), error: /duplicate participant ID/ },
    { action: "import-buyers", input: actualBuyers([observation(0, { currentAlternative: "TEST-REJECTED-CORRECTION" }), observation(8)]), error: /at most eight/ },
  ];
  for (const { action, input, error } of cases) {
    const rejected = pilot(database, action, input);
    assert.equal(rejected.status, 1);
    assert.equal(rejected.stdout, "");
    assert.match(rejected.stderr, error);
    assert.doesNotMatch(rejected.stderr, /TEST-/);
    assert.equal(snapshot(database), before);
  }
});
