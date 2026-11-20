"""Project one pinned text decision cohort and its rights-filtered build quotes."""

from decimal import Decimal, localcontext
import json
from json import JSONDecodeError
import re
from urllib.parse import urlencode
from uuid import UUID

from fastest_pilot_bundle import bundle_manifest, digest, json_text
from fastest_prices import PriceError
from fastest_prices.result import eligible_offer
from fastest_release.validation import plain_text
from fastest_serving import METRICS as SERVING_METRICS, PROTOCOL as SERVING_PROTOCOL, load_records
from fastest_text.__main__ import load_dataset, text_artifacts


METRICS = {
    "decode": {"label": "Decode throughput", "unit": "tok/s", "direction": "higher", "default": "40"},
    "prefill": {"label": "Prefill throughput", "unit": "tok/s", "direction": "higher", "default": "500"},
    "budget": {"label": "Landed whole-build price", "direction": "lower", "default": "1500"},
}
ENTRIES = {"machine": "Use my machine", "budget": "Shop by budget", "expert": "Expert compare"}
SERVING_ENTRY = "serving"
PUBLIC_FIELDS = {"entry", "machine", "decode", "prefill", "budget", "priority", "privacy", "x", "y", *SERVING_METRICS}
DEFAULT_MARKET = {"market": "US", "destination": None, "currency": "USD", "condition": "new"}
PRIVACY_LABELS = {"local-only": "Require local-only execution", "allow-external": "Allow external services"}
PRIVACY_RECORDS = {"local-only": "Local-only execution", "external": "External service use"}
STATUSES = ("pass", "miss", "unknown", "ineligible")
NUMBER = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,8})?")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _number(text, definition):
    _require(NUMBER.fullmatch(text), f"Invalid {definition['label'].lower()} goal.")
    return format(Decimal(text), "f").rstrip("0").rstrip(".") if "." in text else text


def _item(status, reason, *, value=None, **evidence):
    return {"status": status, "reason": reason, "value": value, **evidence}


class GoalEvidenceWithdrawn(LookupError):
    """A measured goal observation lacks current public authorization."""


class GoalRightsUnavailable(RuntimeError):
    """The configured rights file could not be read or validated."""


