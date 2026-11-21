from functools import partial
import json
import logging
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import TimeoutExpired
import re
from urllib.parse import parse_qs

from fastest_agent_task import AGENT_TASK_ROUTE
from fastest_agent_task.publication import report_artifacts as agent_task_report_artifacts
from fastest_cost import CostInputError, PUBLIC_FIELDS as COST_FIELDS, calculate
from fastest_cost.render import ROUTES as COST_ROUTES, render as render_cost
from fastest_fit import FitEngineError, FitService, PUBLIC_FIELDS
from fastest_fit.page import render_fit
from fastest_goals import GoalEvidenceWithdrawn, GoalRightsUnavailable, GoalService, PUBLIC_FIELDS as GOAL_FIELDS
from fastest_goals.page import render_goals
from fastest_image import IMAGE_PILOT_ROUTE
from fastest_image.__main__ import report_artifacts as image_report_artifacts
from fastest_pilot_bundle import bundle_manifest, digest
from fastest_prices import PriceError, PriceReleaseNotFound
from fastest_release_watch.applicability import apply_notes
from fastest_release_watch.feed import utc_now
from fastest_release_watch.postgres import WatchStorageError
from fastest_release_watch.render import render as render_runtime_watch
from fastest_text import TEXT_PILOT_ROUTE

from . import CONTRIBUTOR_RECEIPT_PATH, ReleaseError, ReleaseNotFound
from .advisor_page import ROUTE as ADVISOR_ROUTE, render as render_advisor
from .api import ADVISOR_PATH, PublicApi
from .artifacts import build_artifacts
from .profiles import ProfileRelease, RUN_ID
from .scaling import ROUTE as SCALING_ROUTE, render_scaling, scaling_report


CONTENT_TYPES = {
    "benchmark.md": "text/markdown; charset=utf-8",
    "benchmark.html": "text/html; charset=utf-8",
    "chart.json": "application/json",
    "table.json": "application/json",
    "manifest.json": "application/json",
}
RELEASE_ROUTE = re.compile(
    r"/releases/(current|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})/([^/]+)"
)


RUNTIME_WATCH_ROUTES = {
    "/runtime-releases": ("html", CONTENT_TYPES["benchmark.html"]),
    "/runtime-releases.md": ("markdown", CONTENT_TYPES["benchmark.md"]),
    "/runtime-releases.json": ("json", CONTENT_TYPES["table.json"]),
}


PRICE_ROUTE = re.compile(r"/price-releases/([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})/prices\.json")


AGENT_TASK_PIN = re.compile(r"[a-f0-9]{64}")
AGENT_TASK_ARTIFACT_ROUTE = re.compile(r"/agent-task/([a-f0-9]{64})/([^/]+)")


PROFILE_ROUTE = re.compile(r"/profiles/(v1-[a-f0-9]{16})/(machines|models)/([a-z0-9.-]+)\.(html|json|md)")


GOALS_ROUTE = re.compile(
    r"/goals/([a-f0-9]{64})(\.json|/(?:text-pilot\.(?:html|json|md)|manifest\.json))?"
)


def render_contributor_receipt(revisions):
    items = []
    for revision in revisions:
        status = escape(revision["status"].replace("_", " ").capitalize())
        item = f'<li><h2>Version {revision["version"]}</h2><p>{status}</p>'
        if revision["issues"]:
            issues = ", ".join(escape(issue.replace("_", " ").capitalize()) for issue in revision["issues"])
            item += f"<p>Intake issues: {issues}</p>"
        if "url" in revision:
            label = "View withdrawal notice" if revision["status"] == "withdrawn" else "View published evidence"
            item += f'<p><a href="{escape(revision["url"])}">{label}</a></p>'
        items.append(item + "</li>")
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Benchmark submission status</title><main><h1>Benchmark submission status</h1><ol>'
        + "".join(items) + "</ol></main></html>"
    )


