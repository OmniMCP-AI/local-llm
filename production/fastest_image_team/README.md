# Image team comparison

Compare local, cloud and hybrid plans for one ten-person e-commerce team. Each plan must serve the same monthly volume and deliver the same peak cohort by the same deadline under one workflow and acceptance rubric. No reviewed aggregate team scenario or equivalent commercial service rates are checked in. The default report records that evidence gap. The [two-machine image pilot](../fastest_image/README.md) is a solo protocol reference.

From `production/`, build a report into a new directory.

```sh
python3 -B -m fastest_image_team build /path/to/image-team
python3 -B -m fastest_image_team build /path/to/image-team-example --illustrative
python3 -B -m fastest_image_team build /path/to/image-team-reviewed --scenario /path/to/consented.json
```

Each bundle contains matched HTML, Markdown and versioned typed JSON, plus a SHA-256 manifest. `fastest_image_team.calculate(data)` returns the same JSON-compatible result. Counts are integers. Money, rates and durations use decimal strings, with up to six decimal places on calculated quantities. An unavailable estimate carries a reason or null value. The revision digest identifies the scenario and method assumptions.

## Prepare an aggregate scenario

Use the [fictional example](illustrative.json) as the version 1 field guide. For a real scenario use `kind: consented` and review references of `kind: reviewed`. Each reference identifies a public or publishable evidence record and its revision. Consent must cover publication of all scenario fields. Keep product assets, prompts, account details, individual activity and private records outside the report.

- Record the exact workflow and model artifact digests, runtime revision and acceptance rubric revision. Use a reviewed privacy requirement, monthly accepted target and a peak cohort within it. Record the deadline from peak arrival, in hours.
- In each plan, record the exact configuration and aggregate labor availability, including available person-hours per month and simultaneous reviewers at peak. Record full loaded labor value and the smaller or equal incremental hourly cash actually paid for the workload.
- Give each lane measurements or reviewed estimates scoped to the same workload and workflow at the stated concurrency. Provide effective group completion time for one wave of attempts, net monthly compute hours, start delay from the existing peak queue, accepted yield, review minutes per attempt and rework minutes per rejected attempt. Use an accepted count based on the common rubric. A rejection consumes another attempt and may also consume handling labor. Rework time only covers handling a rejected output because retries already consume wave time and review.
- Set quality, privacy and commercial rights to `pass`, `fail` or `unknown` based on the reviewed evidence. Include storage access, retention and provider reuse conditions where applicable. Use a null service or scope for missing team-load evidence. Unknown or mismatched scope withholds qualification.
- Use one currency and market with dated rates. Record landed hardware and setup in upfront cash, net fixed monthly operating charges, marginal cash per attempt, billed monthly storage and transfer, and their unit rates for each lane. Use null cost when price evidence is unavailable. Enter zero for documented charges that do not apply. For hybrid, enter incremental costs and rates at the allocated load and count shared costs once.

## Read the result

The model estimates peak generation from queued start delay, required attempts and whole concurrency waves. It reserves staffing time after the last lane completes. A wave includes generation and retrieval at its scoped load. The displayed peak accepted count uses that reserved time and expected yield, capped by the routed demand and the monthly capacity limits. The model uses planning yields and assumes divisible review work across available staff.

Monthly compute and labor checks run separately. Hybrid applies a fixed local share to both monthly and peak demand, rounded down to whole accepted images. Spare capacity in one hybrid lane does not cover a shortfall in the other. Required rework and all attempts count toward labor, usage charges and capacity.

Payback compares local and hybrid against the cloud plan using incremental upfront cash and recurring cash savings. Salaried time with no incremental payment contributes to loaded cost only. Both compared plans must qualify on equivalent workflow, quality, rights, privacy, monthly capacity and peak deadline, and have comparable prices. Only a within-horizon result from consented, reviewed inputs supports a conditional cash payback conclusion. The fictional example and sensitivity cases show arithmetic on assumptions.

Sensitivity changes demand, peak queue delay, yield and per-attempt tariff by 25% in either direction, one driver at a time. Both demand counts change together, yield is capped at 100%, and fixed charges and billed storage and transfer amounts stay fixed.

Run `python3 -B -m unittest discover -s tests -p 'test_image_team.py'` from `production/`.
