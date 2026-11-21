"""Versioned, allowlisted projections of the public release readers."""

from collections import deque
from dataclasses import dataclass
import json
import logging
import re
from subprocess import TimeoutExpired
from threading import Lock
from time import monotonic
from typing import Callable
from urllib.parse import parse_qsl, urlencode

from fastest_agent_task import AGENT_TASK_PIN_PATTERN, AGENT_TASK_ROUTE
from fastest_cost import CostInputError, DEFAULT_ACCEPTED, DEFAULT_MONTHS, MAX_ACCEPTED, MAX_MONTHS, calculate
from fastest_goals import (
    ENTRIES, METRICS, NUMBER, PRIVACY_LABELS, SERVING_ENTRY, SERVING_METRICS, GoalEvidenceWithdrawn,
    GoalRightsUnavailable,
)
from fastest_prices import PriceError, PriceReleaseNotFound
from fastest_prices.result import eligible_offer

from . import ReleaseError, ReleaseNotFound
from .advisor import advise


BASE = "/api/v1"
ADVISOR_PATH = BASE + "/advisor"
AGENT_TASK_PATH = BASE + "/comparison/agent-task"
DESCRIPTION = BASE + "/openapi.json"
CATALOG = "/.well-known/api-catalog"
VERSION = "1.0.0"
JSON = "application/json"
OPENAPI = "application/vnd.oai.openapi+json"
LINKSET = 'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"'
PROFILE_REVISION = {"type": "string", "pattern": r"^(?:current|v1-[a-f0-9]{16})$"}
KIND = {"type": "string", "enum": ["machines", "models"]}
UUID_PATTERN = r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}"
UUID_PARAM = {"type": "string", "pattern": f"^{UUID_PATTERN}$"}
AGENT_TASK_PIN = {"type": "string", "pattern": f"^{AGENT_TASK_PIN_PATTERN}$", "maxLength": 64,
                  "description": "SHA-256 of the pinned public report manifest."}
EVIDENCE_FIELDS = ("profile_cell", "backend", "runtime_revision", "run_id", "artifact_companion_sha256",
                   "workflow_sha256", "driver_version", "comparison_eligibility", "runner_image_version", "wall_power")
CONTRIBUTOR_FIELDS = ("runtime_revision", "runtime_sha256", "os_driver", "settings", "source_sha256",
                      "comparison_eligibility")
OFFER_FIELDS = ("listing_id", "seller", "kind", "confirmation", "stock", "discount", "observed_at",
                "captured_at", "price", "currency", "tax", "shipping", "landed_price", "age_days",
                "freshness", "latest_for_listing", "sample_selected", "availability", "expires_at")


def _object(fields):
    properties = {
        key: value if isinstance(value, dict) else {"type": value}
        for key, value in fields.items()
    }
    return {"type": "object", "properties": properties, "required": list(properties)}


def _array(items):
    return {"type": "array", "items": items}


PAGINATION = _object({"offset": "integer", "limit": "integer", "next_offset": ["integer", "null"]})
CATALOG_ENTRY = _object({"id": "string", "kind": KIND, "name": "string", "url": "string"})
MEASUREMENT = _object({"id": "string", "version": "integer", "value": "string", "unit": "string",
                       "statistic": "string", "boundary": "string", "sample_count": "integer"})
EVIDENCE_CONDITION = {"oneOf": [
    {**_object({"status": {"const": "known"}, "value": "string"}), "additionalProperties": False},
    {**_object({"status": {"const": "missing"}, "reason": "string"}), "additionalProperties": False},
]}
EVIDENCE_CONDITIONS = {
    "type": "object",
    "description": "Optional public conditions by evidence kind and field permission.",
    "properties": dict.fromkeys((*EVIDENCE_FIELDS, *CONTRIBUTOR_FIELDS), EVIDENCE_CONDITION),
    "additionalProperties": False,
}
PRICE_OFFER = _object({
    "listing_id": "string", "seller": "string", "kind": "string", "confirmation": "string",
    "stock": "string", "discount": "string", "observed_at": "string", "captured_at": "string",
    "price": "string", "currency": "string", "tax": "object", "shipping": "object",
    "landed_price": ["string", "null"], "age_days": "integer", "freshness": "string",
    "latest_for_listing": "boolean", "sample_selected": ["boolean", "null"],
    "comparable_asking_quote": "boolean", "citation": "object",
})
PRICE_OFFER["properties"].update({
    "availability": {"type": "string", "description": "Availability at the pinned release date."},
    "expires_at": {"type": ["string", "null"], "format": "date-time"},
})
TARIFF_REFERENCES = _object({
    "schema_version": {"type": "integer", "const": 1},
    "revision": "string",
    "authorization": _object({
        "status": {"type": "string", "const": "approved"}, "decision_id": UUID_PARAM,
        "expires_at": {"type": "string", "format": "date-time"},
    }),
    "references": _array(_object({
        "id": "string", "kind": "string", "provider": "string", "offering": "string", "revision": "string",
        "market": "string", "region": "string", "currency": "string", "amount": "string", "unit": "string",
        "component": "string", "qualification": "string", "source": "string",
        "effective_from": {"type": ["string", "null"], "format": "date"},
        "effective_until": {"type": ["string", "null"], "format": "date"},
        "checked_at": {"type": "string", "format": "date-time"},
        "citation": _object({"locator": {"type": "string", "format": "uri"}, "revision": "string"}),
    })),
})

