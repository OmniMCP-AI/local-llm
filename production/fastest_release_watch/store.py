from contextlib import closing
from datetime import timedelta
import json
import sqlite3

from .feed import FEED_URL, PAGE_SIZE, REPOSITORY, json_text, timestamp


STALE_AFTER = timedelta(days=1)
SCHEMA = """
CREATE TABLE IF NOT EXISTS source_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL,
    last_attempt TEXT,
    last_error TEXT,
    last_success TEXT
);
CREATE TABLE IF NOT EXISTS release_revision (
    revision_id TEXT PRIMARY KEY NOT NULL,
    release_id INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    document TEXT NOT NULL
);
"""


def record(database, mode, observed_at, releases=(), error=None):
    with closing(sqlite3.connect(database)) as db, db:
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA)
        db.execute("INSERT OR IGNORE INTO source_status (id, mode) VALUES (1, ?)", (mode,))
        if db.execute("SELECT mode FROM source_status").fetchone()[0] != mode:
            raise ValueError("Use separate databases for fixture replay and live refresh")
        if error is None:
            db.executemany(
                "INSERT OR IGNORE INTO release_revision VALUES (?, ?, ?, ?)",
                [(r["revision_id"], r["release_id"], observed_at, json_text(r)) for r in releases],
            )
            db.execute(
                "UPDATE source_status SET last_success = ? WHERE last_success IS NULL OR last_success < ?",
                (observed_at, observed_at),
            )
        db.execute(
            """UPDATE source_status SET last_attempt = ?, last_error = ?
               WHERE last_attempt IS NULL OR last_attempt <= ?""",
            (observed_at, error, observed_at),
        )


def snapshot(database, as_of):
    status = None
    rows = []
    if database.exists():
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db, db:
            db.execute("BEGIN")
            if db.execute("SELECT 1 FROM sqlite_schema WHERE name = 'source_status'").fetchone():
                status = db.execute(
                    "SELECT mode, last_attempt, last_error, last_success FROM source_status",
                ).fetchone()
                rows = db.execute(
                    "SELECT observed_at, document FROM release_revision ORDER BY observed_at DESC, rowid DESC",
                ).fetchall()
    return build_snapshot(as_of, status, rows)


def build_snapshot(as_of, status, rows):
    mode, last_attempt, last_error, last_success = status or (None, None, None, None)
    stale = last_success is None or timestamp(as_of) - timestamp(last_success) > STALE_AFTER
    return {
        "schema": "fastest.ai/runtime-release-watch/v1",
        "source": {"repository": REPOSITORY, "feed_url": FEED_URL, "page_size": PAGE_SIZE, "mode": mode},
        "last_attempt": last_attempt,
        "last_error": last_error,
        "last_successful_refresh": last_success,
        "stale": stale,
        "releases": release_history(rows),
    }


def release_history(rows):
    by_release = {}
    for observed_at, document in rows:
        revision = {**json.loads(document), "first_seen_at": observed_at}
        by_release.setdefault(revision["release_id"], []).append(revision)
    groups = sorted(
        by_release.values(),
        key=lambda group: (group[0]["published_at"], group[0]["release_id"]),
        reverse=True,
    )
    history = []
    current_stable_found = False
    for latest, *older in groups:
        if latest["prerelease"]:
            latest["status"] = "prerelease"
        else:
            latest["status"] = "superseded_release" if current_stable_found else "current"
            current_stable_found = True
        history.append(latest)
        history.extend({**row, "status": "superseded_revision"} for row in older)
    return history
