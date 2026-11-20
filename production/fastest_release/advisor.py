"""Guide one decision using the published goals and cost readers."""

from urllib.parse import urlencode

from fastest_goals import PUBLIC_FIELDS as GOAL_FIELDS
from fastest_cost import PUBLIC_FIELDS as COST_FIELDS


FIELDS = {
    "decode": "the minimum decode throughput in tok/s",
    "prefill": "the minimum prefill throughput in tok/s",
    "privacy": "whether processing must stay local",
    "budget": "the maximum landed whole-build price in the comparison market's currency",
    "machine": "the machine to evaluate",
    "monthly_accepted": "the number of accepted tasks needed each month",
    "months": "the cost comparison horizon in months",
}


def advise(parameters, read_goals, read_cost):
    """Return a clarification, a supported answer or an evidence-based abstention."""
    decision = parameters.pop("decision", "configuration")
    fields = GOAL_FIELDS if decision == "configuration" else COST_FIELDS | {"privacy"}
    if parameters.keys() - fields - {"revision"}:
        raise ValueError("A selector does not apply to this decision.")
    privacy = parameters.get("privacy")
    result = {
        "decision": decision, "missing": [], "recommendation": None, "comparison": None, "costs": None,
        "citations": [], "wizard": None,
        "execution": {
            "mode": "rules", "location": "server", "external_services": [],
            "workload_privacy_requirement": privacy,
            "evidence_reads": "Configured public release readers, including the price database when configured.",
        },
    }
    if decision == "configuration":
        entry = parameters.setdefault("entry", "expert")
        required = ["decode", "prefill", "privacy"]
        if entry == "budget":
            required.append("budget")
        elif entry == "machine":
            required.append("machine")
    else:
        required = ["monthly_accepted", "months", "privacy"]

    missing = [field for field in required if not parameters.get(field)]
    if missing:
        return {**result, "status": "clarify", "missing": missing,
                "message": "Please provide " + ", ".join(FIELDS[field] for field in missing) + "."}
    if decision == "configuration":
        return {**result, **_configuration(read_goals(parameters))}
    parameters.pop("privacy")
    return {**result, **_cost(read_cost(parameters), privacy)}


def _configuration(data):
    selection = data["selection"]
    rows = data["rows"]
    if selection["entry"] == "machine":
        rows = [row for row in rows if row["selected_machine"]]
    chosen = next((row["id"] for row in rows if row["status"] == "pass"), None)
    if chosen:
        rows = [row for row in rows if row["id"] == chosen]

    text_citation = data["citations"][0]
    citations = [{"kind": "text-pilot", **text_citation}]
    checks = []
    for row in rows:
        identifier = row["id"]
        checks.append({
            "id": identifier, "status": row["status"], "goals": row["goals"],
            "gates": {gate: record["status"] for gate, record in row["gates"].items()},
        })
        if row["run_source"]:
            citations.append({"kind": "text-run", **text_citation, "cell_id": identifier, **row["run_source"]})
        quote = row["metrics"]["budget"]
        row_url = f"{data['url']}#goal-{identifier}"
        if "budget" in row["goals"] and quote["value"] is not None:
            citations.append({
                "kind": "landed-quote", "cell_id": identifier, "url": row_url,
                "release_id": quote["release_id"], "listing_id": quote["listing_id"],
                "locator": quote["source_locator"], "observed_at": quote["observed_at"],
            })
        privacy = row["gates"]["privacy"]
        if "source" in privacy:
            citations.append({
                "kind": "privacy-review", "cell_id": identifier, "url": row_url,
                "release_id": data["release_id"], "locator": privacy["source"],
            })

    if chosen:
        message = "The selected configuration meets the supplied goals in this release."
    elif selection["entry"] == "machine":
        message = "The released evidence does not establish that your machine meets all supplied goals."
    else:
        message = "The released evidence does not establish a configuration that meets all supplied goals."
    replay = urlencode({"revision": data["release_id"], **selection})
    return {
        "status": "answer" if chosen else "abstain",
        "message": message,
        "recommendation": chosen, "wizard": data["url"], "citations": citations,
        "comparison": {
            "release_id": data["release_id"], "selection": selection, "rows": checks,
            "market": data["market"],
            "protocol": data["protocol"], "quality_rubric": data["quality_rubric"],
            "replay_url": "/api/v1/comparison?" + replay,
        },
    }


def _cost(data, privacy):
    options = {}
    for name, option in data["options"].items():
        external = name in {"rental", "api"}
        excluded = external and privacy == "local-only"
        options[name] = {
            "execution": "external" if external else "local",
            "status": "excluded" if excluded else option["service"]["status"],
            "reasons": ["external_processing_disallowed"] if excluded else option["service"]["reasons"],
            "upfront": None if excluded else option["purchase"]["upfront"],
            "monthly": None if excluded else option["monthly"]["recurring_cost"],
            "terminal_residual": None if excluded else option["totals"]["terminal_residual"],
            "nominal_cost": None if excluded else option["totals"]["nominal_cost"],
        }
    available = any(option["nominal_cost"] is not None for option in options.values())
    if not available:
        message = "The calculator has no supported total for the requested workload and privacy requirement."
    elif data["estimate_kind"] == "illustrative":
        message = "These totals use fictional prices and service assumptions for the requested workload."
    else:
        message = "The calculator provides these totals for the requested workload and privacy requirement."

    assumptions = data["assumptions"]
    replay = urlencode({"revision": data["revision"], "scenario": data["scenario"],
                        "monthly_accepted": assumptions["monthly_accepted"], "months": assumptions["months"]})
    return {
        "status": "answer" if available else "abstain",
        "message": message, "wizard": data["url"], "citations": data["citations"],
        "costs": {
            "revision": data["revision"], "scenario": data["scenario"], "estimate_kind": data["estimate_kind"],
            "assumptions": assumptions,
            "currency": data["units"]["money"], "options": options, "replay_url": "/api/v1/calculator?" + replay,
        },
    }
