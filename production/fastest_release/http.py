import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re
from urllib.parse import parse_qs

from fastest_fit import FitEngineError, FitService, PUBLIC_FIELDS
from fastest_fit.page import render_fit

from . import ReleaseError, ReleaseNotFound
from .artifacts import build_artifacts


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


def make_server(store, host="127.0.0.1", port=8000, trusted_hosts=(), *, fit_engine=None):
    """Bind a read-only HTTP server that checks rights on every release request."""
    fit = FitService(fit_engine) if fit_engine is not None else None

    class ReleaseRequest(BaseHTTPRequestHandler):
        def _respond(self, status, body="", content_type="text/plain; charset=utf-8", location=None):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
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
            if fit is not None:
                if path in {"/fit", "/fit.json"}:
                    return self._fit(path, query)
                if path == "/":
                    benchmark = (
                        '<p><a href="/releases/current/benchmark.html">Current benchmark</a></p>'
                        if store is not None else ""
                    )
                    return self._respond(
                        200, '<!doctype html><html lang="en"><meta charset="utf-8">'
                        '<title>fastest.ai</title><h1>fastest.ai</h1>'
                        '<p><a href="/fit">Estimate model fit</a></p>' + benchmark,
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
