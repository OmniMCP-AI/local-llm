import base64
import json
from pathlib import Path
import subprocess
import uuid

from .artifacts import build_artifacts
from .validation import InvalidObservation, plain_text, validate


class ReleaseNotFound(LookupError):
    """No release is available at the requested ID."""


class ReleaseError(RuntimeError):
    """PostgreSQL rejected the release operation."""


def _sql_text(value):
    # Base64 carries arbitrary UTF-8 as SQL-safe characters over stdin.
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"convert_from(decode('{encoded}', 'base64'), 'UTF8')"


class ReleaseStore:
    """Write reviewed observation revisions and read their rights-filtered releases."""

    def __init__(self, database_url):
        self.database_url = database_url

    def _query(self, sql):
        result = subprocess.run(
            ["psql", "-XqAtw", "-v", "ON_ERROR_STOP=1", "-d", self.database_url],
            input=sql,
            encoding="utf-8",
            capture_output=True,
            timeout=30,
        )
        if result.returncode:
            raise ReleaseError(result.stderr.strip())
        return result.stdout.strip()

    def migrate(self):
        for migration in ("schema.sql", "research.sql"):
            self._query(Path(__file__).with_name(migration).read_text(encoding="utf-8"))

    def publish(self, observation):
        validate(observation)
        payload = _sql_text(json.dumps(observation, ensure_ascii=False))
        return self._query(f"SELECT fastest_release.publish_observation({payload}::jsonb);")

    def read(self, release_id=None):
        requested = "NULL" if release_id in (None, "current") else f"'{uuid.UUID(release_id)}'::uuid"
        result = self._query(f"SELECT fastest_release.read_release({requested});")
        if not result:
            raise ReleaseNotFound(release_id or "current")
        return json.loads(result)

    def artifact(self, release_id, name):
        try:
            return build_artifacts(self.read(release_id))[name]
        except KeyError as error:
            if error.args == (name,):
                raise ReleaseNotFound(name) from error
            raise

    def withdraw(self, evidence_id, reason):
        if not plain_text(reason):
            raise InvalidObservation("withdrawal reason must be nonempty, single-line text")
        evidence = uuid.UUID(evidence_id)
        result = self._query(
            f"SELECT fastest_release.withdraw_evidence('{evidence}'::uuid, {_sql_text(reason)});"
        )
        if result != "t":
            raise ReleaseNotFound(evidence_id)
