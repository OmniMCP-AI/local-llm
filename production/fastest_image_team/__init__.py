"""Model local, cloud and hybrid image plans against one aggregate workload."""

from copy import deepcopy
from decimal import Decimal, localcontext
from math import ceil, floor

from fastest_cost import ACCOUNTING, _decimal_strings, simple_cash_payback
from fastest_pilot_bundle import digest, json_text

from .intake import LANES, SERVICE_FLAGS, validate


METHOD = "same-image-team-workload-v1"
PILOT = {
    "revision": "two-machine-image-pilot-v1",
    "path": "production/fastest_image/plan.json",
    "qualification": "Solo pilot measurements cannot establish team-load rates, commercial rights or cloud equivalence.",
}
MODEL = {
    "peak": "One simultaneous peak cohort is included in monthly demand. Each lane runs full concurrency waves, "
            "after its stated peak queue delay. Labor starts after both lanes finish, "
            "using the available peak reviewers in parallel. Peak estimates use the monthly capacity limits.",
    "capacity": "Monthly compute hours are net usable hours for each lane. Yield is the share of attempts accepted "
                "under the common rubric. Estimate attempts by rounding up demand divided by yield. "
                "All attempts incur review and rejections incur additional handling.",
    "allocation": "Hybrid routes a fixed local share of monthly and peak accepted demand, rounded down. "
                  "Unused capacity in one lane does not replace the other lane's assignment.",
    "financial": "Monthly fees, usage, storage, transfer and incremental labor cash are included. "
                 "Loaded labor is valued separately. Simple cash payback excludes terminal value, "
                 "financing and the time value of money.",
    "sensitivity": "Each sensitivity case changes one assumption by 25%. Volume changes monthly and peak demand "
                   "together, rounding up to whole images. Yield is capped at 100%. Billed storage and transfer "
                   "quantities stay fixed. Sensitivity cases are hypothetical.",
}


def _lane_service(inputs, workload, monthly, peak):
    result = {"status": "unknown", "monthly_accepted_target": monthly, "peak_accepted_target": peak}
    evidence = inputs["service"]
    if evidence is None or evidence["scope"] is None:
        return {**result, "reasons": ["missing_scoped_service_evidence"]}
    scope = evidence["scope"]
    if scope["workflow"] != workload["workflow"] or scope["workload_revision"] != workload["revision"]:
        return {**result, "reasons": ["workflow_or_workload_scope_mismatch"]}
    failures = [f"{flag}_unmet" for flag in SERVICE_FLAGS if evidence[flag] == "fail"]
    unknowns = [f"{flag}_unknown" for flag in SERVICE_FLAGS if evidence[flag] == "unknown"]
    yield_rate = Decimal(scope["accepted_yield"])
    if not yield_rate and monthly:
        failures.append("accepted_yield_zero")
    if failures or unknowns:
        return {**result, "status": "infeasible" if failures else "unknown", "reasons": failures + unknowns}

    concurrency = scope["concurrency"]
    wave_seconds = Decimal(scope["wave_seconds"])
    queue_hours = Decimal(scope["peak_queue_hours"]) if peak else Decimal(0)
    monthly_attempts = ceil(monthly / yield_rate) if monthly else 0
    peak_attempts = ceil(peak / yield_rate) if peak else 0
    monthly_waves = floor(Decimal(scope["monthly_compute_hours"]) * 3600 / wave_seconds)
    monthly_capacity = floor(monthly_waves * concurrency * yield_rate)
    wave_count = ceil(Decimal(peak_attempts) / concurrency)
    review = Decimal(scope["review_minutes_per_attempt"])
    rework = Decimal(scope["rework_minutes_per_rejected"])
    rejected = monthly_attempts - monthly
    reasons = ["monthly_compute_capacity_unmet"] if monthly_capacity < monthly else []
    return {
        **result, "status": "infeasible" if reasons else "feasible", "reasons": reasons,
        "monthly_attempts": monthly_attempts, "monthly_rejected": rejected,
        "monthly_capacity_accepted": monthly_capacity, "peak_attempts": peak_attempts,
        "peak_waiting_attempts": peak_attempts if queue_hours else max(0, peak_attempts - concurrency),
        "peak_queue_hours": queue_hours, "peak_generation_seconds": queue_hours * 3600 + wave_count * wave_seconds,
        "monthly_review_minutes": monthly_attempts * review,
        "monthly_rework_minutes": rejected * rework,
        "peak_labor_minutes": peak_attempts * review + (peak_attempts - peak) * rework,
    }


