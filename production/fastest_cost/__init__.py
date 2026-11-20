"""Deterministic public text cost comparison for one shared workload."""

from copy import deepcopy
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from math import ceil, floor
import json
from pathlib import Path
import re

from fastest_text.__main__ import PLAN_PATH

METHOD = "same-text-workload-cost-v1"
OPTION_LABELS = {"keep": "Keep machine", "upgrade": "Upgrade", "rental": "Rent GPU", "api": "Use API"}
PUBLIC_FIELDS = frozenset(("scenario", "monthly_accepted", "months"))
LOCAL_MONTHLY_FIELDS = ("load_kwh", "idle_kwh", "cooling_kwh", "it_electricity", "external_cooling", "maintenance")
MONTHLY_FIELDS = {
    "keep": LOCAL_MONTHLY_FIELDS,
    "upgrade": LOCAL_MONTHLY_FIELDS,
    "rental": ("paid_idle_hours", "billed_hours", "compute", "storage", "transfer"),
    "api": ("uncached_input_tokens", "cached_input_tokens", "output_tokens", "uncached_input_cost",
            "cached_input_cost", "output_cost", "fixed_fee"),
}
WORKLOAD_REVISION = "zh-copy-economics-v1"
DEFAULT_ACCEPTED = 1800
DEFAULT_MONTHS = 24
MAX_ACCEPTED = 100_000_000
MAX_MONTHS = 120
MONTHLY_DISCOUNT_RATE = Decimal("0.005")
MILLION = 1_000_000
ACCOUNTING = Context(prec=40)


def _bound(selection, key, default, maximum):
    value = str(selection.get(key, default))
    if not re.fullmatch(r"[0-9]{1,9}", value) or not 1 <= int(value) <= maximum:
        raise ValueError(f"{key} must be an integer from 1 to {maximum}.")
    return int(value)


def _decimal_strings(value):
    """Keep counts integral and publish accounting quantities as decimal strings."""
    if isinstance(value, Decimal):
        # This is the export boundary. All calculations retain working precision.
        text = format(value.quantize(Decimal("0.000001")), "f").rstrip("0").rstrip(".")
        return "0" if text in {"0", "-0"} else text
    if isinstance(value, dict):
        return {key: _decimal_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decimal_strings(item) for item in value]
    return value


def _workload():
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    return {
        "id": plan["rubric"]["task_id"], "revision": WORKLOAD_REVISION,
        "label": "Simplified Chinese product-card copy",
        "pilot_revision": plan["id"], "quality_rubric": plan["rubric"]["id"],
        "criteria": plan["rubric"]["criteria"], "prompt": plan["rubric"]["prompt"],
        "quality": "An attempt passes all five criteria before it counts as an accepted task.",
        "privacy": "Use fictional product facts. Remote processing requires approved handling and retention terms.",
        "concurrency": 1,
        "input_tokens_per_attempt": 1024, "output_tokens_per_attempt": 128,
        "token_basis": "Scenario billing estimates per attempt, using the same token mix for all options.",
        "minimum_acceptance_rate": "0.90", "maximum_p95_latency_ms": 25000,
        "latency_boundary": "Client request to completed response at the stated load (p95).",
        "evidence_scope": "The pilot's isolated prefill and decode timings have a different boundary from same-task completion.",
        "source_path": "production/fastest_text/plan.json",
    }


def _scenario(name):
    if name == "illustrative":
        return json.loads(Path(__file__).with_name("illustrative.json").read_text(encoding="utf-8"))
    return {
        "revision": "public-evidence-text-economics-v1",
        "price_basis": {
            "market": "US delivery",
            "currency": "USD", "as_of": None,
            "method": "No approved comparable landed build, tariff or endpoint price is available for this scenario.",
            "source_path": "production/fastest_prices/README.md",
            "electricity": {"revision": None, "per_kwh": None},
        },
        "options": {
            key: {
                "configuration": label,
                "purchase": None,
                "operation": None,
                "service": None,
            }
            for key, label in OPTION_LABELS.items()
        },
    }


