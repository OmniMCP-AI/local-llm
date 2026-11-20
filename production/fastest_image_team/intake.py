"""Validate publishable aggregate assumptions before modeling team economics."""

from datetime import date
from decimal import Decimal
import re


WORKFLOW_KEYS = ("workflow_sha256", "artifact_sha256", "runtime_revision", "rubric_revision")
LANES = {"local": ("local",), "cloud": ("cloud",), "hybrid": ("local", "cloud")}
SERVICE_FLAGS = ("quality", "privacy", "commercial_rights")


def fields(value, keys, name):
    if not isinstance(value, dict) or value.keys() != set(keys.split()):
        raise ValueError(f"{name} must contain exactly these fields: {keys}.")
    return value


def label(value, name, pattern=r"[^\x00-\x1f\x7f]{1,250}"):
    if not isinstance(value, str) or not value.strip() or re.fullmatch(pattern, value) is None:
        raise ValueError(f"Invalid {name}.")
    return value


def quantity(value, name, maximum="1000000000", *, minimum="0"):
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,10}(\.[0-9]{1,9})?", value):
        number = Decimal(value)
        if Decimal(minimum) <= number <= Decimal(maximum):
            return number
    raise ValueError(f"{name} must be a decimal string from {minimum} to {maximum}.")


def count(value, name, maximum, minimum=1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}.")
    return value


def workflow(value, name):
    fields(value, " ".join(WORKFLOW_KEYS), name)
    for key, item in value.items():
        pattern = r"[a-f0-9]{64}" if key.endswith("sha256") else r"[^\x00-\x1f\x7f]{1,250}"
        label(item, f"{name}.{key}", pattern)


def source(value, name, kind):
    fields(value, "reference revision kind", name)
    label(value["reference"], f"{name}.reference")
    label(value["revision"], f"{name}.revision")
    if value["kind"] != kind:
        raise ValueError(f"{name}.kind must be {kind}.")


def validate_service(value, name, kind):
    fields(value, "scope quality privacy commercial_rights privacy_conditions service_evidence", name)
    for flag in SERVICE_FLAGS:
        if value[flag] not in ("pass", "fail", "unknown"):
            raise ValueError(f"{name}.{flag} must be pass, fail or unknown.")
    label(value["privacy_conditions"], f"{name}.privacy_conditions")
    source(value["service_evidence"], f"{name}.service_evidence", kind)
    if (scope := value["scope"]) is None:
        return
    fields(scope, "workflow workload_revision concurrency wave_seconds monthly_compute_hours peak_queue_hours "
           "accepted_yield review_minutes_per_attempt rework_minutes_per_rejected", f"{name}.scope")
    workflow(scope["workflow"], f"{name}.scope.workflow")
    label(scope["workload_revision"], f"{name}.scope.workload_revision")
    count(scope["concurrency"], f"{name}.scope.concurrency", 1024)
    quantity(scope["wave_seconds"], f"{name}.scope.wave_seconds", "2678400", minimum="0.000001")
    quantity(scope["accepted_yield"], f"{name}.scope.accepted_yield", "1")
    for field in ("monthly_compute_hours", "peak_queue_hours"):
        quantity(scope[field], f"{name}.scope.{field}", "744")
    for field in ("review_minutes_per_attempt", "rework_minutes_per_rejected"):
        quantity(scope[field], f"{name}.scope.{field}", "1440")


def validate_cost(value, name, kind):
    if value is None:
        return
    money = "upfront_cash fixed_monthly_cash cash_per_attempt storage_gb_month cash_per_gb_month transfer_gb cash_per_gb"
    fields(value, money + " price_evidence", name)
    source(value["price_evidence"], f"{name}.price_evidence", kind)
    for field in money.split():
        quantity(value[field], f"{name}.{field}")


def validate(data):
    fields(data, "schema_version revision kind workload currency market price_as_of months plans", "scenario")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Use image team scenario schema version 1.")
    if data["kind"] not in ("consented", "illustrative"):
        raise ValueError("Scenario kind must be consented or illustrative.")
    kind = "reviewed" if data["kind"] == "consented" else "fictional"
    for field in ("revision", "market"):
        label(data[field], field)
    label(data["currency"], "currency", r"[A-Z]{3}")
    date.fromisoformat(label(data["price_as_of"], "price_as_of", r"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
    count(data["months"], "months", 120)
    workload = fields(data["workload"], "team_size revision source public_aggregate_allowed workflow "
                      "monthly_accepted peak_accepted deadline_hours privacy_requirement", "workload")
    if workload["team_size"] != 10 or type(workload["team_size"]) is not int:
        raise ValueError("The image scenario is scoped to a ten-person team.")
    if workload["public_aggregate_allowed"] is not True:
        raise ValueError("Publication requires consent to release the aggregate workflow and workload.")
    source(workload["source"], "workload.source", kind)
    label(workload["revision"], "workload.revision")
    workflow(workload["workflow"], "workload.workflow")
    target = count(workload["monthly_accepted"], "monthly_accepted", 1_000_000)
    count(workload["peak_accepted"], "peak_accepted", target)
    quantity(workload["deadline_hours"], "deadline_hours", "744", minimum="0.000001")
    label(workload["privacy_requirement"], "workload.privacy_requirement")
    for plan_id, plan in fields(data["plans"], "local cloud hybrid", "plans").items():
        fields(plan, "lanes labor" + (" local_share" if plan_id == "hybrid" else ""), plan_id)
        if plan_id == "hybrid":
            quantity(plan["local_share"], "local_share", "0.999999999", minimum="0.000000001")
        name = f"{plan_id}.labor"
        labor = fields(plan["labor"], "monthly_hours peak_reviewers loaded_hourly cash_hourly evidence", name)
        count(labor["peak_reviewers"], f"{name}.peak_reviewers", workload["team_size"])
        quantity(labor["monthly_hours"], f"{name}.monthly_hours", str(workload["team_size"] * 744))
        loaded = quantity(labor["loaded_hourly"], f"{name}.loaded_hourly")
        quantity(labor["cash_hourly"], f"{name}.cash_hourly", str(loaded))
        source(labor["evidence"], f"{name}.evidence", kind)
        for lane_id, lane in fields(plan["lanes"], " ".join(LANES[plan_id]), f"{plan_id}.lanes").items():
            name = f"{plan_id}.{lane_id}"
            fields(lane, "configuration service cost", name)
            label(lane["configuration"], f"{name}.configuration")
            if lane["service"] is not None:
                validate_service(lane["service"], f"{name}.service", kind)
            validate_cost(lane["cost"], f"{name}.cost", kind)
