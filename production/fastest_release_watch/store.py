from contextlib import closing
from datetime import timedelta
import json
import sqlite3

from .feed import HOST, PAGE_SIZE, RUNTIME, SOURCES, json_text, timestamp


STALE_AFTER = timedelta(days=1)
MODE_ERROR = "Use separate databases for fixture replay and live refresh"
SOURCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_status (
    runtime_id TEXT PRIMARY KEY NOT NULL,
    mode TEXT NOT NULL,
    last_attempt TEXT,
    last_error TEXT,
    last_success TEXT
)
"""
RELEASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS release_revision (
    revision_id TEXT PRIMARY KEY NOT NULL,
    release_id INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    document TEXT NOT NULL
);
"""


def source_table_is_legacy(db):
    return not db.execute("SELECT 1 FROM pragma_table_info('source_status') WHERE name = 'runtime_id'").fetchone()


def record(database, mode, observed_at, releases=(), error=None, *, runtime_id=RUNTIME):
    releases = list(releases)
    if runtime_id not in SOURCES or any(r["runtime_id"] != runtime_id for r in releases):
        raise ValueError("Releases must belong to the selected source")
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(SOURCE_SCHEMA)
        db.execute(RELEASE_SCHEMA)
        if source_table_is_legacy(db):
            db.execute("ALTER TABLE source_status RENAME TO legacy_source_status")
            db.execute(SOURCE_SCHEMA)
            db.execute(
                "INSERT INTO source_status SELECT ?, mode, last_attempt, last_error, last_success "
                "FROM legacy_source_status",
                (RUNTIME,),
            )
            db.execute("DROP TABLE legacy_source_status")
        if db.execute("SELECT 1 FROM source_status WHERE mode <> ?", (mode,)).fetchone():
            raise ValueError(MODE_ERROR)
        db.execute("INSERT OR IGNORE INTO source_status (runtime_id, mode) VALUES (?, ?)", (runtime_id, mode))
        if error is None:
            db.executemany(
                "INSERT OR IGNORE INTO release_revision VALUES (?, ?, ?, ?)",
                [(r["revision_id"], r["release_id"], observed_at, json_text(r)) for r in releases],
            )
            db.execute(
                "UPDATE source_status SET last_success = ? "
                "WHERE runtime_id = ? AND (last_success IS NULL OR last_success < ?)",
                (observed_at, runtime_id, observed_at),
            )
        db.execute(
            """UPDATE source_status SET last_attempt = ?, last_error = ?
               WHERE runtime_id = ? AND (last_attempt IS NULL OR last_attempt <= ?)""",
            (observed_at, error, runtime_id, observed_at),
        )


def snapshot(database, as_of):
    statuses = []
    rows = []
    if database.exists():
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db, db:
            db.execute("BEGIN")
            if db.execute("SELECT 1 FROM sqlite_schema WHERE name = 'source_status'").fetchone():
                if source_table_is_legacy(db):
                    statuses = db.execute(
                        "SELECT ?, mode, last_attempt, last_error, last_success FROM source_status", (RUNTIME,),
                    ).fetchall()
                else:
                    statuses = db.execute(
                        "SELECT runtime_id, mode, last_attempt, last_error, last_success FROM source_status",
                    ).fetchall()
                rows = db.execute(
                    "SELECT observed_at, document FROM release_revision ORDER BY observed_at DESC, rowid DESC",
                ).fetchall()
    return build_snapshot(as_of, statuses, rows)


def build_snapshot(as_of, statuses, rows):
    recorded = {runtime_id: fields for runtime_id, *fields in statuses}
    now = timestamp(as_of)
    sources = {}
    for runtime_id, source in SOURCES.items():
        mode, last_attempt, last_error, last_success = recorded.get(runtime_id, (None, None, None, None))
        sources[runtime_id] = {
            "name": source.name,
            "repository": source.repository,
            "feed_url": f"https://{HOST}{source.feed_path}",
            "page_size": PAGE_SIZE,
            "mode": mode,
            "last_attempt": last_attempt,
            "last_error": last_error,
            "last_successful_refresh": last_success,
            "stale": last_success is None or now - timestamp(last_success) > STALE_AFTER,
        }
    # Keep the v1 summary fields scoped to the original llama.cpp feed.
    llama = sources[RUNTIME]
    return {
        "schema": "fastest.ai/runtime-release-watch/v1",
        "source": {key: llama[key] for key in ("repository", "feed_url", "page_size", "mode")},
        **{key: llama[key] for key in ("last_attempt", "last_error", "last_successful_refresh", "stale")},
        "sources": sources,
        "releases": release_history(rows),
    }


def release_history(rows):
    by_release = {}
    for observed_at, document in rows:
        revision = {**json.loads(document), "first_seen_at": observed_at}
        key = (revision["runtime_id"], revision["release_id"])
        by_release.setdefault(key, []).append(revision)
    groups = sorted(
        by_release.values(),
        key=lambda group: (group[0]["published_at"], group[0]["release_id"], group[0]["runtime_id"]),
        reverse=True,
    )
    history = []
    current_stable_found = set()
    for latest, *older in groups:
        runtime_id = latest["runtime_id"]
        if latest["prerelease"]:
            latest["status"] = "prerelease"
        else:
            latest["status"] = "superseded_release" if runtime_id in current_stable_found else "current"
            current_stable_found.add(runtime_id)
        history.append(latest)
        history.extend({**row, "status": "superseded_revision"} for row in older)
    return history
