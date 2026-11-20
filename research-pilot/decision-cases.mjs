import { readFileSync } from "node:fs";

const requiredTextFields = [
  "task",
  "currentHardwareOrAlternative",
  "budget",
  "deadline",
  "privacyConstraints",
  "unresolved",
  "successCriterion",
];
const baselineDecisions = new Set(["keep", "cloud", "upgrade", "undecided"]);

function isText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function missingFields({ consent, redactionReviewed, card }) {
  if (consent !== "granted") return ["consent"];
  if (redactionReviewed !== true) return ["redactionReviewed"];

  const missing = requiredTextFields.filter(field => !isText(card?.[field]));
  if (!baselineDecisions.has(card?.baselineDecision)) missing.push("baselineDecision");
  if (card?.alternative !== undefined && !isText(card.alternative)) {
    missing.push("alternative");
  }
  return missing;
}

function reviewIntake({ mode, interviews }) {
  const caseCards = [];
  const heldCases = [];
  for (const interview of interviews) {
    const { caseId, card } = interview;
    const missing = missingFields(interview);
    if (missing.length > 0) {
      heldCases.push({ caseId, missing });
      continue;
    }

    const result = { caseId, baselineDecision: card.baselineDecision };
    for (const field of requiredTextFields) result[field] = card[field].trim();
    if (card.alternative !== undefined) result.alternative = card.alternative.trim();
    caseCards.push(result);
  }

  const isActual = mode === "actual";
  const actualInterviews = isActual ? interviews.length : 0;
  const actualCases = isActual ? caseCards.length : 0;
  const targetMinimum = 10;
  const targetMaximum = 12;
  const caseTarget = 5;
  const review = {
    interviews: {
      actual: actualInterviews,
      synthetic: isActual ? 0 : interviews.length,
      targetMinimum,
      targetMaximum,
      remainingToMinimum: Math.max(0, targetMinimum - actualInterviews),
    },
    cases: {
      actual: actualCases,
      synthetic: isActual ? 0 : caseCards.length,
      target: caseTarget,
      remainingToTarget: Math.max(0, caseTarget - actualCases),
    },
  };
  return { mode, review, caseCards, heldCases };
}

function validateIntake(intake) {
  if (!["actual", "synthetic"].includes(intake?.mode) || !Array.isArray(intake?.interviews)) {
    return 'Use a mode of "actual" or "synthetic" and an interviews array.';
  }

  const caseIds = new Set();
  for (const [index, interview] of intake.interviews.entries()) {
    const caseId = interview?.caseId;
    if (typeof caseId !== "string" || !/^case-[0-9]{3}$/.test(caseId)) {
      return `Interview ${index + 1} needs a case ID in the format case-001.`;
    }
    if (caseIds.has(caseId)) {
      return `Interview ${index + 1} has a duplicate case ID.`;
    }
    caseIds.add(caseId);
  }
}

function main() {
  let intake;
  try {
    intake = JSON.parse(readFileSync(0, "utf8"));
  } catch {
    console.error("Provide valid intake JSON on stdin.");
    return 1;
  }

  const error = validateIntake(intake);
  if (error) {
    console.error(error);
    return 1;
  }
  console.log(JSON.stringify(reviewIntake(intake), null, 2));
  return 0;
}

process.exitCode = main();