def _purchase(option, inputs):
    if option in {"rental", "api"}:
        return {"revision": None, "parts": [], "gpu_only": None, "reused_parts": None,
                "whole_build": None, "upfront": Decimal(0)}
    if inputs is None:
        return {"revision": None, "parts": [], "gpu_only": None, "reused_parts": None,
                "whole_build": None, "upfront": None}
    parts = [{**part, "extended_price": Decimal(part["unit_price"]) * part["quantity"]} for part in inputs["parts"]]
    return {
        "revision": inputs["revision"], "parts": parts,
        "gpu_only": sum((part["extended_price"] for part in parts if part["kind"] == "gpu"), Decimal(0)),
        "reused_parts": sum((part["extended_price"] for part in parts if part["reused"]), Decimal(0)),
        "whole_build": sum(part["extended_price"] for part in parts),
        "upfront": sum((part["extended_price"] for part in parts if not part["reused"]), Decimal(0)),
    }


def _service(inputs, workload, accepted, paid_idle_hours):
    if inputs is None:
        return {
            "status": "unknown", "reasons": ["missing_same_task_service_evidence"], "attempts": None,
            "active_hours": None, "maximum_monthly_accepted": None,
        }
    rate = Decimal(inputs["acceptance_rate"])
    seconds = Decimal(inputs["seconds_per_attempt"])
    available = Decimal(inputs["available_hours"])
    active_budget = min(available * Decimal(inputs["utilization"]), available - paid_idle_hours)
    capacity = floor(floor(max(active_budget, Decimal(0)) * 3600 / seconds) * rate)
    attempts = ceil(Decimal(accepted) / rate)
    active_hours = Decimal(attempts) * seconds / 3600
    reasons = []
    if inputs["quality"] != "pass" or rate < Decimal(workload["minimum_acceptance_rate"]):
        reasons.append("quality_below_target")
    if inputs["privacy"] != "pass":
        reasons.append("privacy_policy_unmet")
    if inputs["p95_latency_ms"] > workload["maximum_p95_latency_ms"]:
        reasons.append("latency_slo_unmet")
    if accepted > capacity:
        reasons.append("insufficient_capacity")
    return {
        "status": "infeasible" if reasons else "feasible", "reasons": reasons,
        "attempts": attempts, "active_hours": active_hours, "maximum_monthly_accepted": capacity,
    }


def _monthly(option, inputs, service, available_hours, price, workload):
    if inputs is None or service["status"] != "feasible":
        return dict.fromkeys((*MONTHLY_FIELDS[option], "recurring_cost"))
    active = service["active_hours"]
    if option in {"keep", "upgrade"}:
        load_kwh = active * Decimal(inputs["load_watts"]) / 1000
        idle_kwh = (available_hours - active) * Decimal(inputs["idle_watts"]) / 1000
        cooling_kwh = (load_kwh + idle_kwh) * Decimal(inputs["external_cooling_ratio"])
        it_electricity = (load_kwh + idle_kwh) * Decimal(price)
        external_cooling = cooling_kwh * Decimal(price)
        maintenance = Decimal(inputs["monthly_maintenance"])
        return {
            "load_kwh": load_kwh, "idle_kwh": idle_kwh, "cooling_kwh": cooling_kwh,
            "it_electricity": it_electricity, "external_cooling": external_cooling,
            "maintenance": maintenance, "recurring_cost": it_electricity + external_cooling + maintenance,
        }
    if option == "rental":
        paid_idle = Decimal(inputs["paid_idle_hours"])
        billed_hours = active + paid_idle
        compute = billed_hours * Decimal(inputs["hourly_rate"])
        storage, transfer = Decimal(inputs["monthly_storage"]), Decimal(inputs["monthly_transfer"])
        return {
            "paid_idle_hours": paid_idle, "billed_hours": billed_hours,
            "compute": compute, "storage": storage, "transfer": transfer,
            "recurring_cost": compute + storage + transfer,
        }

    attempts = service["attempts"]
    input_tokens = attempts * workload["input_tokens_per_attempt"]
    cached = floor(input_tokens * Decimal(inputs["cached_input_ratio"]))
    uncached = input_tokens - cached
    output = attempts * workload["output_tokens_per_attempt"]
    input_cost = uncached * Decimal(inputs["input_per_million"]) / MILLION
    cached_cost = cached * Decimal(inputs["cached_input_per_million"]) / MILLION
    output_cost = output * Decimal(inputs["output_per_million"]) / MILLION
    fee = Decimal(inputs["monthly_fee"])
    return {
        "uncached_input_tokens": uncached, "cached_input_tokens": cached, "output_tokens": output,
        "uncached_input_cost": input_cost, "cached_input_cost": cached_cost, "output_cost": output_cost,
        "fixed_fee": fee, "recurring_cost": input_cost + cached_cost + output_cost + fee,
    }