PAGE = {
    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
    "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0},
}
PROFILE_PARAMS = {
    "kind": KIND, "id": {"type": "string", "pattern": r"^[a-z0-9.-]+$"},
    "revision": PROFILE_REVISION, **PAGE,
}
PROFILE_RESPONSE = {
    "revision": "string", "profile": "object", "url": "string", "cohorts": "array",
    "results": "array", "pagination": PAGINATION, "rights": "object", "citations": "array",
}
GOAL_PARAMS = {
    "revision": {"type": "string", "pattern": r"^(?:current|[a-f0-9]{64})$"},
    "entry": {"type": "string", "enum": list(ENTRIES)},
    "machine": {"type": "string", "pattern": r"^[a-z0-9.-]*$"},
    "privacy": {"type": "string", "enum": list(PRIVACY_LABELS)},
    **{key: {"type": "string", "enum": list(METRICS)} for key in ("priority", "x", "y")},
    **{key: {"type": "string", "pattern": f"^{NUMBER.pattern}$"} for key in ("prefill", "decode")},
    "budget": {"type": "string", "pattern": f"^(?:{NUMBER.pattern})?$"},
}
COMPARISON_PARAMS = {
    **GOAL_PARAMS,
    "entry": {"type": "string", "enum": [*ENTRIES, SERVING_ENTRY]},
    **{key: {"type": "string", "enum": [*METRICS, *SERVING_METRICS]} for key in ("priority", "x", "y")},
    **{key: {"type": "string", "pattern": f"^{NUMBER.pattern}$"} for key in ("user_p95", "capacity")},
    "wall_energy": {"type": "string", "pattern": f"^(?:{NUMBER.pattern})?$"},
}
COST_PARAMS = {
    "revision": {"type": "string", "pattern": r"^v1-[a-f0-9]{64}$"},
    "scenario": {"type": "string", "enum": ["evidence", "illustrative"], "default": "evidence"},
    "monthly_accepted": {"type": "integer", "minimum": 1, "maximum": MAX_ACCEPTED, "default": DEFAULT_ACCEPTED},
    "months": {"type": "integer", "minimum": 1, "maximum": MAX_MONTHS, "default": DEFAULT_MONTHS},
}
ADVISOR_PARAMS = {
    **GOAL_PARAMS, **COST_PARAMS,
    "decision": {"type": "string", "enum": ["configuration", "cost"], "default": "configuration"},
    "entry": {**GOAL_PARAMS["entry"], "default": "expert"},
    "monthly_accepted": {"type": "integer", "minimum": 1, "maximum": MAX_ACCEPTED},
    "months": {"type": "integer", "minimum": 1, "maximum": MAX_MONTHS},
    "revision": {"type": "string", "pattern": r"^(?:current|(?:v1-)?[a-f0-9]{64})$"},
}
REQUESTS_PER_MINUTE = 120
ERRORS = {
    400: "Invalid query parameters",
    404: "Operation or public release unavailable",
    410: "Public rights have ended",
    429: "API listener rate limit reached",
    503: "Canonical reader unavailable",
}


@dataclass(frozen=True)
class Operation:
    read: Callable[[dict[str, str]], dict]
    summary: str
    parameters: dict
    fields: dict
    required: tuple = ()