def _cost(inputs, lanes, labor_hours, workload, months):
    cash_labor = labor_hours * Decimal(inputs["labor"]["cash_hourly"])
    loaded_labor = labor_hours * Decimal(inputs["labor"]["loaded_hourly"])
    charges = {}
    for key, lane in lanes.items():
        if (rate := inputs["lanes"][key]["cost"]) is None:
            return None
        charges[key] = {
            "upfront_cash": Decimal(rate["upfront_cash"]),
            "fixed": Decimal(rate["fixed_monthly_cash"]),
            "attempts": lane["monthly_attempts"] * Decimal(rate["cash_per_attempt"]),
            "storage": Decimal(rate["storage_gb_month"]) * Decimal(rate["cash_per_gb_month"]),
            "transfer": Decimal(rate["transfer_gb"]) * Decimal(rate["cash_per_gb"]),
        }
    upfront = sum(row["upfront_cash"] for row in charges.values())
    operations = sum(sum(value for key, value in row.items() if key != "upfront_cash") for row in charges.values())
    recurring_cash = operations + cash_labor
    horizon_cost = upfront + months * (operations + loaded_labor)
    return {
        "lanes": charges, "upfront_cash": upfront, "monthly_cash": recurring_cash,
        "monthly_labor_cash": cash_labor, "monthly_loaded_labor": loaded_labor,
        "horizon_cash": upfront + months * recurring_cash, "horizon_loaded_cost": horizon_cost,
        "loaded_cost_per_accepted": horizon_cost / (months * workload["monthly_accepted"]),
    }


def _plan(plan_id, inputs, workload, months):
    share = {"local": Decimal(1), "cloud": Decimal(0)}.get(plan_id)
    if plan_id == "hybrid":
        share = Decimal(inputs["local_share"])
    monthly_local = floor(workload["monthly_accepted"] * share)
    peak_local = floor(workload["peak_accepted"] * share)
    allocations = {"local": (monthly_local, peak_local),
                   "cloud": (workload["monthly_accepted"] - monthly_local, workload["peak_accepted"] - peak_local)}
    lanes = {key: _lane_service(inputs["lanes"][key], workload, *allocations[key]) for key in LANES[plan_id]}
    reasons = [f"{key}.{reason}" for key, lane in lanes.items() for reason in lane["reasons"]]
    result = {
        "status": "infeasible" if any(lane["status"] == "infeasible" for lane in lanes.values()) else "unknown",
        "reasons": reasons, "lanes": lanes, "peak_accepted_by_deadline": None, "cost": None,
    }
    if any("peak_generation_seconds" not in lane for lane in lanes.values()):
        return result

    labor = inputs["labor"]
    reviewers = labor["peak_reviewers"]
    monthly_labor_minutes = sum(lane["monthly_review_minutes"] + lane["monthly_rework_minutes"] for lane in lanes.values())
    peak_labor_seconds = 60 * sum(lane["peak_labor_minutes"] for lane in lanes.values())
    generation_seconds = max(lane["peak_generation_seconds"] for lane in lanes.values())
    deadline_seconds = Decimal(workload["deadline_hours"]) * 3600
    monthly_labor_seconds = Decimal(labor["monthly_hours"]) * 3600
    if monthly_labor_minutes * 60 > monthly_labor_seconds:
        reasons.append("monthly_labor_capacity_unmet")
    if generation_seconds * reviewers + peak_labor_seconds > deadline_seconds * reviewers:
        reasons.append("peak_deadline_unmet")
    deliverable = 0
    for key, lane in lanes.items():
        scope = inputs["lanes"][key]["service"]["scope"]
        review_reserved = (deadline_seconds - lane["peak_queue_hours"] * 3600) * reviewers - peak_labor_seconds
        waves = floor(max(Decimal(0), review_reserved) / (Decimal(scope["wave_seconds"]) * reviewers))
        attempts = waves * scope["concurrency"]
        accepted = floor(attempts * Decimal(scope["accepted_yield"]))
        deliverable += min(lane["peak_accepted_target"], lane["monthly_capacity_accepted"], accepted)
    result.update(
        status="infeasible" if reasons else "feasible",
        peak_accepted_by_deadline=deliverable if peak_labor_seconds <= monthly_labor_seconds else 0,
        peak_completion_hours=(generation_seconds + peak_labor_seconds / reviewers) / 3600,
        peak_labor_elapsed_hours=peak_labor_seconds / (reviewers * 3600),
        monthly_labor_hours=monthly_labor_minutes / 60,
    )
    if result["status"] == "feasible":
        result["cost"] = _cost(inputs, lanes, result["monthly_labor_hours"], workload, months)
        if result["cost"] is None:
            reasons.append("missing_price_evidence")
    return result