def make_server(store, host="127.0.0.1", port=8000, trusted_hosts=(), *, fit_engine=None,
                profile_releases=(), profile_archives=(), goals=None, goal_history=(), price_reader=None,
                scaling_pair=(), cost_scenario=None, contributor_receipts=False, agent_task_release=None,
                cost_tariff_references=None, runtime_watch=None, runtime_watch_notes=None):
    """Bind a read-only HTTP server that checks rights on every release request."""
    if contributor_receipts and store is None:
        raise ValueError("Contributor receipts require a release reader.")
    if agent_task_release is not None and (store is None or not AGENT_TASK_PIN.fullmatch(agent_task_release)):
        raise ValueError("An agent task release requires a release reader and a pinned report digest.")
    scaling_pair = tuple(scaling_pair)
    if scaling_pair and (
        store is None or len(scaling_pair) != 2 or len(set(scaling_pair)) != 2
        or not all(RUN_ID.fullmatch(identifier) for identifier in scaling_pair)
    ):
        raise ValueError("A scaling pair requires a release store and two distinct pinned release UUIDs.")
    scaling_url = SCALING_ROUTE + "/" + "/".join(scaling_pair) if scaling_pair else SCALING_ROUTE
    fit = FitService(fit_engine) if fit_engine is not None else None
    planned = ProfileRelease()
    profiles = ProfileRelease(store, profile_releases) if profile_releases else planned
    archived = [ProfileRelease(store, release_ids) for release_ids in profile_archives]
    profile_versions = {profile.id: profile for profile in (planned, profiles, *archived)}
    profile_indexes = {profile.base + "/index.html": profile for profile in profile_versions.values()}
    default_goals = GoalService()
    goals = goals or default_goals
    goal_versions = {service.release_id: service for service in (default_goals, *goal_history, goals)}
    image_report_id, image_files = image_report_artifacts()
    image_manifest = bundle_manifest(image_report_id, image_files)
    image_base = f"{IMAGE_PILOT_ROUTE}/{digest(image_manifest)}/"
    image_files["manifest.json"] = image_manifest
    text_manifest = default_goals.text_artifact("manifest.json")
    text_base = f"{TEXT_PILOT_ROUTE}/{digest(text_manifest)}/"
    text_files = {name: default_goals.text_artifact(name) for name in (
        "text-pilot.html", "text-pilot.md", "text-pilot.json", "manifest.json",
    )}
    agent_task_files = agent_task_report_artifacts()
    agent_task_base = f"{AGENT_TASK_ROUTE}/{digest(agent_task_files['manifest.json'])}/"
    pilot_redirects = {
        AGENT_TASK_ROUTE: (
            f"{AGENT_TASK_ROUTE}/{agent_task_release}/agent-task.html"
            if agent_task_release is not None else agent_task_base + "agent-task.html"
        ),
        IMAGE_PILOT_ROUTE: image_base + "image-pilot.html",
        TEXT_PILOT_ROUTE: (
            f"/goals/{goals.release_id}/text-pilot.html" if goals.text["evidence_kind"] == "measured"
            else text_base + "text-pilot.html"
        ),
    }
    pilot_types = {"html": CONTENT_TYPES["benchmark.html"], "md": CONTENT_TYPES["benchmark.md"],
                   "json": "application/json", "txt": "text/plain; charset=utf-8"}
    pilot_files = {
        base + name: (content, pilot_types[name.rsplit(".", 1)[1]])
        for base, files in ((image_base, image_files), (text_base, text_files), (agent_task_base, agent_task_files))
        for name, content in files.items()
    }
    cost_reader = partial(calculate, reviewed_path=cost_scenario, price_reader=price_reader,
                          tariff_references_path=cost_tariff_references)
    api = PublicApi(store, profiles, profile_versions, goals, goal_versions, price_reader,
                    cost_reader=cost_reader, tariff_references_enabled=cost_tariff_references is not None)
    profile_script = Path(__file__).with_name("profile-interaction.js").read_text(encoding="utf-8")

    class ReleaseRequest(BaseHTTPRequestHandler):
        def log_request(self, code="-", size="-"):
            path = self.path.partition("?")[0]
            if path in {ADVISOR_ROUTE, ADVISOR_PATH, CONTRIBUTOR_RECEIPT_PATH}:
                self.log_message('"%s %s %s" %s %s', self.command, path, self.request_version, code, size)
            else:
                super().log_request(code, size)

        def _respond(self, status, body="", content_type="text/plain; charset=utf-8", location=None, *, profile_script=False):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if self.path.partition("?")[0] == CONTRIBUTOR_RECEIPT_PATH:
                self.send_header("X-Robots-Tag", "noindex")
            policy = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            self.send_header("Content-Security-Policy", policy + ("; script-src 'self'" if profile_script else ""))
            if location is not None:
                self.send_header("Location", location)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(encoded)

        def do_GET(self):
            request_hosts = self.headers.get_all("Host", [])
            if len(request_hosts) != 1 or request_hosts[0].lower() not in allowed_hosts:
                return self._respond(400, "Invalid Host header.\n")
            path, _, query = self.path.partition("?")
            if path == CONTRIBUTOR_RECEIPT_PATH and contributor_receipts:
                return self._contributor_receipt(query)
            price_match = PRICE_ROUTE.fullmatch(path)
            if price_match and price_reader is not None:
                return self._price(price_match[1])
            if path in {SCALING_ROUTE, SCALING_ROUTE + ".json", scaling_url, scaling_url + ".json"}:
                return self._scaling(path)
            if runtime_watch is not None and path in RUNTIME_WATCH_ROUTES:
                return self._runtime_watch(path)
            if path in COST_ROUTES:
                return self._cost(path, query)
            if path == ADVISOR_ROUTE:
                status, selection, result = api.advisor_form(query)
                service = goal_versions.get(selection.get("revision"), goals)
                return self._respond(status, render_advisor(service, selection, result), CONTENT_TYPES["benchmark.html"])
            if api.handles(path):
                status, result, content_type = api.get(path, query)
                body = json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n"
                return self._respond(status, body, content_type)
            if path == "/profiles/interaction.js":
                return self._respond(200, profile_script, "text/javascript; charset=utf-8")
            if path in pilot_redirects:
                return self._respond(307, location=pilot_redirects[path])
            if path in pilot_files:
                return self._respond(200, *pilot_files[path])
            agent_task = AGENT_TASK_ARTIFACT_ROUTE.fullmatch(path)
            if store is not None and agent_task and agent_task[2] in agent_task_files:
                return self._agent_task(*agent_task.groups())
            if path in {"/profiles", "/profiles/current"}:
                return self._respond(307, location=profiles.base + "/index.html")
            if path in profile_indexes:
                return self._respond(200, profile_indexes[path].index(), CONTENT_TYPES["benchmark.html"])
            profile_match = PROFILE_ROUTE.fullmatch(path)
            if profile_match is not None and profile_match[1] in profile_versions:
                return self._profile(profile_versions[profile_match[1]], *profile_match.groups()[1:], query)
            if path in {"/goals", "/goals/current"}:
                return self._goals(goals, "", query, pin=True)
            goal_match = GOALS_ROUTE.fullmatch(path)
            if goal_match:
                release, suffix = goal_match.groups()
                if release not in goal_versions:
                    return self._respond(404, "Goals release unavailable.\n")
                return self._goals(goal_versions[release], suffix or "", query)
            if fit is not None and path in {"/fit", "/fit.json"}:
                return self._fit(path, query)
            if path == "/":
                fit_link = '<p><a href="/fit">Estimate model fit</a></p>' if fit is not None else ""
                benchmark = (
                    '<p><a href="/releases/current/benchmark.html">Current benchmark</a></p>'
                    if store is not None else ""
                )
                watch_links = (
                    '<p><a href="/runtime-releases">llama.cpp release watch</a> '
                    '<a href="/runtime-releases.md">Markdown</a> '
                    '<a href="/runtime-releases.json">JSON</a></p>'
                    if runtime_watch is not None else ""
                )
                return self._respond(
                    200, '<!doctype html><html lang="en"><meta charset="utf-8">'
                    '<title>fastest.ai</title><h1>fastest.ai</h1>'
                    '<p><a href="/profiles">Machine and model comparisons</a></p>'
                    '<p><a href="/goals">Compare setups by goal</a></p>'
                    '<p><a href="/advisor">Guided advisor</a></p>'
                    '<p><a href="/costs">Compare text workload costs</a></p>'
                    f'<p><a href="{TEXT_PILOT_ROUTE}">Two-machine text pilot</a></p>'
                    f'<p><a href="{IMAGE_PILOT_ROUTE}">Two-machine image pilot</a></p>'
                    f'<p><a href="{AGENT_TASK_ROUTE}">Controlled inventory agent comparison</a></p>'
                    f'<p><a href="{SCALING_ROUTE}">Compare single-to-multi-GPU scaling</a></p>' + fit_link + benchmark + watch_links,
                    CONTENT_TYPES["benchmark.html"],
                )
            match = RELEASE_ROUTE.fullmatch(path)
            if store is None or match is None or match[2] not in CONTENT_TYPES:
                return self._respond(404, "Release artifact unavailable.\n")

            release_id, name = match.groups()
            try:
                snapshot = store.read(release_id)
                if release_id == "current" and snapshot["status"] == "published":
                    pinned = snapshot["release_id"]
                    return self._respond(307, location=f"/releases/{pinned}/{name}")
                body = build_artifacts(snapshot)[name]
            except ReleaseNotFound:
                return self._respond(404, "Release artifact unavailable.\n")
            except ReleaseError:
                logging.exception("Cannot read the benchmark release")
                return self._respond(503, "Release service unavailable.\n")

            status = 410 if snapshot["status"] == "withdrawn" else 200
            return self._respond(status, body, CONTENT_TYPES[name])

        def _runtime_watch(self, path):
            format_name, content_type = RUNTIME_WATCH_ROUTES[path]
            try:
                report = runtime_watch.snapshot(utc_now())
                if report["source"]["mode"] == "fixture":
                    raise ValueError("Fixture histories are reserved for CLI review.")
                report = apply_notes(report, runtime_watch_notes, store.read if store is not None else None)
            except (WatchStorageError, ReleaseError, TimeoutExpired, OSError, ValueError):
                logging.warning("Cannot read the runtime release watch")
                report = {"error": "Runtime release watch unavailable."}
                return self._respond(503, render_runtime_watch(report, format_name), content_type)
            return self._respond(200, render_runtime_watch(report, format_name), content_type)

        def _agent_task(self, pin, artifact):
            try:
                result = store.read_agent_task_artifact(pin, artifact)
            except ReleaseNotFound:
                return self._respond(404, "Agent task release unavailable.\n")
            except (ReleaseError, OSError, TimeoutExpired, json.JSONDecodeError):
                logging.warning("Cannot read an agent task release")
                return self._respond(503, "Agent task release service unavailable.\n")
            if result["status"] == "withdrawn":
                return self._respond(410, "Agent task evidence withdrawn.\n")
            if result["status"] != "published" or not isinstance(result.get("content"), str):
                return self._respond(503, "Agent task release service unavailable.\n")
            return self._respond(200, result["content"], pilot_types[artifact.rsplit(".", 1)[1]])

        def _contributor_receipt(self, query):
            key, _, receipt = query.partition("=")
            unavailable = "Contributor receipt unavailable.\n"
            if key != "id" or not RUN_ID.fullmatch(receipt):
                return self._respond(404, unavailable)
            try:
                revisions = store.read_contributor_receipt(receipt)
            except ReleaseNotFound:
                return self._respond(404, unavailable)
            except (ReleaseError, TimeoutExpired, OSError):
                logging.warning("Cannot read a contributor receipt")
                return self._respond(503, "Contributor receipt service unavailable.\n")
            return self._respond(200, render_contributor_receipt(revisions), CONTENT_TYPES["benchmark.html"])

        def _scaling(self, path):
            is_json = path.endswith(".json")
            if scaling_pair and path.removesuffix(".json") == SCALING_ROUTE:
                return self._respond(307, location=scaling_url + (".json" if is_json else ""))
            try:
                report = scaling_report(store, scaling_pair)
            except (ReleaseError, TimeoutExpired, OSError):
                logging.exception("Cannot read a pinned GPU scaling pair")
                return self._respond(503, "GPU scaling release service unavailable.\n")
            status = 410 if (report["reason"] or "").endswith("_withdrawn") else 200
            if is_json:
                return self._respond(status, json.dumps(report, ensure_ascii=False, allow_nan=False) + "\n",
                                     CONTENT_TYPES["table.json"])
            return self._respond(status, render_scaling(report), CONTENT_TYPES["benchmark.html"])

        def _price(self, release_id):
            try:
                result = price_reader(release_id)
            except PriceReleaseNotFound:
                return self._respond(404, "Price release unavailable.\n")
            except (OSError, TimeoutExpired, PriceError):
                logging.exception("Cannot read a price release")
                return self._respond(503, "Price release service unavailable.\n")
            status = 410 if result["status"] == "withdrawn" else 200
            return self._respond(status, json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n",
                                 CONTENT_TYPES["table.json"])

        def _cost(self, path, query):
            try:
                fields = COST_FIELDS | {"revision"}
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(fields))
                if params.keys() - fields or any(len(values) != 1 for values in params.values()):
                    raise ValueError("Unknown or repeated cost parameter.")
                selection = {key: values[0] for key, values in params.items()}
                revision = selection.pop("revision", None)
                result = cost_reader(selection)
            except (CostInputError, OSError, TimeoutExpired, PriceError):
                logging.exception("Cannot read the configured cost scenario")
                return self._respond(503, "Cost scenario unavailable.\n")
            except ValueError as error:
                return self._respond(400, f"{error}\n")
            if revision is not None and revision != result["revision"]:
                return self._respond(404, "Cost scenario revision unavailable.\n")
            return self._respond(200, render_cost(result, path), COST_ROUTES[path])

        def _profile(self, profiles, kind, identity, extension, query):
            try:
                data = profiles.data(kind, identity)
            except LookupError:
                return self._respond(404, "Profile unavailable.\n")
            except ReleaseError:
                logging.exception("Cannot read a profile benchmark release")
                return self._respond(503, "Release service unavailable.\n")
            if extension == "json":
                return self._respond(200, json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n", "application/json")
            if extension == "md":
                return self._respond(200, profiles.markdown(data), CONTENT_TYPES["benchmark.md"])
            selected = query.removeprefix("run=") if query.startswith("run=") else ""
            selected = selected if RUN_ID.fullmatch(selected) else None
            return self._respond(200, profiles.render(data, selected), CONTENT_TYPES["benchmark.html"], profile_script=True)

        def _goals(self, service, suffix, query, *, pin=False):
            if suffix.startswith("/"):
                name = suffix[1:]
                extension = name.rsplit(".", 1)[1]
                content_type = {"html": CONTENT_TYPES["benchmark.html"], "md": CONTENT_TYPES["benchmark.md"],
                                "json": "application/json"}[extension]
                try:
                    return self._respond(200, service.text_artifact(name), content_type)
                except GoalEvidenceWithdrawn:
                    return self._respond(410, "Goal evidence withdrawn.\n")
                except GoalRightsUnavailable:
                    return self._respond(503, "Goal evidence unavailable.\n")
            try:
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(GOAL_FIELDS))
                if any(len(values) != 1 for values in params.values()):
                    raise ValueError("Repeated goals parameter.")
                selection = service.selection({key: values[0] for key, values in params.items()})
            except ValueError as error:
                return self._respond(400, f"{error}\n")
            if pin:
                return self._respond(307, location=service.url(selection))
            try:
                result = service.evaluate(selection)
            except GoalEvidenceWithdrawn:
                return self._respond(410, "Goal evidence withdrawn.\n")
            except GoalRightsUnavailable:
                return self._respond(503, "Goal evidence unavailable.\n")
            if suffix == ".json":
                return self._respond(200, json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n", "application/json")
            return self._respond(200, render_goals(service, result, fit is not None), CONTENT_TYPES["benchmark.html"])

        def _fit(self, path, query):
            try:
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(PUBLIC_FIELDS))
                if params.keys() - PUBLIC_FIELDS or any(len(values) != 1 for values in params.values()):
                    raise ValueError("Unknown or repeated fit parameter.")
                selection = {key: values[0] for key, values in params.items()}
                if path == "/fit" and selection.keys() <= {"machine"}:
                    if selection and selection["machine"] not in fit.machines:
                        raise ValueError("Unknown machine.")
                    result = None
                else:
                    result = fit.estimate(selection)
            except ValueError as error:
                return self._respond(400, f"{error}\n")
            except FitEngineError:
                logging.exception("Cannot run the pinned fit engine")
                return self._respond(503, "Fit engine unavailable.\n")
            if path == "/fit.json":
                return self._respond(200, json.dumps(result, allow_nan=False) + "\n", "application/json")
            return self._respond(200, render_fit(fit, selection, result), CONTENT_TYPES["benchmark.html"])

        do_HEAD = do_GET

    server = ThreadingHTTPServer((host, port), ReleaseRequest)
    hostnames = tuple(trusted_hosts) or (f"{host}:{server.server_port}",)
    allowed_hosts = {name.lower() for name in hostnames}
    return server