def _totals(upfront, recurring, residual, months, accepted):
    if upfront is None or recurring is None or residual is None:
        return {"terminal_residual": residual, "nominal_cost": None, "discounted_cost": None,
                "cost_per_accepted_task": None}
    nominal = upfront + months * recurring - residual
    factor = 1 + MONTHLY_DISCOUNT_RATE
    terminal_discount = factor ** -months
    discounted = upfront + recurring * (1 - terminal_discount) / MONTHLY_DISCOUNT_RATE - residual * terminal_discount
    return {
        "terminal_residual": residual, "nominal_cost": nominal, "discounted_cost": discounted,
        "cost_per_accepted_task": nominal / (months * accepted),
    }


def _options(scenario, workload, accepted, months):
    rate = scenario["price_basis"]["electricity"]["per_kwh"]
    options = {}
    for key, inputs in scenario["options"].items():
        purchase = _purchase(key, inputs["purchase"] if key in {"keep", "upgrade"} else None)
        operation = inputs["operation"]
        paid_idle = Decimal(operation["paid_idle_hours"]) if key == "rental" and operation else Decimal(0)
        service_inputs = inputs["service"]
        service = _service(service_inputs, workload, accepted, paid_idle)
        available = Decimal(service_inputs["available_hours"]) if service_inputs else None
        monthly = _monthly(key, operation, service, available, rate, workload)
        residual = Decimal(0)
        if key in {"keep", "upgrade"}:
            residual = Decimal(operation["terminal_residual"]) if operation else None
        options[key] = {
            "label": OPTION_LABELS[key], "service": service, "purchase": purchase, "monthly": monthly,
            "totals": _totals(purchase["upfront"], monthly["recurring_cost"], residual, months, accepted),
        }
    return options


def _payback(options, months):
    comparisons = (("upgrade", "keep"), ("upgrade", "rental"), ("upgrade", "api"),
                   ("keep", "rental"), ("keep", "api"))
    rows = []
    for target, baseline in comparisons:
        left, right = options[target], options[baseline]
        statuses = {left["service"]["status"], right["service"]["status"]}
        savings, payback = None, None
        if "infeasible" in statuses:
            status = "infeasible_service"
        elif any(row["monthly"]["recurring_cost"] is None or row["purchase"]["upfront"] is None
                 for row in (left, right)):
            status = "unknown_inputs"
        else:
            savings = right["monthly"]["recurring_cost"] - left["monthly"]["recurring_cost"]
            if savings <= 0:
                status = "nonpositive_savings"
            else:
                incremental = left["purchase"]["upfront"] - right["purchase"]["upfront"]
                payback = max(incremental, Decimal(0)) / savings
                status = "beyond_horizon" if payback > months else "within_horizon"
        rows.append({"option": target, "baseline": baseline, "status": status,
                     "monthly_savings": savings, "payback_months": payback})
    return rows


