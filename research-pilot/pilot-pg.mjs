import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { cohortSize, reviewObservations, summarize } from "./buyer-pilot.mjs";
import { reviewIntake, summarizeIntake, validateIntake } from "./decision-cases.mjs";

const cases = "fastest_decision_pilot.decision_case";
const buyers = "fastest_decision_pilot.buyer_observation";
const beginWrite = `BEGIN;
SET LOCAL lock_timeout = '10s';
LOCK TABLE ${cases}, ${buyers} IN SHARE ROW EXCLUSIVE MODE;`;

function runSql(database, input) {
  const result = spawnSync("psql", ["-X", "-w", "-qAt", "--set=ON_ERROR_STOP=1", "--dbname", database], {
    input, encoding: "utf8", timeout: 30_000, maxBuffer: 16 * 1024 * 1024,
  });
  if (result.status !== 0) {
    throw new Error("PostgreSQL pilot command failed. Check the connection, schema initialization and database permissions.");
  }
  return result.stdout.trim();
}

function recordset(rows, columns) {
  // Encode the already projected rows to keep values out of the SQL syntax and psql commands.
  const encoded = Buffer.from(JSON.stringify(rows)).toString("base64");
  return `jsonb_to_recordset(convert_from(decode('${encoded}', 'base64'), 'UTF8')::jsonb) AS input(${columns})`;
}

function consentStatus(value) {
  return ["granted", "pending", "declined", "withdrawn"].includes(value) ? value : null;
}

function readActualInput() {
  let input;
  try {
    input = JSON.parse(readFileSync(0, "utf8"));
  } catch {
    throw new Error("Provide valid pilot JSON on stdin.");
  }
  if (input?.mode !== "actual") throw new Error('PostgreSQL imports require mode "actual".');
  return input;
}

function importIntake(database, input) {
  const error = validateIntake(input);
  if (error) throw new Error(error);
  const status = new Map(input.interviews.map(row => [row.caseId, consentStatus(row.consent)]));
  const { caseCards, heldCases } = reviewIntake(input);
  const rows = [
    ...caseCards.map(({ caseId, ...details }) => ({ case_id: caseId, consent: status.get(caseId), missing: [], details })),
    ...heldCases.map(({ caseId, missing }) => ({ case_id: caseId, consent: status.get(caseId), missing })),
  ];
  runSql(database, `${beginWrite}
    INSERT INTO ${cases} AS current_case (case_id, consent, missing, details)
    SELECT case_id, consent, missing, details
    FROM ${recordset(rows, "case_id text, consent text, missing text[], details jsonb")}
    ON CONFLICT (case_id) DO UPDATE SET
      consent = EXCLUDED.consent, missing = EXCLUDED.missing, details = EXCLUDED.details
      WHERE current_case.consent IS DISTINCT FROM 'withdrawn';
    UPDATE ${buyers} AS buyer
    SET case_id = NULL, missing = ARRAY['caseId'], details = NULL
    FROM ${cases} AS decision_case
    WHERE buyer.case_id = decision_case.case_id AND decision_case.details IS NULL;
    COMMIT;`);
}

function importBuyers(database, input) {
  if (!Array.isArray(input.observations)) throw new Error("Provide an observations array.");
  const caseIds = JSON.parse(runSql(database, `SELECT coalesce(json_agg(case_id ORDER BY case_id), '[]'::json)
    FROM ${cases} WHERE details IS NOT NULL;`));
  const caseIntake = { mode: "actual", caseCards: caseIds.map(caseId => ({ caseId })) };
  const { eligible, held } = reviewObservations({ ...input, caseIntake });
  const status = new Map(input.observations.map(row => [row.participantId, consentStatus(row.consent)]));
  const rows = [
    ...eligible.map(({ participantId, caseId, ...details }) => ({
      participant_id: participantId, case_id: caseId, consent: status.get(participantId), missing: [], details,
    })),
    ...held.map(({ participantId, missing }) => ({ participant_id: participantId, consent: status.get(participantId), missing })),
  ];
  const result = runSql(database, `${beginWrite}
    SELECT coalesce(array_agg(case_id ORDER BY case_id), ARRAY[]::text[]) =
      ARRAY[${caseIds.map(id => `'${id}'`).join(",")}]::text[] AS same_approval
      FROM ${cases} WHERE details IS NOT NULL \\gset
    \\if :same_approval
      INSERT INTO ${buyers} AS current_buyer (participant_id, case_id, consent, missing, details)
      SELECT participant_id, case_id, consent, missing, details
      FROM ${recordset(rows, "participant_id text, case_id text, consent text, missing text[], details jsonb")}
      ON CONFLICT (participant_id) DO UPDATE SET
        case_id = EXCLUDED.case_id, consent = EXCLUDED.consent, missing = EXCLUDED.missing, details = EXCLUDED.details
        WHERE current_buyer.consent IS DISTINCT FROM 'withdrawn';
      SELECT count(*) <= ${cohortSize} AS cohort_fits FROM ${buyers} WHERE details IS NOT NULL \\gset
      \\if :cohort_fits
        COMMIT;
      \\else
        ROLLBACK;
        \\echo cohort-too-large
      \\endif
    \\else
      ROLLBACK;
      \\echo approval-changed
    \\endif`);
  if (result === "cohort-too-large") throw new Error("Submit a cohort of at most eight eligible participants.");
  if (result === "approval-changed") throw new Error("Approved cases changed during import. Retry with the latest intake.");
}

function report(database) {
  const current = JSON.parse(runSql(database, `SELECT json_build_object(
    'cases', (SELECT coalesce(json_agg(decision_case ORDER BY case_id), '[]'::json) FROM ${cases}),
    'buyers', (SELECT coalesce(json_agg(buyer_observation ORDER BY participant_id), '[]'::json) FROM ${buyers})
  );`));
  const caseCards = [];
  const heldCases = [];
  for (const { case_id: caseId, details, missing } of current.cases) {
    if (details === null) heldCases.push({ caseId, missing });
    else caseCards.push({ caseId, ...details });
  }
  const eligible = [];
  const held = [];
  for (const { participant_id: participantId, case_id: caseId, details, missing } of current.buyers) {
    if (details === null) held.push({ participantId, missing });
    else eligible.push({ participantId, caseId, ...details });
  }
  return {
    caseIntake: summarizeIntake("actual", caseCards, heldCases),
    buyerPilot: { mode: "actual", actual: summarize(eligible, held) },
  };
}

function main() {
  const [action, ...extra] = process.argv.slice(2);
  if (extra.length || !["init", "import-intake", "import-buyers", "report"].includes(action)) {
    throw new Error("Usage: node research-pilot/pilot-pg.mjs {init|import-intake|import-buyers|report}");
  }
  const database = process.env.FASTEST_PILOT_DATABASE_URL;
  if (!database?.trim()) throw new Error("Set FASTEST_PILOT_DATABASE_URL to an authorized PostgreSQL database.");
  if (action === "init") runSql(database, readFileSync(new URL("./pilot-pg.sql", import.meta.url), "utf8"));
  if (action === "import-intake") importIntake(database, readActualInput());
  if (action === "import-buyers") importBuyers(database, readActualInput());
  if (action === "report") console.log(JSON.stringify(report(database), null, 2));
}

try {
  main();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
