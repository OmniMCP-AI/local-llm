# Text workload cost comparison

From `production/`, run `python3 -B -m fastest_release serve` and open [Compare text workload costs](http://127.0.0.1:8000/costs). Choose the illustrative example to see fully populated calculations. Change accepted tasks per month and the horizon to update the comparison, cumulative curve, sensitivity and payback in one request. The HTTP response links to the same result in Markdown and JSON. The comparison needs no database to run.

The public evidence scenario reports missing prerequisites until the operator supplies approved inputs. The [text pilot](../fastest_text/README.md) describes the task and review rubric. Its isolated prefill and decode phases have a different latency boundary from completed requests. The cost gate requires same-task capacity, review outcomes and p95 completion latency for each option. [Regional price releases](../fastest_prices/README.md) identify exact markets, quote scope and conditions. The comparison requires comparable, permitted landed prices for the complete configurations, as well as approved local electricity and endpoint tariffs when applicable. The checked-in examples are fictional. An illustrative result carries no market or measurement claim.

The same read-only `fastest_cost.calculate(selection)` function supplies every format. It accepts a mapping of `scenario` (`evidence` or `illustrative`), `monthly_accepted` (1–100,000,000) and `months` (1–120). Selectors are optional. The default demand is 1,800 accepted tasks per month over 24 months. Results carry a schema version, method, input revisions and a digest of the assumptions. Money and derived decimal quantities are strings with up to six decimal places. Counts are integers. Unknown or inapplicable values are null, with service and payback outcomes explaining why a comparison is withheld.

## Configure reviewed evidence

Start the release server with `--cost-scenario /path/to/reviewed-cost.json` to
load one operator-reviewed scenario into the **Public evidence** view. The
calculator, HTML and Markdown, JSON API, and advisor use the same inputs.
The public selectors control task volume, time horizon and view. The
configured file governs which evidence can be used.

Operators can inspect tariff candidates in the private PostgreSQL intake.
Check the source revision, effective dates, market, exact meter or endpoint,
billing terms and workload eligibility before approving any candidate. For a
time-of-use schedule, document how usage in each band maps to the scenario's
single `per_kwh` input and which fixed charges are attributable to the workload.
Assess any applicable storage, transfer and other charges before reviewing a
base cloud rate as an operating input.
[Private intake workflow](../fastest_intake/README.md)

Use a JSON object with these fields.

| Field | Required contents |
| --- | --- |
| `schema_version`, `revision` | Integer 1 and an immutable input revision. Change the revision when the reviewed inputs change. |
| `authorization` | `status` set to `approved`, a publication review `decision_id` as a canonical UUID, and `expires_at` in UTC `YYYY-MM-DDTHH:MM:SSZ` format. |
| `workload` | Copy `id`, `revision`, `quality_rubric`, `concurrency`, `latency_boundary`, `input_tokens_per_attempt` and `output_tokens_per_attempt` from `calculate()["workload"]` in the same checkout. |
| `price_basis` | Two-letter `market`, explicit delivery `destination`, three-letter `currency`, UTC `as_of` date, review `method`, and `electricity` as null or an object with `revision` and `per_kwh`. |
| `options` | Any subset of `keep`, `upgrade`, `rental` and `api` with reviewed inputs. Each includes a `configuration` name, exact `configuration_revision`, and `service` and `operation` records or nulls. Each local option also includes `purchase` or null. |
| `citations` | A map with `scenario`, plus one key per supplied input such as `electricity`, `keep.purchase`, `keep.service` or `api.operation`. Each contains an approved public HTTPS `locator` and the corresponding input `revision`. |

A service record includes `revision`, `quality` and `privacy` reviews
(`pass` or `miss`), same-task `sample_count`, `accepted_count`, and
`p95_latency_ms`, `seconds_per_attempt`, `available_hours` and
`utilization`. Acceptance probability uses the exact sample counts. The
service needs reviewed completed requests for the pinned task and latency
boundary. Use the applicable `operation` field names from
[the accounting example](illustrative.json). Rates and decimal quantities
use decimal strings. Rental and API inputs include the applicable billing
and eligibility terms.

A reviewed local `purchase` includes the itemized `parts` and `revision`,
plus a regional `price_release` UUID, `scope_id`, and `condition`. Configure
`FASTEST_DATABASE_URL` to read these quotes. An eligible landed whole-build
offer must match the setup revision, market, date, destination, currency and
condition. The reviewed part values must add to that quote. Partial inputs
can appear with unavailable totals. A revoked quote no longer supplies the
purchase values or their citations.

The server reads the file on each evidence calculation. Replace it atomically
after review. Set the authorization status to `withdrawn` to remove the
scenario from public calculations. Expired authorization also removes it.
Links to the reviewed output pin the result revision for the chosen demand
and horizon. A changed or retired revision returns 404 on replay.

## Configure reviewed tariff references

Start the release server from `production/` with the optional reference
manifest.

```sh
python3 -B -m fastest_release serve --cost-tariff-references /private/reviewed-tariffs.json
```

Costs shows approved components in the **Public evidence** view. The same
`tariff_references` block appears in `/costs.json` and `/api/v1/calculator`.
The references keep their source currency, billing units, effective dates
and eligibility terms. A workload comparison still requires separate approved
inputs through `--cost-scenario`. For example, a time-of-use rate requires an
energy allocation by band, and a quoted rental base rate requires evidence
of applicable billing charges and same-task service capacity.

Use an operator-reviewed JSON object with these fields.

| Field | Required contents |
| --- | --- |
| `schema_version`, `revision` | Integer 1 and an immutable manifest revision. Change it when updating the reviewed components. |
| `authorization` | The same `status`, `decision_id` and UTC `expires_at` fields as the reviewed scenario. This decision covers every approved component in the manifest. |
| `references` | Up to 128 separately cited tariff components reviewed for public display. Each has a unique `id`. |

Each component has `id`, `kind`, `provider`, `offering`, `revision`,
`market`, `region`, `currency`, `amount`, `unit`, `component`,
`effective_from`, `effective_until`, `qualification`, `source`,
`checked_at` and `citation`. For PostgreSQL-derived references, join the
candidate to its captured source probe and batch in the private intake.
Keep the original amount as a decimal string and the original billing unit
from [the tariff intake schema](../fastest_intake/README.md). Copy each
known effective date as `YYYY-MM-DD` or use null for an unspecified date.
Use a public source name for `source` and the batch's check time in UTC
`YYYY-MM-DDTHH:MM:SSZ` for `checked_at`. The `citation` object contains
the exact public HTTPS `locator` and the component's tariff `revision`.
Include public fields approved for export and keep raw intake packets
private.

The server reads the manifest on each evidence request. Replace it
atomically after review. Effective dates apply from the start date through
the day before the end date, evaluated against the current UTC date.
Remove individual components by replacing the manifest. Setting
`authorization.status` to `withdrawn` or reaching `expires_at` removes
the entire block. Exact links return 404 once their displayed revision is
retired.

## Accounting assumptions

- Service uses one simultaneous request. Required attempts round up from the requested accepted tasks divided by the expected acceptance rate. Rejected attempts consume time, energy and API tokens. Capacity uses the allowed active hours, time per attempt and acceptance rate, rounding down to whole attempts and accepted tasks. Active hours must fit the utilization limit and, for rental, leave room for paid idle. Quality, privacy, p95 completion latency and capacity must all qualify for a comparable operating cost.
- A reused part contributes to whole-build replacement value and uses zero current cash. The GPU-only value covers all GPU units. The example prices use one currency and assumed landed amounts for the stated market. Local load and idle power use the system wall boundary. External cooling adds a separate share of IT energy. Local idle applies to the balance of powered hours. Off hours consume zero under this model.
- The illustrated rental tariff prorates active and paid idle hours, then adds monthly storage and transfer. The API tariff separately meters uncached and cached input, all output tokens and a fixed fee. Cloud options have zero hardware purchase, setup and residual cash flows in this model.
- Nominal cost adds upfront and monthly costs, then subtracts residual value only at the selected terminal month. Discounted cost uses monthly end-of-period cash flows and the versioned effective monthly rate. The assumed terminal residual is held fixed when the horizon changes. Simple payback divides positive incremental upfront cash by positive recurring savings and omits the terminal residual. Zero upfront can yield immediate payback if recurring savings are positive. The result distinguishes payback beyond the horizon, infeasible service, unknown inputs and nonpositive savings.
- Sensitivity changes one input at a time to 50% and 150% of its base value. Monthly accepted tasks round down for the low case and up for the high case, with one as the lower bound. Each case reruns the same service and cost equations.

Run `python3 -B -m unittest discover -s tests -p 'test_cost.py'` from `production/` for the calculation and HTTP checks.