def _curve(options, months):
    return [
        {"month": month, **{
            key: (
                row["purchase"]["upfront"] + month * row["monthly"]["recurring_cost"]
                - (row["totals"]["terminal_residual"] if month == months else 0)
                if row["totals"]["nominal_cost"] is not None else None
            )
            for key, row in options.items()
        }}
        for month in range(months + 1)
    ]


def _sensitivity(scenario, workload, accepted, months):
    paths = (
        ("electricity", ("price_basis", "electricity", "per_kwh"), "USD/kWh"),
        ("rental_hourly_rate", ("options", "rental", "operation", "hourly_rate"), "USD/hour"),
        ("api_output_rate", ("options", "api", "operation", "output_per_million"), "USD/M output tokens"),
    )
    cases = [{
        "driver": "monthly_accepted", "unit": "accepted tasks/month",
        "levels": [max(1, accepted // 2), ceil(Decimal(accepted) * Decimal("1.5"))],
    }]
    for driver, path, unit in paths:
        current = scenario
        for key in path:
            current = current.get(key) if current is not None else None
        cases.append({
            "driver": driver, "unit": unit, "path": path,
            "levels": [Decimal(current) * factor if current is not None else None for factor in (Decimal("0.5"), Decimal("1.5"))],
        })

    rows = []
    for case in cases:
        for label, value in zip(("low", "high"), case["levels"]):
            row = {"driver": case["driver"], "unit": case["unit"], "level": label, "value": value, "options": {}}
            if value is not None:
                alternate = scenario
                volume = value if "path" not in case else accepted
                if "path" in case:
                    alternate = deepcopy(scenario)
                    field = alternate
                    for key in case["path"][:-1]:
                        field = field[key]
                    field[case["path"][-1]] = value
                options = _options(alternate, workload, volume, months)
                row["options"] = {
                    key: {"nominal_cost": item["totals"]["nominal_cost"],
                          "service_status": item["service"]["status"], "reasons": item["service"]["reasons"]}
                    for key, item in options.items()
                }
            rows.append(row)
    return rows


def calculate(selection=None):
    """Return the versioned JSON-compatible comparison for public query selectors."""
    selection = {} if selection is None else selection
    if selection.keys() - PUBLIC_FIELDS:
        raise ValueError("Unknown cost parameter.")
    name = selection.get("scenario", "evidence")
    if name not in ("evidence", "illustrative"):
        raise ValueError("Unknown cost scenario.")
    accepted = _bound(selection, "monthly_accepted", DEFAULT_ACCEPTED, MAX_ACCEPTED)
    months = _bound(selection, "months", DEFAULT_MONTHS, MAX_MONTHS)
    scenario = _scenario(name)
    workload = _workload()
    identity = {
        "result_type": "text-workload-cost-comparison", "schema_version": 1, "method": METHOD,
        "scenario": name, "estimate_kind": "illustrative" if name == "illustrative" else "unavailable",
        "inputs": scenario, "workload": workload,
        "assumptions": {"monthly_accepted": accepted, "months": months,
                        "monthly_discount_rate": str(MONTHLY_DISCOUNT_RATE), "hours_per_month": 730},
        "units": {
            "money": scenario["price_basis"]["currency"], "energy": "kWh", "power": "W",
            "accepted_work": "accepted tasks", "time_horizon": "months",
            "service_hours": "hours", "latency": "ms", "token_rates": "per million tokens",
        },
    }
    identity_bytes = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with localcontext(ACCOUNTING):
        options = _options(scenario, workload, accepted, months)
        return {
            **identity, "revision": "v1-" + sha256(identity_bytes).hexdigest(),
            **_decimal_strings({
                "options": options, "payback": _payback(options, months),
                "cumulative_cost": _curve(options, months),
                "sensitivity": _sensitivity(scenario, workload, accepted, months),
            }),
        }
