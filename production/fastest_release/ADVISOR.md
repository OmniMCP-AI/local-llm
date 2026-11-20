# Guided configuration advisor

The read-only advisor evaluates one structured decision in the release service. It replies with an `answer`, a `clarify` response listing the missing selectors, or an `abstain` response with the available checks. It is available in [the public API description](../README.md#query-the-public-release-api).

Run `python3 -B -m fastest_release serve` from `production/` and try these requests.

```sh
curl 'http://127.0.0.1:8000/api/v1/advisor?entry=expert&decode=40&prefill=500&privacy=local-only'
curl 'http://127.0.0.1:8000/api/v1/advisor?decision=cost&monthly_accepted=1800&months=24&privacy=allow-external'
curl 'http://127.0.0.1:8000/api/v1/advisor?decision=cost&scenario=illustrative&monthly_accepted=1800&months=24&privacy=allow-external'
```

- For a configuration, supply minimum decode and prefill rates in tok/s and a `privacy` requirement of `local-only` or `allow-external`. The default entry is `expert`. Supply `machine` with `entry=machine` to evaluate that machine. Supply a maximum landed whole-build price with `entry=budget`. The response carries the pinned market and currency. Use the same revision, priority and optional chart selectors as the wizard.
- For a cost comparison, supply monthly accepted tasks, a horizon in months and a privacy requirement. The default `evidence` scenario can abstain for missing approved same-task service and cost inputs. An explicit `illustrative` scenario uses fictional prices and service assumptions. The response identifies external-processing options and excludes their amounts when the workload must stay local.
- A configuration answer cites a pinned text comparison, the selected run's cell and source revision, and any applicable public privacy review and landed quote identifiers. An abstention retains the relevant goal and gate statuses. Cost answers carry decimal strings from the canonical calculator and cite the workload and assumption revisions. The `replay_url` pins the exact data query. The `wizard` link opens the corresponding page for more detail.

The rules run in the release-serving process. No model or external inference service receives the request. At most one canonical comparison or calculator operation runs for a decision. A configuration read can access the deployment's configured price database. Source locators are untrusted citation data. The endpoint accepts only typed selectors and has no free-text input, arbitrary tool access or write capability. The workload privacy setting describes the requested configuration's processing policy. The advisor request still reaches the release server.

## Scripted evaluation

From `production/`, use Python 3.11 or later.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_advisor.py -v
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B tests/test_advisor.py --report
```

The 20 scripted cases returned nine answers, nine abstentions and two clarifications. Tests compare both paths using identical selectors where the wizard accepts them. The advisor asks for explicit inputs where the wizard can use defaults. In machine mode it evaluates the named machine while the wizard continues to rank the full cohort. The advisor applies local-only to cost options as well.

- All 13 configuration results with complete inputs matched the expected checks and selection scope. The other configuration case asked for the missing prefill threshold and privacy requirement.
- All 18 results backed by a canonical read matched the pinned source references. The case with hostile text preserved the source locator as citation data and used the same supported recommendation and rules disclosure.
- All five cost results with complete inputs replayed at the exact calculator revision. All 10 disclosed nominal totals matched the calculator and recomputed as upfront plus monthly cost times months minus terminal residual for the fixtures. The other cost case asked for monthly accepted volume and horizon.

One Apple silicon development-host run is shown below. Each figure is the median of 25 timed in-process dispatches with alternating order, in microseconds. The baseline dispatch reads the wizard's canonical comparison or calculator response. Timings exclude HTTP transport, rendering, fixture setup, model inference and user interaction.

| Scenario | Advisor outcome | Wizard outcome | Advisor µs | Wizard µs |
| --- | --- | --- | ---: | ---: |
| Decode priority | RTX 4090 | RTX 4090 | 43.3 | 32.9 |
| Prefill priority | Apple M4 | Apple M4 | 43.1 | 33.1 |
| Owned M4 passes | Apple M4 | RTX 4090 ranked first | 45.5 | 34.9 |
| Owned M4 misses decode | Abstain | RTX 4090 ranked first | 45.4 | 34.8 |
| Landed quote at cap | Apple M4 | Apple M4 | 46.5 | 35.0 |
| Landed quote one cent over cap | Abstain | No match | 47.5 | 36.1 |
| Stale price | Abstain | No match | 41.3 | 30.9 |
| Withdrawn price | Abstain | No match | 39.5 | 29.5 |
| External setup fails local requirement | Abstain | No match | 42.5 | 31.7 |
| External setup allowed | Apple M4 | Apple M4 | 42.8 | 32.5 |
| Quality review rejects output | Abstain | No match | 39.7 | 29.4 |
| Planned runs are unmeasured | Abstain | No match | 30.2 | 21.4 |
| Hostile text in source locator | Apple M4 | Apple M4 | 44.2 | 33.0 |
| Prefill and privacy missing | Clarify | Defaults applied | 6.3 | 28.3 |
| Cost volume and horizon missing | Clarify | Defaults applied | 7.8 | 127.9 |
| Public cost evidence unavailable | Abstain | Costs unavailable | 146.6 | 132.9 |
| Explicit illustrative comparison | Four totals | Four totals | 695.8 | 677.7 |
| Local-only illustrative comparison | Two local totals | Four totals | 699.8 | 683.1 |
| Requested volume exceeds capacity | Abstain | Costs unavailable | 544.0 | 525.2 |
| One-month residual exceeds cash cost | Four totals | Four totals | 628.2 | 609.5 |

Use the wizard to inspect alternatives, compare points on the Pareto chart, and read detailed exclusions and benchmark methods. The cost page provides itemized parts and recurring costs, sensitivity, cumulative cash cost and payback.

The cases use synthetic benchmarks and quotes alongside the released missing-evidence scenarios. No live model runs, live tariff checks or human decision pilot were part of this evaluation. The timing results characterize the scripted rules and reader paths on one host.
