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

Give the authorized buyer-pilot facilitator the approved `caseCards` from an actual report. Use `caseId` to tie the baseline decision and success criterion to the follow-up choice, elapsed time, cited evidence and unresolved uncertainty. Track willingness to pay separately in the buyer pilot. [Buyer decision pilot](https://github.com/OmniMCP-AI/local-llm/issues/19)

Run the synthetic checks with `node --test research-pilot/decision-cases.test.mjs`.