class GoalService:
    def __init__(self, manifest=None, *, price_reader=None, rights_path=None):
        policy = json.loads(manifest.read_text(encoding="utf-8")) if manifest else {
            "schema_version": 1, "records": [], "market": DEFAULT_MARKET, "candidates": {},
        }
        _require(isinstance(policy, dict) and policy.keys() - {"serving_records"} == {
            "schema_version", "records", "market", "candidates",
        } and type(policy["schema_version"]) is int and policy["schema_version"] == 1, "Invalid goals cohort manifest.")
        records = policy["records"]
        _require(isinstance(records, list) and all(plain_text(path) for path in records), "Invalid goals text records.")
        self.text = load_dataset([manifest.parent / path for path in records])
        self.machines = {cell["id"]: cell["name"] for cell in self.text["cells"]}
        self.market = policy["market"]
        _require(isinstance(self.market, dict) and self.market.keys() == DEFAULT_MARKET.keys()
                 and re.fullmatch("[A-Z]{2}", str(self.market["market"]))
                 and re.fullmatch("[A-Z]{3}", str(self.market["currency"]))
                 and self.market["condition"] in ("new", "used", "refurbished", "open_box")
                 and (self.market["destination"] is None or plain_text(self.market["destination"])),
                 "Invalid goals market.")
        self.candidates = policy["candidates"]
        _require(isinstance(self.candidates, dict) and self.candidates.keys() <= self.machines.keys(),
                 "Unknown goals cohort candidate.")
        for candidate in self.candidates.values():
            _require(isinstance(candidate, dict) and candidate.keys() <= {"build_revision", "price_release", "privacy"},
                     "Invalid goals candidate metadata.")
            if "price_release" in candidate:
                identifier = candidate["price_release"]
                try:
                    canonical = str(UUID(identifier))
                except (TypeError, ValueError, AttributeError):
                    raise ValueError("Invalid price release ID.") from None
                _require(canonical == identifier and plain_text(candidate.get("build_revision")) and self.market["destination"],
                         "A price release requires a pinned whole-build revision and market destination.")
                _require(price_reader is not None, "A pinned price release requires a price database.")
            elif "build_revision" in candidate:
                _require(plain_text(candidate["build_revision"]), "Invalid whole-build revision.")
            if "privacy" in candidate:
                privacy = candidate["privacy"]
                _require(isinstance(privacy, dict) and set(privacy) == {"value", "source"}
                         and privacy["value"] in tuple(PRIVACY_RECORDS) and plain_text(privacy["source"]),
                         "Invalid reviewed privacy evidence.")
        self.price_reader = price_reader
        self.metrics = {metric: {**definition, **({"unit": self.market["currency"]} if metric == "budget" else {})}
                        for metric, definition in METRICS.items()}
        serving_records = policy.get("serving_records", [])
        _require(isinstance(serving_records, list) and all(plain_text(path) for path in serving_records),
                 "Invalid goals serving records.")
        self.serving = load_records([manifest.parent / path for path in serving_records], self.text)
        release = {"version": 1, "text": self.text, "market": self.market, "candidates": self.candidates}
        if "serving_records" in policy:
            release["serving"] = {"protocol": SERVING_PROTOCOL, "setups": self.serving}
        self.release_id = digest(json_text(release))
        self.rights_path = rights_path
        context = [self.text[key] for key in ("artifact", "runtime")]
        self.observation_digests = {
            "text": {cell["id"]: digest(json_text(["text", self.text["protocol"], self.text["rubric"], context, cell]))
                     for cell in self.text["cells"] if "rights" in cell},
            "serving": {cell: digest(json_text(["serving", SERVING_PROTOCOL, context, cell, record]))
                        for cell, record in self.serving.items() if "rights" in record},
        }
        self._text_artifacts = text_artifacts(self.text)
        self._text_artifacts["manifest.json"] = bundle_manifest(self.text["id"], self._text_artifacts)

    def _require_current_rights(self, lane):
        required = self.observation_digests[lane].values()
        if not required:
            return
        if self.rights_path is None:
            raise GoalEvidenceWithdrawn(self.release_id)
        try:
            policy = json.loads(self.rights_path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError, UnicodeError) as error:
            raise GoalRightsUnavailable("Goal rights could not be read.") from error
        if (not isinstance(policy, dict) or set(policy) != {"schema_version", "observations"}
                or type(policy["schema_version"]) is not int or policy["schema_version"] != 1
                or not isinstance(policy["observations"], dict)
                or any(not re.fullmatch(r"[a-f0-9]{64}", key) or decision not in ("allow", "withdrawn")
                       for key, decision in policy["observations"].items())):
            raise GoalRightsUnavailable("Invalid goal rights policy.")
        if any(policy["observations"].get(observation) != "allow" for observation in required):
            raise GoalEvidenceWithdrawn(self.release_id)

    def text_artifact(self, name):
        self._require_current_rights("text")
        return self._text_artifacts[name]

    def selection(self, values):
        _require(values.keys() <= PUBLIC_FIELDS, "Unknown goals parameter.")
        entry = values.get("entry", "machine")
        _require(entry in ENTRIES or entry == SERVING_ENTRY, "Unknown starting point.")
        serving = entry == SERVING_ENTRY
        metrics = SERVING_METRICS if serving else self.metrics
        inactive = METRICS if serving else SERVING_METRICS
        _require(not inactive.keys() & values.keys(), "A threshold does not apply to this workload.")
        machine = values.get("machine", next(iter(self.machines)) if entry == "machine" else "")
        _require(machine == "" or machine in self.machines, "Unknown setup.")
        x_default = "capacity" if serving else "budget" if entry == "budget" else "prefill"
        y_default = "user_p95" if serving else "decode"
        priority = values.get("priority", "budget" if entry == "budget" else y_default)
        privacy = values.get("privacy", "local-only")
        x, y = values.get("x", x_default), values.get("y", y_default)
        _require(priority in metrics and privacy in PRIVACY_LABELS, "Unknown priority or privacy requirement.")
        _require(x in metrics and y in metrics and x != y, "Choose two distinct chart axes.")
        targets = {}
        for metric, definition in metrics.items():
            optional = metric in {"budget", "wall_energy"}
            default = "" if metric == "budget" and entry != "budget" else definition["default"]
            value = values.get(metric, default)
            targets[metric] = "" if optional and not value else _number(value, definition)
        return {"entry": entry, "machine": machine, **targets, "priority": priority, "privacy": privacy, "x": x, "y": y}

    def url(self, selection, suffix=""):
        return f"/goals/{self.release_id}{suffix}?{urlencode(selection)}"

    def _price(self, machine, candidate):
        identifier = candidate.get("price_release")
        if not identifier:
            return _item("unknown", "No reviewed, authorized whole-build price is pinned for this setup.")
        try:
            price = self.price_reader(identifier)
        except PriceError:
            return _item("unknown", "The pinned price release is unavailable.")
        if price["status"] == "withdrawn":
            return _item("unknown", "The pinned price release was withdrawn.")
        if price["data_class"] != "authorized_observations":
            return _item("unknown", "The pinned price release is illustrative.")
        expected_scope = {"kind": "whole_build", "id": machine, "revision_id": candidate["build_revision"]}
        if price["scope"] != expected_scope or any(price[field] != value for field, value in self.market.items()):
            return _item("unknown", "The pinned price does not cover this exact whole-build revision and market terms.")
        if price["adapter_status"] in {"incomplete", "failed"}:
            return _item("unknown", "The latest refresh for the pinned price was incomplete or failed.")
        if price["adapter_status"] != "fresh":
            return _item("unknown", "The pinned price source is stale or has no successful check.")
        offers = [offer for offer in price["offers"] if offer["latest_for_listing"] and eligible_offer(offer)]
        current = [
            offer for offer in offers
            if offer["freshness"] == "fresh" and offer.get("availability", "available") == "available"
        ]
        if not current:
            reason = "Eligible whole-build quotes are unavailable at the pinned date." if offers else (
                "No fresh, unconditional, confirmed, in-stock asking quote has known tax and shipping."
            )
            return _item("unknown", reason)
        quote = min(current, key=lambda offer: (Decimal(offer["landed_price"]), offer["listing_id"]))
        return _item("available", "Lowest comparable landed asking quote in the pinned release.",
                     value=quote["landed_price"], release_id=identifier,
                     **{field: quote[field] for field in ("observed_at", "seller", "listing_id", "source_locator")})

    def _row(self, cell, selection):
        machine = cell["id"]
        candidate = self.candidates.get(machine, {})
        metrics = {
            metric: {field: cell["metrics"][metric][field] for field in ("value", "status", "reason", "sample_count")}
            for metric in ("decode", "prefill")
        }
        metrics["budget"] = self._price(machine, candidate)
        quality = cell["quality"]
        if quality["output_count"]:
            accepted, total = quality["accepted_count"], quality["output_count"]
            count = f"{accepted} of {total} reviewed outputs met every rubric criterion."
            quality_gate = _item("pass" if accepted == total else "ineligible", count)
        else:
            quality_gate = _item("unknown", "No reviewed output from this setup for the pinned Chinese product-copy task.")

        privacy = candidate.get("privacy")
        privacy_required = selection["privacy"] == "local-only"
        if not privacy:
            privacy_gate = _item("unknown" if privacy_required else "pass", "Execution privacy is unverified.")
        else:
            allowed = not privacy_required or privacy["value"] == "local-only"
            privacy_gate = _item("pass" if allowed else "ineligible", PRIVACY_RECORDS[privacy["value"]] + ".",
                                 source=privacy["source"])

        if cell["status"] == "blocked":
            admission = _item("unknown", cell["blocker"])
        elif cell["status"] == "failed":
            reasons = list(dict.fromkeys(attempt["reason"] for attempt in cell["attempts"]))
            admission = _item("ineligible", "No successful timed attempt. " + " ".join(reasons))
        else:
            admission = _item("pass", f"Reviewed measurements on the pinned protocol ({cell['status']} run).")
        gates = {"admission": admission, "quality": quality_gate, "privacy": privacy_gate}
        return self._decision_row(cell, selection, self.metrics, metrics, gates,
                                  run_source=cell.get("source"), build_revision=candidate.get("build_revision"))

    def _serving_row(self, cell, selection):
        evidence = self.serving[cell["id"]]
        if evidence["status"] == "measured":
            admission = _item("pass", "Reviewed measurements cover the full serving protocol.")
        elif evidence["status"] == "failed":
            admission = _item("ineligible", "The full serving run produced zero accepted responses.")
        else:
            admission = _item("unknown", evidence["reason"])
        privacy = evidence.get("privacy")
        required = selection["privacy"] == "local-only"
        if privacy is None:
            privacy_gate = _item("unknown" if required else "pass", "Serving execution privacy is unverified.")
        else:
            status = "ineligible" if required and privacy != "local-only" else "pass"
            privacy_gate = _item(status, PRIVACY_RECORDS[privacy] + ".", source=evidence["source"]["locator"])
        return self._decision_row(
            cell, selection, SERVING_METRICS, evidence["metrics"], {"admission": admission, "privacy": privacy_gate},
            run_source=evidence.get("source"), serving={key: value for key, value in evidence.items() if key != "metrics"},
        )

    def _decision_row(self, cell, selection, definitions, metrics, gates, **metadata):
        goals = {metric: self._check(definition, metrics[metric], selection[metric], gates["admission"],
                                     gate_missing=metric != "budget")
                 for metric, definition in definitions.items() if selection[metric]}
        gate_states = {gate["status"] for gate in gates.values()}
        goal_states = {goal["status"] for goal in goals.values()}
        status = next((state for state in ("ineligible", "miss", "unknown")
                       if state in goal_states | gate_states), "pass")
        return {
            "id": cell["id"], "name": cell["name"], "backend": cell["backend"], "status": status,
            "selected_machine": cell["id"] == selection["machine"],
            "gates": gates, "goals": goals, "metrics": metrics, "chart_eligible": gate_states == {"pass"},
            **metadata,
        }

    def _check(self, definition, observation, target, admission, *, gate_missing):
        unit = definition["unit"]
        value = observation["value"]
        if value is None:
            status = "ineligible" if gate_missing and admission["status"] == "ineligible" else "unknown"
            reason = admission["reason"] if status == "ineligible" else observation["reason"]
            return _item(status, reason, value=None, target=target, unit=unit, gap=None)
        low = definition["direction"] == "lower"
        with localcontext() as context:
            context.prec = 80
            gap = Decimal(value) - Decimal(target) if low else Decimal(target) - Decimal(value)
        if gap > 0:
            difference = format(gap, "f")
            side = "over the maximum" if low else "below the minimum"
            return _item("miss", f"{difference} {unit} {side}.", value=value, target=target, unit=unit, gap=difference)
        return _item("pass", "At or within the required limit.", value=value, target=target, unit=unit, gap="0")

    def evaluate(self, selection):
        serving = selection["entry"] == SERVING_ENTRY
        self._require_current_rights("serving" if serving else "text")
        definitions = SERVING_METRICS if serving else self.metrics
        row_for = self._serving_row if serving else self._row
        rows = [row_for(cell, selection) for cell in self.text["cells"]]

        def rank(row):
            metric = selection["priority"]
            value = row["metrics"][metric]["value"]
            return STATUSES.index(row["status"]), value is None, _axis(definitions[metric], value) if value is not None else 0, row["id"]

        rows.sort(key=rank)
        supported = [row["id"] for row in rows if row["status"] == "pass"]
        alternatives = [row["id"] for row in rows if row["chart_eligible"] and row["status"] in {"pass", "miss"}
                        and (not supported or row["id"] != supported[0])]
        return {
            "release_id": self.release_id, "text_release": self.text["id"], "selection": selection,
            "market": self.market, "metrics": definitions, "rows": rows,
            "protocol": SERVING_PROTOCOL["id"] if serving else self.text["protocol"]["id"],
            "quality_rubric": "fixed-token-response@1" if serving else self.text["rubric"]["id"],
            **({"serving_protocol": {**SERVING_PROTOCOL, "artifact": self.text["artifact"],
                                     "runtime_revision": self.text["runtime"]["revision"]}} if serving else {}),
            "recommendation": supported[0] if supported else None, "alternatives": alternatives,
            "chart": _chart(rows, selection["x"], selection["y"], definitions),
        }


def _axis(definition, value):
    decimal = Decimal(value)
    return decimal if definition["direction"] == "lower" else decimal.copy_negate()


def _chart(rows, x, y, definitions):
    points = []
    for row in rows:
        x_value, y_value = (row["metrics"][metric]["value"] for metric in (x, y))
        if row["chart_eligible"] and x_value is not None and y_value is not None:
            points.append({"id": row["id"], "x": x_value, "y": y_value})

    axes = [(_axis(definitions[x], point["x"]), _axis(definitions[y], point["y"])) for point in points]
    for point, (first, second) in zip(points, axes):
        point["pareto"] = not any(a <= first and b <= second and (a < first or b < second) for a, b in axes)
    return {"x": x, "y": y, "points": points}