def _payback(plans, months, can_support):
    rows = {}
    cloud = plans["cloud"]
    for key in ("local", "hybrid"):
        plan = plans[key]
        costs = (plan["cost"], cloud["cost"])
        if "infeasible" in (plan["status"], cloud["status"]):
            status, savings, time = "infeasible_service", None, None
        elif None in costs:
            status, savings, time = "unknown_inputs", None, None
        else:
            left, right = costs
            status, savings, time = simple_cash_payback(
                left["upfront_cash"], left["monthly_cash"], right["upfront_cash"], right["monthly_cash"], months,
            )
        rows[key] = {
            "baseline": "cloud", "status": status, "months": time, "monthly_cash_savings": savings,
            "supports_payback_claim": can_support and status == "within_horizon",
        }
    return rows


def _evaluate(data, can_support):
    plans = {key: _plan(key, data["plans"][key], data["workload"], data["months"]) for key in LANES}
    return plans, _payback(plans, data["months"], can_support)


def _sensitivity(data):
    cases = []
    for driver in ("monthly_and_peak_demand", "peak_queue_delay", "accepted_yield", "attempt_tariff"):
        for factor in (Decimal("0.75"), Decimal("1.25")):
            scenario = deepcopy(data)
            if driver == "monthly_and_peak_demand":
                for key in ("monthly_accepted", "peak_accepted"):
                    scenario["workload"][key] = max(1, ceil(scenario["workload"][key] * factor))
            for plan in scenario["plans"].values():
                for lane in plan["lanes"].values():
                    scope = lane["service"]["scope"] if lane["service"] is not None else None
                    if scope is not None and driver == "peak_queue_delay":
                        scope["peak_queue_hours"] = Decimal(scope["peak_queue_hours"]) * factor
                    if scope is not None and driver == "accepted_yield":
                        scope["accepted_yield"] = min(Decimal(1), Decimal(scope["accepted_yield"]) * factor)
                    if lane["cost"] is not None and driver == "attempt_tariff":
                        lane["cost"]["cash_per_attempt"] = Decimal(lane["cost"]["cash_per_attempt"]) * factor
            plans, payback = _evaluate(scenario, False)
            cases.append({
                "driver": driver, "factor": factor, "plans": {
                    key: {
                        "status": plan["status"], "reasons": plan["reasons"],
                        "peak_accepted_by_deadline": plan["peak_accepted_by_deadline"],
                        "peak_completion_hours": plan.get("peak_completion_hours"),
                        "monthly_compute_capacity_accepted": {
                            lane: values.get("monthly_capacity_accepted") for lane, values in plan["lanes"].items()
                        },
                        "horizon_cash": plan["cost"]["horizon_cash"] if plan["cost"] else None,
                    }
                    for key, plan in plans.items()
                }, "payback": payback,
            })
    return cases


def calculate(data=None):
    """Return a versioned JSON-compatible estimate from consented aggregate assumptions."""
    if data is not None:
        validate(data)
    identity = {
        "result_type": "image-team-comparison", "schema_version": 1, "method": METHOD,
        "estimate_kind": data["kind"] if data is not None else "unavailable",
        "inputs": deepcopy(data), "model": MODEL.copy(), "pilot_reference": PILOT.copy(),
    }
    with localcontext(ACCOUNTING):
        if data is None:
            plans = {
                key: {"status": "unknown", "reasons": ["missing_consented_team_scenario"], "lanes": {},
                      "peak_accepted_by_deadline": None, "cost": None}
                for key in LANES
            }
            payback, sensitivity = _payback(plans, 0, False), []
        else:
            plans, payback = _evaluate(data, data["kind"] == "consented")
            sensitivity = _sensitivity(data)
        return {
            **identity, "revision": "v1-" + digest(json_text(identity)),
            **_decimal_strings({"plans": plans, "payback": payback, "sensitivity": sensitivity}),
        }
