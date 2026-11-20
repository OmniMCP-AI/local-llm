"""Validate the operator's dated, rights-cleared cost inputs."""

from datetime import date, datetime, timezone
from decimal import Context, Decimal, localcontext
import json
import re
from urllib.parse import urlsplit
from uuid import UUID

from fastest_prices import PriceReleaseNotFound
from fastest_prices.result import eligible_offer
from fastest_release.validation import keys, plain_text, valid_expiry


WORKLOAD_FIELDS = ("id", "revision", "quality_rubric", "concurrency", "latency_boundary",
                   "input_tokens_per_attempt", "output_tokens_per_attempt")
LOCAL = {"keep", "upgrade"}
LOCAL_FIELDS = "load_watts idle_watts external_cooling_ratio monthly_maintenance terminal_residual"
OPERATION_FIELDS = {
    "keep": LOCAL_FIELDS,
    "upgrade": LOCAL_FIELDS,
    "rental": "hourly_rate paid_idle_hours monthly_storage monthly_transfer",
    "api": "input_per_million cached_input_per_million output_per_million cached_input_ratio monthly_fee",
}
CONDITIONS = ("new", "used", "refurbished", "open_box")


class CostInputError(ValueError):
    """The operator's reviewed scenario cannot be loaded safely."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def revision(value):
    require(plain_text(value) and len(value) <= 160, "Missing or invalid input revision.")


def decimal(value, field, minimum=0, maximum=10**10):
    require(isinstance(value, str) and re.fullmatch(r"(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,8})?", value)
            and minimum <= Decimal(value) <= maximum, f"Invalid reviewed value for {field}.")


def canonical_uuid(value):
    return isinstance(value, str) and str(UUID(value)) == value


def is_public_locator(value):
    if not plain_text(value) or any(character in value for character in "\\<>") or any(map(str.isspace, value)):
        return False
    parts = urlsplit(value)
    return parts.scheme == "https" and parts.hostname and parts.username is None and parts.port != 0


def validate_service(service):
    keys(service, "revision quality privacy p95_latency_ms seconds_per_attempt sample_count accepted_count "
         "available_hours utilization", "cost service")
    require(service["quality"] in ("pass", "miss") and service["privacy"] in ("pass", "miss"),
            "Review quality and privacy for the pinned service.")
    attempts, accepted = service["sample_count"], service["accepted_count"]
    require(type(attempts) is int and type(accepted) is int and 1 <= accepted <= attempts <= 1_000_000,
            "Invalid same-task service sample counts.")
    require(type(service["p95_latency_ms"]) is int and 1 <= service["p95_latency_ms"] <= 3_600_000,
            "Invalid p95 completion latency.")
    decimal(service["seconds_per_attempt"], "seconds_per_attempt", Decimal("0.00000001"), 3600)
    decimal(service["available_hours"], "available_hours", Decimal("0.00000001"), 730)
    decimal(service["utilization"], "utilization", Decimal("0.00000001"), 1)
    with localcontext(Context(prec=40)):
        service["acceptance_rate"] = str(Decimal(accepted) / attempts)


def validate_operation(option, operation):
    external_fields = " eligibility billing" if option not in LOCAL else ""
    numeric = OPERATION_FIELDS[option].split()
    keys(operation, "revision " + OPERATION_FIELDS[option] + external_fields, "cost operation")
    for field in numeric:
        bound = 1 if field == "cached_input_ratio" else 730 if field == "paid_idle_hours" else 10**10
        decimal(operation[field], field, maximum=bound)
    if external_fields:
        require(all(plain_text(operation[field]) for field in external_fields.split()),
                "External tariffs require billing and eligibility terms.")


def validate_purchase(purchase):
    keys(purchase, "revision parts price_release scope_id condition", "cost purchase")
    require(canonical_uuid(purchase["price_release"]) and plain_text(purchase["scope_id"])
            and purchase["condition"] in CONDITIONS, "A cost purchase requires a pinned whole-build price release.")
    parts = purchase["parts"]
    require(isinstance(parts, list) and 1 <= len(parts) <= 64, "Provide the reviewed, itemized whole build.")
    for part in parts:
        keys(part, "sku kind condition quantity unit_price reused", "cost part")
        require(plain_text(part["sku"]) and plain_text(part["kind"]) and part["condition"] in CONDITIONS
                and type(part["quantity"]) is int and 1 <= part["quantity"] <= 128
                and type(part["reused"]) is bool, "Invalid reviewed BOM part.")
        decimal(part["unit_price"], "unit_price")
    require(len({part["sku"] for part in parts}) == len(parts), "Duplicate reviewed BOM part.")


def match_purchase(purchase, price_basis, config_revision, price_reader, now):
    if price_reader is None:
        return None
    identifier = purchase["price_release"]
    try:
        price = price_reader(identifier)
    except PriceReleaseNotFound:
        return None
    if (price["status"] != "published" or price.get("release_id") != identifier
            or price.get("data_class") != "authorized_observations" or price.get("adapter_status") != "fresh"
            or price.get("condition") != purchase["condition"]
            or any(price.get(field) != price_basis[field] for field in ("market", "destination", "currency", "as_of"))
            or price.get("scope") != {"kind": "whole_build", "id": purchase["scope_id"], "revision_id": config_revision}):
        return None
    with localcontext(Context(prec=40)):
        total = sum(Decimal(part["unit_price"]) * part["quantity"] for part in purchase["parts"])
    matches = [offer for offer in price["offers"] if offer["latest_for_listing"] and offer["freshness"] == "fresh"
               and offer.get("availability", "available") == "available"
               and (not offer.get("expires_at") or datetime.fromisoformat(offer["expires_at"]) > now)
               and eligible_offer(offer) and Decimal(offer["landed_price"]) == total]
    if not matches:
        return None
    offer = min(matches, key=lambda entry: (entry["listing_id"], entry["source_locator"]))
    return {"locator": offer["source_locator"], "revision": identifier}


def read_reviewed(path, workload, empty, price_reader):
    try:
        return _read_reviewed(json.loads(path.read_text(encoding="utf-8")), workload, empty, price_reader)
    except (OSError, ValueError) as error:
        raise CostInputError(f"Invalid reviewed cost scenario: {error}") from error


def _read_reviewed(record, workload, empty, price_reader):
    keys(record, "schema_version revision authorization workload price_basis options citations", "reviewed cost scenario")
    require(type(record["schema_version"]) is int and record["schema_version"] == 1, "Unsupported cost schema version.")
    authorization = record["authorization"]
    keys(authorization, "status decision_id expires_at", "cost authorization")
    require(authorization["status"] in ("approved", "withdrawn") and canonical_uuid(authorization["decision_id"])
            and valid_expiry(authorization["expires_at"]), "Invalid cost publication authorization.")
    now = datetime.now(timezone.utc)
    if authorization["status"] == "withdrawn" or datetime.fromisoformat(authorization["expires_at"]) <= now:
        return None
    require(record["workload"] == {field: workload[field] for field in WORKLOAD_FIELDS},
            "The cost workload must match the pinned task, rubric, token mix and completion boundary.")

    basis = record["price_basis"]
    keys(basis, "market destination currency as_of method electricity", "cost price basis")
    require(re.fullmatch(r"[A-Z]{2}", str(basis["market"])) and re.fullmatch(r"[A-Z]{3}", str(basis["currency"]))
            and all(plain_text(basis[field]) for field in ("destination", "method"))
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", str(basis["as_of"]))
            and date.fromisoformat(basis["as_of"]) <= now.date(), "Invalid dated market or currency for cost inputs.")

    citations = record["citations"]
    require(isinstance(citations, dict), "Cost citations must be scoped to their input.")
    expected = {"scenario": record["revision"]}
    electricity = basis["electricity"]
    if electricity is None:
        basis["electricity"] = empty["price_basis"]["electricity"]
    else:
        keys(electricity, "revision per_kwh", "electricity tariff")
        decimal(electricity["per_kwh"], "per_kwh")
        expected["electricity"] = electricity["revision"]

    options = record["options"]
    require(isinstance(options, dict) and options and options.keys() <= OPERATION_FIELDS.keys(), "Unknown cost options.")
    purchase_citations = {}
    for option, data in options.items():
        keys(data, "configuration configuration_revision service operation" + (" purchase" if option in LOCAL else ""),
             "cost option")
        require(plain_text(data["configuration"]), "A reviewed cost option needs a named configuration.")
        revision(data["configuration_revision"])
        for group, validator in (("service", validate_service), ("operation", lambda item: validate_operation(option, item))):
            source = data[group]
            if source is not None:
                validator(source)
                expected[f"{option}.{group}"] = source["revision"]
        purchase = data.get("purchase")
        if purchase is not None:
            validate_purchase(purchase)
            scope = f"{option}.purchase"
            expected[scope] = purchase["revision"]
            citation = match_purchase(purchase, basis, data["configuration_revision"], price_reader, now)
            if citation is None:
                data["purchase"] = None
            else:
                purchase_citations[f"{option}.price_release"] = citation

    require(citations.keys() == expected.keys(), "Each cost input requires a scoped citation.")
    for scope, pinned in expected.items():
        revision(pinned)
        citation = citations[scope]
        keys(citation, "locator revision", "cost citation")
        require(citation["revision"] == pinned and is_public_locator(citation["locator"]),
                "A cost citation must identify the reviewed revision and public HTTPS locator.")
    public_citations = [
        {"scope": scope, **citation} for scope, citation in {**citations, **purchase_citations}.items()
        if not scope.endswith(".purchase") or options[scope.split(".")[0]]["purchase"] is not None
    ]
    return {
        "revision": record["revision"], "authorization": authorization, "citations": public_citations,
        "price_basis": {**basis, "source_path": citations["scenario"]["locator"]},
        "options": {**empty["options"], **options},
    }