def _params(query, operation, *, blank_as_missing=()):
    if len(query) > 4096:
        raise ValueError("Query exceeds 4096 characters.")
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True, errors="strict",
                      max_num_fields=max(1, len(operation.parameters)))
    selection = dict(pairs)
    if len(selection) != len(pairs) or selection.keys() - operation.parameters.keys():
        raise ValueError("Unknown or repeated API parameter.")
    selection = {key: value for key, value in selection.items() if value or key not in blank_as_missing}
    if set(operation.required) - selection.keys():
        raise ValueError("A required API parameter is missing.")
    for key, value in selection.items():
        schema = operation.parameters[key]
        if schema["type"] == "integer":
            valid = re.fullmatch(r"[0-9]{1,9}", value) and schema["minimum"] <= int(value) <= schema["maximum"]
        else:
            valid = (
                len(value) <= schema.get("maxLength", 128)
                and all(character.isprintable() for character in value)
                and ("enum" not in schema or value in schema["enum"])
                and ("pattern" not in schema or re.fullmatch(schema["pattern"], value))
            )
        if not valid:
            raise ValueError(f"Invalid {key} parameter.")
    return selection


def _page(values, selection):
    offset = int(selection.get("offset", PAGE["offset"]["default"]))
    limit = int(selection.get("limit", PAGE["limit"]["default"]))
    end = offset + limit
    pagination = {
        "offset": offset, "limit": limit,
        "next_offset": end if end < len(values) and end <= PAGE["offset"]["maximum"] else None,
    }
    return values[offset:end], pagination


def _pick(document, *fields):
    return {field: document[field] for field in fields if field in document}


def _rights(document):
    return {"export_scope": "public-release", **_pick(document, "decision_id", "expires_at")}


