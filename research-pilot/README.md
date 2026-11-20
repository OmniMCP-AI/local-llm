# Decision case intake

The four-to-six week validation proposed in the [product spec](../docs/product-spec.md) calls for 10–12 target-user interviews and five consented, concrete cases. As of setup, the pilot has **zero actual interviews and zero actual cases**. The minimum interview gap is 10 and the case gap is five. Outreach, interviews and consent require a human researcher. [Decision case issue](https://github.com/OmniMCP-AI/local-llm/issues/9)

## Conduct an interview

Interview Chinese-speaking marketing or e-commerce users about a recent choice involving local AI hardware, a cloud endpoint or an upgrade. Ask what they needed to do, what they use today, what they can spend, when they need a solution, what data must stay private and which uncertainty still prevents a decision. Capture their baseline before showing fastest.ai. Ask what observable result or evidence would make the choice defensible.

Prepare a short paraphrase for the case card when the participant grants permission to use the case in the pilot. Remove names, handles, contact details, company and customer identifiers, private prompts, exact quotes and any combination of details that could identify the participant. Generalize identifying details while preserving the decision constraints. Keep source material and proof of consent in the researcher's approved private storage.

## Prepare the local intake

The input is a JSON object with `mode` set to `actual` for completed target-user interviews or `synthetic` for a rehearsal, plus an `interviews` array. Use one row per completed interview and assign a stable code in the form `case-001`. Keep the same code when an interview is updated. Store the input and exported report outside version control. The `research-pilot/records/` directory is ignored if you keep files under the checkout.

Each interview has these fields.

| Field | Value |
| --- | --- |
| `caseId` | Unique code in the form `case-001`, assigned by the researcher. |
| `consent` | `granted`, `pending`, `declined` or `withdrawn`. For an interview without granted consent, keep only the code and status if the research process permits tracking the completion. |
| `redactionReviewed` | Boolean. Set to `true` when a person has checked the wording of every card field. |
| `card` | Object with the reviewed fields below. |

| Card field | Value |
| --- | --- |
| `task` | String giving the concrete task and workload or volume when relevant. |
| `currentHardwareOrAlternative` | String describing the existing system or current workaround. |
| `alternative` | Optional string describing another option the participant considered. |
| `budget` | String giving the amount or range, currency and spending period where applicable. |
| `deadline` | String giving the decision deadline or time window. |
| `privacyConstraints` | String describing what can leave the device or organization, if anything. |
| `unresolved` | String identifying the uncertainty to test. |
| `baselineDecision` | `keep`, `cloud`, `upgrade` or `undecided` before using fastest.ai. |
| `successCriterion` | String describing the observable result or evidence required to resolve the uncertainty. |

Use a string with meaningful content for each required text field. Leave a field absent if it is missing so the review can flag the gap. The tool checks structure and recognizes the reviewer's consent and redaction flags. The researcher is responsible for the accuracy of those flags and the content of every exported field.

## Review and hand off

Run the review offline from the repository root with Node.js.

```sh
node research-pilot/decision-cases.mjs < research-pilot/records/intake.json
```

To inspect the initial counts without creating a file:

```sh
printf '%s\n' '{"mode":"actual","interviews":[]}' | node research-pilot/decision-cases.mjs
```

The JSON report gives actual and synthetic counts, remaining gaps to 10 interviews and five cases, eligible `caseCards`, and `heldCases` with fields to review. It exits with status 1 for malformed input, invalid case IDs or duplicate case IDs. A rehearsal never counts toward recruitment. If consent is withdrawn, update the intake and use a fresh report to remove that card from any handoff.

Give the authorized buyer-pilot facilitator the reviewed intake report. Its `caseCards` carry the baseline and success criterion for each approved case.

## Report the buyer decision pilot

The eight-person pilot is pending. The report starts with zero actual observations and eight remaining. An authorized facilitator needs approved cases, a comparison and evidence participants can inspect, and consent from each participant. [Buyer decision pilot](https://github.com/OmniMCP-AI/local-llm/issues/19)

Record each participant's current alternative and baseline choice before showing the comparison. Start the timer when they open the comparison. Record the elapsed time when they explain a supported choice, or the time spent if they finish without a supported explanation. Note the evidence they cite, the specific uncertainty they resolved, any question that remains, and any follow-up decision they bring. Ask about willingness to pay separately.

Store only reviewed paraphrases in the input. Assign each person a code such as `participant-001` and reuse that code for corrections. Keep the original `caseId` from the reviewed handoff. Several participants may use the same case. Keep the input, output and any private identity or consent records in authorized storage outside version control.

The input JSON has a `mode` of `actual` or `synthetic`, a `caseIntake` containing the JSON output from `decision-cases.mjs` in the same mode, and an `observations` array. Use one row per person in the cohort.

| Field | Value |
| --- | --- |
| `participantId` | Unique researcher-assigned code in the format `participant-001`. |
| `caseId` | Unchanged code from `caseIntake.caseCards`. |
| `consent` | `granted` when the participant has consented to this use. An observation with pending, declined or withdrawn consent can retain only its code and status if the research process permits it. |
| `redactionReviewed` | `true` when the facilitator has reviewed every field for private or identifying details. |
| `currentAlternative` | Text describing what the participant currently uses. |
| `baselineDecision`, `finalDecision` | `keep`, `cloud`, `upgrade` or `undecided`. |
| `elapsedSeconds` | Nonnegative number of seconds spent on the decision. |
| `explainedChoice` | Boolean indicating whether the participant explained the reason for their choice. |
| `citedEvidence` | Array of short references that support the explanation. Use `[]` if none were cited. |
| `resolvedUncertainty`, `unresolvedUncertainty` | Reviewed text describing the specific uncertainty resolved and what still needs evidence, respectively. Use `null` where there is none. |
| `followUpCase` | Reviewed text describing a concrete follow-up decision the participant brought, or `null`. |
| `willingnessToPay` | Optional `yes`, `no`, `undecided` or `not_asked`. Missing or unrecognized answers are reported as `unrecorded`. |

```sh
node research-pilot/buyer-pilot.mjs < research-pilot/records/buyer-pilot.json
node research-pilot/buyer-pilot.mjs </dev/null
node --test research-pilot/*.test.mjs
```

The report shows each eligible observation and whether its decision changed. The three proposed gates require six supported explanations within 600 seconds, five specific uncertainties resolved, and three concrete follow-up decisions. Each gate has an observed count and a target. Its `met` value stays `null` until exactly eight eligible participants are present. The cohort status is `missing` with zero eligible participants, `incomplete` with one to seven, and `met` or `missed` for a full cohort. Willingness to pay has its own counts and coded responses and has no effect on the gates.

Held observations show the participant code and fields to review. If consent changes, update the observation and use a fresh intake handoff before regenerating the report. Invalid JSON, inconsistent handoff mode, invalid or duplicate participant codes, and more than eight eligible participants stop the report with an error. A fictional rehearsal reports its results under `rehearsal` and leaves the actual status `missing`.
