"""Write the same comparison values in HTML and Markdown."""

from html import escape

from fastest_image.render import markdown_text


TITLE = "Compare image production for a ten-person team"
INTRO = {
    "unavailable": "No consented team scenario is available. Capacity, cost and cash payback are unknown.",
    "illustrative": "Fictional example. Workload, service, prices and payback illustrate the model.",
    "consented": "Scenario estimates based on the released aggregate workload and scoped evidence.",
}
STATUS = {
    "unknown_inputs": "Unavailable · missing comparable evidence",
    "infeasible_service": "Unavailable · service requirements unmet",
    "nonpositive_savings": "No positive recurring cash savings",
    "beyond_horizon": "Beyond the planning horizon",
    "within_horizon": "Within the planning horizon",
}


def _display(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        return ", ".join(_label(item) for item in value) or "—"
    if type(value) is bool:
        return "Yes" if value else "No"
    return str(value)


def _label(key):
    return key.replace("_", " ").replace(".", " · ").capitalize()


def _inputs(record, prefix=""):
    for key, value in record.items():
        label = f"{prefix} · {_label(key)}" if prefix else _label(key)
        if isinstance(value, dict):
            yield from _inputs(value, label)
        else:
            yield (label, value)


def _payback_rows(payback):
    return [(key.title(), STATUS[row["status"]], row["monthly_cash_savings"], row["months"],
             row["supports_payback_claim"]) for key, row in payback.items()]


def _tables(result):
    plans = result["plans"]
    money = result["inputs"]["currency"] if result["inputs"] else "currency unavailable"
    cost_units = f" ({money})"
    yield "Delivery and economics", ("Metric", "Local", "Cloud", "Hybrid"), [
        ("Service", *(plan["status"].title() for plan in plans.values())),
        ("Reasons", *(plan["reasons"] for plan in plans.values())),
        ("Peak accepted images by deadline", *(plan["peak_accepted_by_deadline"] for plan in plans.values())),
        ("Peak completion estimate (hours)", *(plan.get("peak_completion_hours") for plan in plans.values())),
        ("Monthly labor (person-hours)", *(plan.get("monthly_labor_hours") for plan in plans.values())),
        *((label + cost_units, *((plan["cost"] or {}).get(key) for plan in plans.values()))
          for key, label in (
              ("upfront_cash", "Upfront cash"), ("monthly_cash", "Monthly cash"),
              ("monthly_labor_cash", "Monthly incremental labor cash"),
              ("monthly_loaded_labor", "Monthly loaded labor value"),
              ("horizon_cash", "Horizon cash"), ("horizon_loaded_cost", "Horizon loaded cost"),
              ("loaded_cost_per_accepted", "Loaded cost per accepted image"),
          )),
    ]
    yield "Cash payback versus cloud", ("Plan", "Outcome", "Monthly savings" + cost_units,
                                        "Months", "Supports a payback claim"), _payback_rows(result["payback"])
    if result["sensitivity"]:
        columns = ("Driver", "Factor", "Plan", "Service", "Peak accepted by deadline",
                   "Peak completion (hours)", "Monthly compute capacity by lane", "Horizon cash" + cost_units,
                   "Payback months versus cloud", "Payback outcome")
        rows = []
        for case in result["sensitivity"]:
            for key, plan in case["plans"].items():
                payback = case["payback"].get(key)
                capacity = " · ".join(f"{lane.title()} {_display(accepted)}"
                                      for lane, accepted in plan["monthly_compute_capacity_accepted"].items())
                rows.append((_label(case["driver"]), case["factor"], key.title(), plan["status"].title(),
                             plan["peak_accepted_by_deadline"], plan["peak_completion_hours"], capacity,
                             plan["horizon_cash"],
                             payback["months"] if payback else None, STATUS[payback["status"]] if payback else None))
        yield "Sensitivity", columns, rows

    for key, plan in plans.items():
        for lane, record in plan["lanes"].items():
            yield f"{key.title()} · {lane} lane", ("Service or cost item", "Value"), [
                *_inputs(record),
                *_inputs((plan["cost"] or {}).get("lanes", {}).get(lane, {}), f"Charge {cost_units}"),
            ]
    if result["inputs"]:
        inputs = result["inputs"]
        yield "Scenario and aggregate workload", ("Assumption", "Value"), list(_inputs({
            key: value for key, value in inputs.items() if key != "plans"
        }))
        for key, value in inputs["plans"].items():
            yield f"{key.title()} assumptions", ("Assumption", "Value"), list(_inputs(value))


def render(result):
    introduction = INTRO[result["estimate_kind"]]
    revision = result["revision"]
    footer = (*result["model"].values(), result["pilot_reference"]["qualification"],
              f'Pilot reference {result["pilot_reference"]["path"]}.')
    md = [f"# {TITLE}", introduction, "Comparison revision " + revision,
          "[HTML](image-team.html) · [Typed JSON](image-team.json)"]
    html = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<link rel="alternate" type="application/json" href="image-team.json">',
        f'<title>{TITLE}</title><style>',
        'body{font:1rem/1.5 system-ui,sans-serif;margin:auto;max-width:72rem;padding:1rem;color:#162529}',
        'table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #d8e1e2;',
        'padding:.4rem .6rem;text-align:left;overflow-wrap:anywhere}thead{background:#ecf3f3}',
        'div{overflow-x:auto}code{overflow-wrap:anywhere}</style></head><body><main>',
        f"<h1>{TITLE}</h1><p>{escape(introduction)}</p><p>Comparison revision <code>{escape(revision)}</code></p>",
        '<p><a href="image-team.md">Markdown</a> · <a href="image-team.json">Typed JSON</a></p>',
    ]
    for title, columns, rows in _tables(result):
        md.extend((f"## {title}", "\n".join(
            "| " + " | ".join(markdown_text(_display(item)) for item in row) + " |"
            for row in (columns, ("---",) * len(columns), *rows)
        )))
        headers = "".join(f'<th scope="col">{escape(column)}</th>' for column in columns)
        body = "".join(
            f'<tr><th scope="row">{escape(_display(row[0]))}</th>'
            + "".join(f'<td>{escape(_display(item))}</td>' for item in row[1:]) + '</tr>'
            for row in rows
        )
        html.append(f'<h2>{escape(title)}</h2><div role="region" aria-label="{escape(title)}" tabindex="0">'
                    f'<table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>')
    md.extend(("## Model assumptions", *footer))
    html.extend(("<h2>Model assumptions</h2>", *(f"<p>{escape(item)}</p>" for item in footer), "</main></body></html>"))
    return "\n\n".join(md) + "\n", "\n".join(html) + "\n"