class PublicApi:
    def __init__(self, store, profiles, profile_versions, goals, goal_versions, price_reader, *,
                 cost_reader=calculate, tariff_references_enabled=False, agent_task_enabled=False):
        self.price_reader = price_reader
        self.cost_reader = cost_reader
        self.tariff_references_enabled = tariff_references_enabled
        self.store = store
        self.profiles = profiles
        self.profile_versions = profile_versions
        self.goals = goals
        self.goal_versions = goal_versions
        self.operations = {
            BASE + "/search": Operation(
                self._search, "Search the pinned machine and model catalog",
                {"q": {"type": "string", "maxLength": 128}, "kind": KIND, "revision": PROFILE_REVISION, **PAGE},
                {"revision": "string", "results": _array(CATALOG_ENTRY), "pagination": PAGINATION},
            ),
            BASE + "/coverage": Operation(
                self._coverage, "Read measured coverage and exclusions for one profile",
                PROFILE_PARAMS, PROFILE_RESPONSE, ("kind", "id"),
            ),
            BASE + "/comparison/profile": Operation(
                self._profile_comparison, "Compare reviewed runs in pinned profile cohorts",
                PROFILE_PARAMS, PROFILE_RESPONSE, ("kind", "id"),
            ),
            BASE + "/comparison": Operation(
                self._goal_comparison, "Compare setups against released solo or team serving goals",
                COMPARISON_PARAMS, {
                    "release_id": "string", "text_release": "string", "selection": "object",
                    "market": "object", "metrics": "object", "protocol": "string", "quality_rubric": "string",
                    "rows": "array", "recommendation": ["string", "null"], "alternatives": "array", "chart": "object",
                    "url": "string", "citations": "array", "rights": "object",
                },
            ),
            ADVISOR_PATH: Operation(
                self._advisor, "Guide one released configuration or cost decision",
                ADVISOR_PARAMS, {
                    "decision": "string", "status": "string", "message": "string", "missing": _array({"type": "string"}),
                    "recommendation": ["string", "null"], "comparison": ["object", "null"], "costs": ["object", "null"],
                    "citations": "array", "wizard": ["string", "null"], "execution": "object",
                },
            ),
            BASE + "/calculator": Operation(
                self._calculator, "Calculate costs for the same accepted text workload",
                COST_PARAMS, {
                    "revision": "string", "method": "string", "scenario": "string", "estimate_kind": "string",
                    "inputs": "object", "workload": "object", "assumptions": "object", "units": "object",
                    "options": "object", "payback": "array", "cumulative_cost": "array", "sensitivity": "array",
                    "url": "string", "citations": "array", "rights": "object", "exclusions": "object",
                },
            ),
        }
        if store is not None:
            self.operations[BASE + "/evidence"] = Operation(
                self._evidence, "Resolve one reviewed evidence ID or pinned release",
                {"release": {"type": "string", "pattern": f"^(?:current|{UUID_PATTERN})$"},
                 "evidence_id": UUID_PARAM},
                {"release_id": "string", "revision": "integer", "evidence_id": "string", "status": "string",
                 "kind": {"type": "string", "enum": ["measured", "contributor"]},
                 "metric": MEASUREMENT, "conditions": EVIDENCE_CONDITIONS, "hardware": "object", "artifact": "object",
                 "workload": "object", "citations": "array", "rights": "object", "url": "string"},
            )
        if agent_task_enabled:
            self.operations[AGENT_TASK_PATH] = Operation(
                self._agent_task, "Read a reviewed inventory agent-task comparison by report manifest digest",
                {"release": AGENT_TASK_PIN}, {
                    "pin": AGENT_TASK_PIN, "url": "string", "citations": "array", "rights": "object",
                    "units": _object({"wall_time": {"type": "string", "const": "ns"}}),
                    "report": _object({
                        "schema_version": "integer", "kind": {"type": "string", "const": "measured"},
                        "notice": "string", "conditions": "object", "environment": "object",
                        "contexts": "array", "release_id": "string",
                    }),
                }, ("release",),
            )
        if price_reader is not None:
            self.operations[BASE + "/historical-offers"] = Operation(
                self._historical_offers, "Read a page of authorized quotes from a pinned historical release",
                {"release": UUID_PARAM, **PAGE}, {
                    "release_id": "string", "method": "string", "status": "string", "start": "string", "as_of": "string",
                    "unit": "string", "scope": "object", "market": "string", "destination": "string",
                    "condition": "string", "adapter_status": "string", "last_success_at": ["string", "null"],
                    "sampling": "object", "offers": _array(PRICE_OFFER), "pagination": PAGINATION,
                    "rights": "object", "url": "string",
                }, ("release",),
            )
        self.requests = deque()
        self.request_lock = Lock()

    def _allow_request(self):
        with self.request_lock:
            now = monotonic()
            while self.requests and self.requests[0] <= now - 60:
                self.requests.popleft()
            if len(self.requests) >= REQUESTS_PER_MINUTE:
                return False
            self.requests.append(now)
            return True

    def _openapi(self):
        def response(description, schema):
            return {"description": description, "content": {JSON: {"schema": schema}}}

        paths = {}
        for path, operation in self.operations.items():
            success = _object({"api_version": {"type": "string", "const": VERSION}, **operation.fields})
            if path == BASE + "/calculator" and self.tariff_references_enabled:
                success["properties"]["tariff_references"] = TARIFF_REFERENCES
            problem = _object({"api_version": "string", "error": "string"})
            paths[path] = {"get": {
                "operationId": path.removeprefix(BASE + "/").replace("/", "_").replace("-", "_"),
                "summary": operation.summary,
                "parameters": [
                    {"name": name, "in": "query", "required": name in operation.required, "schema": schema}
                    for name, schema in operation.parameters.items()
                ],
                "responses": {"200": response("Current public projection of the pinned revision", success),
                              **{str(code): response(label, problem) for code, label in ERRORS.items()}},
            }}
        return {
            "openapi": "3.1.0",
            "info": {"title": "fastest.ai public evidence API", "version": VERSION,
                     "description": f"Read-only release projections. Each listener allows "
                                    f"{REQUESTS_PER_MINUTE} API requests per rolling minute. Reuse the "
                                    "resolved revision and filters when following a pagination offset."},
            "paths": paths,
        }

    def handles(self, path):
        return path in {CATALOG, BASE} or path.startswith(BASE + "/")

    def advisor_form(self, query):
        """Interpret empty browser controls as missing before dispatching through the public API."""
        if not query:
            return 200, {}, None
        try:
            selection = _params(query, self.operations[ADVISOR_PATH], blank_as_missing=(
                "budget", "decode", "machine", "months", "monthly_accepted", "prefill", "privacy",
            ))
        except ValueError:
            return 400, {}, {"error": ERRORS[400]}
        status, result, _ = self.get(ADVISOR_PATH, urlencode(selection))
        if status == 400:
            result = {"error": ERRORS[400]}
        return status, selection, result

    def get(self, path, query):
        if path in {DESCRIPTION, CATALOG}:
            if query:
                return 400, {"api_version": VERSION, "error": ERRORS[400]}, JSON
            if path == DESCRIPTION:
                return 200, self._openapi(), OPENAPI
            return 200, {"linkset": [{"anchor": BASE + "/search",
                                     "service-desc": [{"href": DESCRIPTION, "type": OPENAPI}]}]}, LINKSET

        if path not in self.operations:
            return 404, {"api_version": VERSION, "error": ERRORS[404]}, JSON
        if not self._allow_request():
            return 429, {"api_version": VERSION, "error": ERRORS[429]}, JSON
        operation = self.operations[path]
        try:
            result = operation.read(_params(query, operation))
        except (ReleaseNotFound, PriceReleaseNotFound):
            return 404, {"api_version": VERSION, "error": ERRORS[404]}, JSON
        except GoalEvidenceWithdrawn:
            return 410, {"api_version": VERSION, "error": ERRORS[410], "status": "withdrawn"}, JSON
        except (CostInputError, GoalRightsUnavailable, ReleaseError, PriceError, OSError, TimeoutExpired, json.JSONDecodeError):
            logging.exception("Canonical public reader failed for %s", path)
            return 503, {"api_version": VERSION, "error": ERRORS[503]}, JSON
        except ValueError as error:
            return 400, {"api_version": VERSION, "error": str(error)}, JSON
        if result.get("status") == "withdrawn":
            return 410, {"api_version": VERSION, "error": ERRORS[410], **result}, JSON
        return 200, {"api_version": VERSION, **result}, JSON

    def _profile_version(self, selection):
        revision = selection.get("revision", "current")
        if revision == "current":
            if int(selection.get("offset", 0)):
                raise ValueError("Pin the profile revision before requesting subsequent pages.")
            return self.profiles
        if revision not in self.profile_versions:
            raise ReleaseNotFound(revision)
        return self.profile_versions[revision]

    def _search(self, selection):
        profiles = self._profile_version(selection)
        term = selection.get("q", "").strip().casefold()
        kind = selection.get("kind")
        results = [
            {**entry, "url": profiles.url(entry["kind"], entry["id"])}
            for entry in profiles.catalog()
            if (kind is None or entry["kind"] == kind)
            and (term in entry["id"].casefold() or term in entry["name"].casefold())
        ]
        page, pagination = _page(results, selection)
        return {"revision": profiles.id, "results": page, "pagination": pagination}


    def _profile_result(self, selection, *, measurements):
        profiles = self._profile_version(selection)
        kind, identifier = selection["kind"], selection["id"]
        try:
            data = profiles.data(kind, identifier)
        except LookupError:
            raise ReleaseNotFound(identifier) from None
        cohorts, results = [], []
        for cohort in data["cohorts"]:
            cohorts.append(_pick(cohort, "id", "plan_date", "model", "workload", "artifact", "runtime", "workflow",
                                 "metrics", "primary_metric", "secondary_metric"))
            for row in cohort["rows"]:
                entry = {"type": "run", "cohort_id": cohort["id"],
                         **_pick(row, "run_id", "cell_id", "backend", "machine_url", "model_url")}
                entry["evidence"] = [
                    {**_pick(observation, "evidence_id", "release_id", "source"),
                     "rights": _rights(observation["rights"])}
                    for observation in row["metrics"].values()
                ]
                if measurements:
                    entry["hardware"] = row["hardware"]
                    entry["metrics"] = {
                        identifier: {**observation, "rights": _rights(observation["rights"])}
                        for identifier, observation in row["metrics"].items()
                    }
                results.append(entry)
            results.extend({"type": "exclusion", "cohort_id": cohort["id"], **entry} for entry in cohort["exclusions"])
        page, pagination = _page(results, selection)
        url = profiles.url(kind, identifier)
        return {"revision": data["release"], "profile": data["profile"], "cohorts": cohorts,
                "url": url, "results": page, "pagination": pagination,
                "rights": {"export_scope": "public-release"}, "citations": [{"url": url, "revision": profiles.id}]}

    def _coverage(self, selection):
        return self._profile_result(selection, measurements=False)

    def _profile_comparison(self, selection):
        return self._profile_result(selection, measurements=True)

    def _goal_comparison(self, parameters):
        revision = parameters.pop("revision", "current")
        service = self.goals if revision == "current" else self.goal_versions.get(revision)
        if service is None:
            raise ReleaseNotFound(revision)
        selection = service.selection(parameters)
        result = service.evaluate(selection)
        url = service.url(selection)
        if selection["entry"] == SERVING_ENTRY:
            rights = {cell: _rights(run["rights"]) for cell, run in service.serving.items() if "rights" in run}
            citations = [{"url": url, "release_id": service.release_id}]
        else:
            rights = {cell["id"]: _rights(cell["rights"]) for cell in service.text["cells"] if "rights" in cell}
            citations = [{"url": f"/goals/{service.release_id}/text-pilot.html", "release_id": result["text_release"]}]
        return {**result, "rights": {"export_scope": "public-release", "measurements": rights},
                "citations": citations, "url": url}

    def _advisor(self, parameters):
        return advise(parameters, self._goal_comparison, self._calculator)

    def _agent_task(self, selection):
        pin = selection["release"]
        result = self.store.read_agent_task_artifact(pin, "agent-task.json")
        if result["status"] == "withdrawn":
            return {"status": "withdrawn"}
        if result["status"] != "published" or not isinstance(result.get("content"), str):
            raise ReleaseError("Agent task dataset unavailable.")
        # Publication validates the report and strips private input before writing this public artifact.
        report = json.loads(result["content"])
        if not isinstance(report, dict):
            raise ReleaseError("Agent task dataset unavailable.")
        if report.get("kind") != "measured" or report.get("environment") is None:
            raise ReleaseNotFound(pin)
        base = f"{AGENT_TASK_ROUTE}/{pin}/"
        return {
            "pin": pin, "report": report, "url": base + "agent-task.html",
            "citations": [{"url": base + "agent-task.json"}, {"url": base + "manifest.json", "sha256": pin}],
            "rights": {"export_scope": "public-release"}, "units": {"wall_time": "ns"},
        }

    def _calculator(self, parameters):
        revision = parameters.pop("revision", None)
        result = self.cost_reader(parameters)
        if revision is not None and revision != result["revision"]:
            raise ReleaseNotFound(revision)
        selection = {"scenario": result["scenario"],
                     **_pick(result["assumptions"], "months", "monthly_accepted")}
        if result["estimate_kind"] == "reviewed" or "tariff_references" in result:
            selection["revision"] = result["revision"]
        exclusions = {key: option["service"]["reasons"] for key, option in result["options"].items()
                      if option["service"]["reasons"]}
        return {**result, "url": "/costs?" + urlencode(selection),
                "rights": {"export_scope": "public-release", **_pick(result["inputs"].get("authorization", {}),
                                                                       "decision_id", "expires_at")},
                "exclusions": exclusions}


    def _evidence(self, selection):
        release = selection.get("release")
        evidence_id = selection.get("evidence_id")
        if release is None and evidence_id is None:
            raise ValueError("Select an evidence ID or a release.")
        snapshot = self.store.read(release) if release is not None else self.store.read_evidence(evidence_id)
        identity = _pick(snapshot, "release_id", "revision", "status")
        if snapshot["status"] == "withdrawn":
            return identity
        row = snapshot["row"]
        if row["kind"] not in ("measured", "contributor") or (evidence_id is not None and row["evidence_id"] != evidence_id):
            raise ReleaseNotFound(evidence_id or release)
        return {
            **identity, **_pick(row, "evidence_id", "kind", "metric", "hardware", "artifact", "workload"),
            "conditions": _pick(row["fields"], *(CONTRIBUTOR_FIELDS if row["kind"] == "contributor" else EVIDENCE_FIELDS)),
            "rights": _rights(row["rights"]), "citations": [row["source"]],
            "url": f"/releases/{snapshot['release_id']}/benchmark.html",
        }

    def _historical_offers(self, selection):
        release = selection["release"]
        result = self.price_reader(release)
        if result["status"] == "withdrawn":
            return _pick(result, "release_id", "status")
        if result["data_class"] != "authorized_observations":
            raise ReleaseNotFound(release)
        offers, pagination = _page(result["offers"], selection)
        source = _pick(result, "source_id", "source_revision")
        rights = {"decision_id": result["authorization_decision_id"], "export_scope": "authorized-offers",
                  "aggregate": result["sampling"]["range_status"] != "rights_restricted"}
        if "authorization_expires_at" in result:
            rights["expires_at"] = result["authorization_expires_at"]
        return {
            **_pick(result, "release_id", "status", "method", "scope", "market", "destination", "condition",
                    "start", "as_of", "adapter_status", "last_success_at", "sampling"),
            "unit": result["currency"], "rights": rights, "pagination": pagination,
            "url": f"/price-releases/{release}/prices.json",
            "offers": [
                {**_pick(offer, *OFFER_FIELDS), "comparable_asking_quote": eligible_offer(offer),
                 "citation": {**source, "locator": offer["source_locator"],
                              "review_decision_id": offer["review"]["decision_id"]}}
                for offer in offers
            ],
        }
