import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import TimeoutExpired
import re
from urllib.parse import parse_qs

from fastest_cost import PUBLIC_FIELDS as COST_FIELDS, calculate
from fastest_cost.render import ROUTES as COST_ROUTES, render as render_cost
from fastest_fit import FitEngineError, FitService, PUBLIC_FIELDS
from fastest_fit.page import render_fit
from fastest_goals import GoalService, PUBLIC_FIELDS as GOAL_FIELDS
from fastest_goals.page import render_goals
from fastest_prices import PriceError, PriceReleaseNotFound

from . import ReleaseError, ReleaseNotFound
from .artifacts import build_artifacts
from .profiles import ProfileRelease, RUN_ID


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


PRICE_ROUTE = re.compile(r"/price-releases/([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})/prices\.json")


PROFILE_ROUTE = re.compile(r"/profiles/(v1-[a-f0-9]{16})/(machines|models)/([a-z0-9.-]+)\.(html|json|md)")


GOALS_ROUTE = re.compile(
    r"/goals/([a-f0-9]{64})(\.json|/(?:text-pilot\.(?:html|json|md)|manifest\.json))?"
)


def make_server(store, host="127.0.0.1", port=8000, trusted_hosts=(), *, fit_engine=None,
                profile_releases=(), profile_archives=(), goals=None, goal_history=(), price_reader=None):
    """Bind a read-only HTTP server that checks rights on every release request."""
    fit = FitService(fit_engine) if fit_engine is not None else None
    planned = ProfileRelease()
    profiles = ProfileRelease(store, profile_releases) if profile_releases else planned
    archived = [ProfileRelease(store, release_ids) for release_ids in profile_archives]
    profile_versions = {profile.id: profile for profile in (planned, profiles, *archived)}
    profile_indexes = {profile.base + "/index.html": profile for profile in profile_versions.values()}
    default_goals = GoalService()
    goals = goals or default_goals
    goal_versions = {service.release_id: service for service in (default_goals, *goal_history, goals)}
    profile_script = Path(__file__).with_name("profile-interaction.js").read_text(encoding="utf-8")

    class ReleaseRequest(BaseHTTPRequestHandler):
        def _respond(self, status, body="", content_type="text/plain; charset=utf-8", location=None, *, profile_script=False):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
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
            price_match = PRICE_ROUTE.fullmatch(path)
            if price_match and price_reader is not None:
                return self._price(price_match[1])
            if path in COST_ROUTES:
                return self._cost(path, query)
            if path == "/profiles/interaction.js":
                return self._respond(200, profile_script, "text/javascript; charset=utf-8")
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
                return self._respond(
                    200, '<!doctype html><html lang="en"><meta charset="utf-8">'
                    '<title>fastest.ai</title><h1>fastest.ai</h1>'
                    '<p><a href="/profiles">Machine and model comparisons</a></p>'
                    '<p><a href="/goals">Compare setups by goal</a></p>'
                    '<p><a href="/costs">Compare text workload costs</a></p>' + fit_link + benchmark,
                    CONTENT_TYPES["benchmark.html"],
                )
            match = RELEASE_ROUTE.fullmatch(path)
            if store is None or match is None or match[2] not in CONTENT_TYPES:
                return self._respond(404, "Release artifact unavailable.\n")

            release_id, name = match.groups()
            try:
                snapshot = store.read(release_id)
                if release_id == "current":
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
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(COST_FIELDS))
                if params.keys() - COST_FIELDS or any(len(values) != 1 for values in params.values()):
                    raise ValueError("Unknown or repeated cost parameter.")
                result = calculate({key: values[0] for key, values in params.items()})
            except ValueError as error:
                return self._respond(400, f"{error}\n")
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
                return self._respond(200, service.text_artifacts[name], content_type)
            try:
                params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=len(GOAL_FIELDS))
                if any(len(values) != 1 for values in params.values()):
                    raise ValueError("Repeated goals parameter.")
                selection = service.selection({key: values[0] for key, values in params.items()})
            except ValueError as error:
                return self._respond(400, f"{error}\n")
            if pin:
                return self._respond(307, location=service.url(selection))
            result = service.evaluate(selection)
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
