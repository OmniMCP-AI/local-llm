from hashlib import sha256
import json
from pathlib import Path
import re
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore, _sql_text

from .applicability import apply_notes
from .feed import RUNTIME, SOURCES, json_text, utc_now
from .review import review_snapshot
from .store import MODE_ERROR, build_snapshot


NOTES_REVISION = re.compile(r"[a-f0-9]{64}")


class WatchStorageError(RuntimeError):
    """The PostgreSQL watcher operation could not complete."""


class PostgresStore:
    def __init__(self, database_url):
        self._postgres = ReleaseStore(database_url)

    def _query(self, sql):
        try:
            return self._postgres._query(sql)
        except (ReleaseError, OSError, TimeoutExpired) as error:
            raise WatchStorageError(
                "PostgreSQL watcher operation failed. Check the connection and apply the watcher migration."
            ) from error

    def migrate(self):
        self._query(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))

    def ingest_notes(self, document):
        reviewed = apply_notes(
            self.snapshot(utc_now()), document, self._postgres.read, include_review_lines=True,
        )
        review_snapshot(reviewed)
        payload = _sql_text(json_text(document))
        return self._query(f"SELECT fastest_release_watch.ingest_applicability({payload});")

    def read_notes(self, revision):
        if not NOTES_REVISION.fullmatch(revision):
            raise ValueError("Expected a lowercase SHA-256 applicability revision")
        result = self._query(f"SELECT fastest_release_watch.read_applicability({_sql_text(revision)});")
        if not result:
            raise ValueError("Unknown applicability revision")
        document = json.loads(result)
        if sha256(json_text(document).encode("utf-8")).hexdigest() != revision:
            raise WatchStorageError("Stored applicability does not match its revision")
        return document

    def record(self, mode, observed_at, releases=(), error=None, *, runtime_id=RUNTIME):
        releases = list(releases)
        if runtime_id not in SOURCES or any(r["runtime_id"] != runtime_id for r in releases):
            raise ValueError("Releases must belong to the selected source")
        payload = _sql_text(json_text(releases))
        error_text = "NULL" if error is None else _sql_text(error)
        recorded = self._query(
            f"SELECT fastest_release_watch.record_refresh("
            f"{_sql_text(runtime_id)}, {_sql_text(mode)}, {_sql_text(observed_at)}::timestamptz, "
            f"{payload}::jsonb, {error_text});"
        )
        if recorded == "f":
            raise ValueError(MODE_ERROR)

    def snapshot(self, as_of):
        payload = json.loads(self._query("""
            SELECT json_build_object(
                'statuses', (
                    SELECT json_agg(json_build_array(
                        runtime_id,
                        mode,
                        to_char(last_attempt AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                        last_error,
                        to_char(last_success AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                    )) FROM fastest_release_watch.source_status
                ),
                'revisions', (
                    SELECT json_agg(
                        json_build_array(
                            to_char(observed_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                            document::text
                        ) ORDER BY observed_at DESC, ingest_order DESC
                    ) FROM fastest_release_watch.release_revision
                )
            );
        """))
        return build_snapshot(as_of, payload["statuses"] or [], payload["revisions"] or [])
