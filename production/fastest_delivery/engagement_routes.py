"""Opt-in pilot evidence and comparison routes for the release origin."""

from hashlib import sha256
import logging
from hmac import compare_digest, digest
from html import escape
import re
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

from fastest_goals import GoalEvidenceWithdrawn, GoalRightsUnavailable
from fastest_goals.page import render_goals
from fastest_release import ReleaseNotFound
from fastest_release.artifacts import build_artifacts

from .engagement_link import LINK_PATH, UUID_PATTERN
from .engagement_store import EngagementStorageError


TOKEN = re.compile(rf"({UUID_PATTERN})\.({UUID_PATTERN})\.([a-f0-9]{{64}})")
BETWEEN_PAGES = "<p><a href=\"/goals\">Compare setups without sharing activity</a></p>"


class PilotEngagement:
    def __init__(self, releases, events, origin, mode, signing_key, goal_service):
        parts = urlsplit(origin)
        if (
            parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.netloc != parts.netloc.lower() or parts.path or parts.query or parts.fragment
            or "\\" in origin or any(character.isspace() or not character.isprintable() for character in origin)
            or parts.port == 0
        ):
            raise ValueError("pilot engagement origin must be an HTTPS origin with a lowercase host and no path")
        if mode not in {"live", "rehearsal"} or not isinstance(signing_key, bytes) or len(signing_key) != 32:
            raise ValueError("pilot engagement requires a mode and a 32-byte signing key")
        self.releases = releases
        self.events = events
        self.origin = origin
        self.host = parts.netloc
        self.mode = mode
        self.secret = signing_key
        self.goals = goal_service

    def _signature(self, key, body):
        return digest(self.secret, f"{self.mode}:{key}:{body}".encode("ascii"), "sha256").hex()

    def _token(self, key):
        body = f"{uuid4()}.{uuid4()}"
        return f"{body}.{self._signature(key, body)}"

    def _evidence(self, release_id):
        snapshot = self.releases.read(release_id)
        files = build_artifacts(snapshot)
        return snapshot, files

    def _page(self, release_id, files, section=""):
        # Restore the public artifact links under the canonical release path.
        html = files["benchmark.html"]
        for filename in ("benchmark.md", "chart.json", "table.json"):
            html = html.replace(f'href="./{filename}"', f'href="/releases/{release_id}/{filename}"')
        return html.replace("</main>", f"{section}</main>")

    def _controls(self, path, key, token=None):
        joining = token is None
        token = self._token(key) if joining else token
        action = "opt-in" if joining else "compare"
        fields = (
            "<p>Share this evidence visit and one comparison result with the pilot. "
            "Activity is anonymous and linked to this post.</p>"
            if joining else
            '<p>This evidence visit was shared. Set your minimum throughput and compare the reviewed setups.</p>'
            '<p><label>Minimum decode (tok/s) <input name="decode" type="number" min="0" step="any" required></label></p>'
            '<p><label>Minimum prefill (tok/s) <input name="prefill" type="number" min="0" step="any" required></label></p>'
        )
        label = "Share anonymous activity" if joining else "Compare setups"
        return (
            '<section aria-labelledby="pilot"><h2 id="pilot">Compare setups</h2>'
            f'<form method="post" action="{escape(path)}#pilot">'
            f'<input type="hidden" name="action" value="{action}">'
            f'<input type="hidden" name="journey" value="{escape(token)}">'
            f'{fields}<p><button>{label}</button></p></form>{BETWEEN_PAGES}</section>'
        )

    def handle(self, host, path, method, submitted=None):
        match = LINK_PATH.fullmatch(path)
        if host != self.host or not match or UUID(match[2]).version != 4:
            return 404, "Pilot evidence unavailable.\n"
        release_id, key = match.groups()
        try:
            snapshot, files = self._evidence(release_id)
        except ReleaseNotFound:
            return 404, "Pilot evidence unavailable.\n"
        if snapshot["status"] == "withdrawn":
            return 410, files["benchmark.html"]
        if snapshot["status"] != "published":
            return 503, "Pilot evidence unavailable.\n"

        try:
            binding = self.events.available(key, self.mode)
        except EngagementStorageError:
            if method not in ("GET", "HEAD"):
                raise
            logging.warning("Pilot engagement binding unavailable")
            binding = None
        eligible = (
            binding is not None and binding["release_id"] == release_id and snapshot["row"]["kind"] == "measured"
            and binding["evidence_destination"] == f"{self.origin}/releases/{release_id}/benchmark.html#citation"
            and binding["manifest_sha256"] == sha256(files["manifest.json"].encode("utf-8")).hexdigest()
        )
        if method in ("GET", "HEAD"):
            controls = self._controls(path, key) if eligible and method == "GET" else ""
            return 200, self._page(release_id, files, controls)
        if not eligible:
            return 409, "Engagement is unavailable for this evidence.\n"

        try:
            fields = parse_qs(submitted, keep_blank_values=True, strict_parsing=True, max_num_fields=4)
            if any(len(values) != 1 for values in fields.values()):
                raise ValueError
            values = {key: value[0] for key, value in fields.items()}
            action, token = values.pop("action"), values.pop("journey")
            expected = {"decode", "prefill"} if action == "compare" else set()
            if action not in {"opt-in", "compare"} or values.keys() != expected:
                raise ValueError
            match = TOKEN.fullmatch(token)
            if not match or not compare_digest(self._signature(key, f"{match[1]}.{match[2]}"), match[3]):
                raise ValueError
        except (KeyError, ValueError):
            return 400, "Invalid pilot form.\n"

        if action == "opt-in":
            if not self.events.arrive(key, self.mode, match[1]):
                return 409, "Engagement is unavailable for this evidence.\n"
            return 200, self._page(release_id, files, self._controls(path, key, token=token))

        try:
            selection = self.goals.selection({"entry": "expert", **values})
            result = self.goals.evaluate(selection)
            rendered = render_goals(self.goals, result, False)
        except ValueError:
            return 400, "Enter valid throughput goals.\n"
        except GoalEvidenceWithdrawn:
            return 410, "Comparison evidence withdrawn.\n"
        except GoalRightsUnavailable:
            return 503, "Comparison evidence unavailable.\n"
        if len(result["chart"]["points"]) >= 2:
            if not self.events.complete(key, self.mode, match[1], match[2]):
                return 409, "Share an evidence visit to start an attributed comparison.\n"
        return 200, rendered
