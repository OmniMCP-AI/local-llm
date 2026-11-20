import { readFileSync } from "node:fs";

const cohortSize = 8;
const decisions = ["keep", "cloud", "upgrade", "undecided"];
const responseOptions = ["yes", "no", "undecided", "not_asked"];

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function missingFields(row, caseIds) {
  if (row.consent !== "granted") return ["consent"];
  if (row.redactionReviewed !== true) return ["redactionReviewed"];
  if (!caseIds.has(row.caseId)) return ["caseId"];

  const missing = [];
  if (!isText(row.currentAlternative)) missing.push("currentAlternative");
  if (!decisions.includes(row.baselineDecision)) missing.push("baselineDecision");
  if (!decisions.includes(row.finalDecision)) missing.push("finalDecision");
  if (!Number.isFinite(row.elapsedSeconds) || row.elapsedSeconds < 0) missing.push("elapsedSeconds");
  if (typeof row.explainedChoice !== "boolean") missing.push("explainedChoice");
  if (!Array.isArray(row.citedEvidence) || !row.citedEvidence.every(isText)) missing.push("citedEvidence");
  for (const field of ["resolvedUncertainty", "unresolvedUncertainty", "followUpCase"]) {
    if (row[field] !== null && !isText(row[field])) missing.push(field);
  }
  return missing;
}

function review({ mode, caseIntake, observations }) {
  const caseIds = new Set();
  if (caseIntake !== undefined || observations.length > 0) {
    if (caseIntake?.mode !== mode || !Array.isArray(caseIntake.caseCards)) {
      throw new Error("Provide a reviewed case intake handoff in the same mode.");
    }
    for (const card of caseIntake.caseCards) {
      if (typeof card?.caseId !== "string" || !/^case-[0-9]{3}$/.test(card.caseId) || caseIds.has(card.caseId)) {
        throw new Error("The reviewed handoff needs unique case IDs in the format case-001.");
      }
      caseIds.add(card.caseId);
    }
  }

  const participantIds = new Set();
  const eligible = [];
  const held = [];
  for (const [index, row] of observations.entries()) {
    const participantId = row?.participantId;
    if (typeof participantId !== "string" || !/^participant-[0-9]{3}$/.test(participantId)) {
      throw new Error(`Observation ${index + 1} needs a participant ID in the format participant-001.`);
    }
    if (participantIds.has(participantId)) {
      throw new Error(`Observation ${index + 1} has a duplicate participant ID.`);
    }
    participantIds.add(participantId);
    const missing = missingFields(row, caseIds);
    if (missing.length > 0) held.push({ participantId, missing });
    else eligible.push(row);
  }
  if (eligible.length > cohortSize) throw new Error("Submit a cohort of at most eight eligible participants.");
  return summarize(eligible, held);
}

function summarize(rows = [], heldObservations = []) {
  const observations = rows.map(({
    participantId, caseId, currentAlternative, baselineDecision, finalDecision,
    elapsedSeconds, explainedChoice, citedEvidence, resolvedUncertainty,
    unresolvedUncertainty, followUpCase,
  }) => ({
    participantId, caseId, currentAlternative, baselineDecision, finalDecision,
    decisionChanged: baselineDecision !== finalDecision,
    elapsedSeconds, explainedChoice, citedEvidence, resolvedUncertainty,
    unresolvedUncertainty, followUpCase,
  }));
  const complete = observations.length === cohortSize;
  function gate(target, qualifies) {
    const observed = observations.filter(qualifies).length;
    return { observed, target, met: complete ? observed >= target : null };
  }

  const gates = {
    supportedChoiceWithinTenMinutes: gate(6, row => row.explainedChoice &&
      row.finalDecision !== "undecided" && row.elapsedSeconds <= 600 && row.citedEvidence.length > 0),
    specificUncertaintyResolved: gate(5, row => row.resolvedUncertainty !== null),
    broughtFollowUp: gate(3, row => row.followUpCase !== null),
  };
  let status = observations.length === 0 ? "missing" : "incomplete";
  if (complete) status = Object.values(gates).every(gate => gate.met) ? "met" : "missed";

  const responses = rows.map(({ participantId, willingnessToPay }) => ({
    participantId,
    response: responseOptions.includes(willingnessToPay) ? willingnessToPay : "unrecorded",
  }));
  const counts = Object.fromEntries([...responseOptions, "unrecorded"].map(option => [
    option, responses.filter(({ response }) => response === option).length,
  ]));
  return {
    status,
    participants: { observed: observations.length, target: cohortSize, remaining: cohortSize - observations.length },
    gates,
    observations,
    heldObservations,
    willingnessToPay: { counts, responses },
  };
}

function main() {
  const text = process.stdin.isTTY ? "" : readFileSync(0, "utf8").trim();
  let input;
  try {
    input = text === "" ? { mode: "actual", observations: [] } : JSON.parse(text);
  } catch {
    console.error("Provide valid buyer pilot JSON on stdin.");
    return 1;
  }
  if (!["actual", "synthetic"].includes(input?.mode) || !Array.isArray(input.observations)) {
    console.error('Use a mode of "actual" or "synthetic" and an observations array.');
    return 1;
  }
  const { mode } = input;
  try {
    const summary = review(input);
    const report = mode === "synthetic"
      ? { mode, actual: summarize(), rehearsal: summary }
      : { mode, actual: summary };
    console.log(JSON.stringify(report, null, 2));
    return 0;
  } catch (error) {
    console.error(error.message);
    return 1;
  }
}

process.exitCode = main();
