from contextlib import closing, contextmanager
import json
import re
import sqlite3
from urllib.parse import urlsplit

from fastest_release.validation import keys, plain_text, valid_expiry


MAX_SUBMISSION_BYTES = 16 * 1024
PUBLIC_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z][a-z0-9-]*")
WITHDRAWAL_REASONS = ("source_deleted", "permission_revoked")
SCHEMA = """
CREATE TABLE IF NOT EXISTS discovery (
    source_url TEXT PRIMARY KEY NOT NULL,
    original_url TEXT NOT NULL,
    source_format TEXT NOT NULL,
    published_at TEXT,
    authority TEXT NOT NULL,
    consent_reference TEXT NOT NULL,
    scope TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TABLE IF NOT EXISTS review (
    source_url TEXT PRIMARY KEY NOT NULL REFERENCES discovery (source_url),
    choice TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    reason TEXT NOT NULL,
    reviewed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE TABLE IF NOT EXISTS withdrawal (
    source_url TEXT PRIMARY KEY NOT NULL,
    reason TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""
ENTRIES = """
    SELECT d.*, r.choice, r.reviewer, r.reason, r.reviewed_at,
           COALESCE(self.reason, origin.reason) AS withdrawal_reason,
           COALESCE(self.recorded_at, origin.recorded_at) AS withdrawal_at
    FROM discovery d
    LEFT JOIN review r USING (source_url)
    LEFT JOIN withdrawal self ON self.source_url = d.source_url
    LEFT JOIN withdrawal origin ON origin.source_url = d.original_url
"""


def permalink(value):
    if not plain_text(value) or not re.fullmatch(r"[!-~]+", value) or "\\" in value:
        raise ValueError("Expected an exact public HTTPS source permalink")
    parts = urlsplit(value)
    if not value.startswith("https://") or not PUBLIC_HOST.fullmatch(parts.netloc) or not parts.path.strip("/"):
        raise ValueError("Expected an exact public HTTPS source permalink")
    if "?" in value.partition("#")[0] and not (
        parts.netloc in ("www.youtube.com", "youtube.com")
        and parts.path == "/watch"
        and re.fullmatch(r"v=[A-Za-z0-9_-]{11}", parts.query)
    ):
        raise ValueError("Use a public permalink without query parameters or access credentials")
    if "#" in value and not re.fullmatch(r"[A-Za-z0-9_-]+", parts.fragment):
        raise ValueError("Use a public permalink with a simple post anchor")


@contextmanager
def write(database):
    with closing(sqlite3.connect(database)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA)
        yield db


def unique_fields(pairs):
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Submission contains duplicate fields")
    return fields


def submit(database, body):
    if len(body) > MAX_SUBMISSION_BYTES:
        raise ValueError("Submission exceeds the byte limit")
    submission = json.loads(body.decode("utf-8"), object_pairs_hook=unique_fields)
    keys(submission, "source_url original_url source_format published_at consent", "Submission")
    consent = submission["consent"]
    keys(consent, "authority reference scope", "Consent")
    source_url, original_url = submission["source_url"], submission["original_url"]
    permalink(source_url)
    permalink(original_url)
    if submission["source_format"] not in ("forum", "social", "video"):
        raise ValueError("Expected a forum, social or video source")
    if submission["published_at"] is not None and not valid_expiry(submission["published_at"]):
        raise ValueError("Expected a UTC publication timestamp at second precision or null")
    if consent["authority"] not in ("rights_holder", "authorized_representative") or not plain_text(consent["reference"]):
        raise ValueError("Consent requires a rights holder or authorized representative and a grant reference")
    if consent["scope"] not in ("discovery_only", "public_source_link"):
        raise ValueError("Expected discovery_only or public_source_link consent")

    recorded = (
        source_url, original_url, submission["source_format"], submission["published_at"],
        consent["authority"], consent["reference"], consent["scope"],
    )
    with write(database) as db:
        db.execute(
            """INSERT INTO discovery
               (source_url, original_url, source_format, published_at, authority, consent_reference, scope)
               VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (source_url) DO NOTHING""",
            recorded,
        )
        existing = db.execute("SELECT * FROM discovery WHERE source_url = ?", (source_url,)).fetchone()
        if tuple(existing)[:-1] != recorded:
            raise ValueError("A different submission already exists for this source permalink")
        return {"source_url": source_url, "submitted_at": existing["submitted_at"]}


def review(database, source_url, choice, reviewer, reason):
    permalink(source_url)
    if choice not in ("approve", "withhold"):
        raise ValueError("Expected approve or withhold")
    if not plain_text(reviewer) or not plain_text(reason):
        raise ValueError("Review requires a reviewer and a single-line reason")
    with write(database) as db:
        discovery = db.execute(ENTRIES + " WHERE d.source_url = ?", (source_url,)).fetchone()
        if discovery is None:
            raise ValueError("No submission for this source permalink")
        decision = db.execute("SELECT * FROM review WHERE source_url = ?", (source_url,)).fetchone()
        if decision is not None:
            if (decision["choice"], decision["reviewer"], decision["reason"]) == (choice, reviewer, reason):
                return dict(decision)
            raise ValueError("The recorded review choice is immutable")
        restricted = withholding_reason(discovery)
        if choice == "approve" and restricted:
            raise ValueError(f"Publication is withheld: {restricted}")
        db.execute(
            "INSERT INTO review (source_url, choice, reviewer, reason) VALUES (?, ?, ?, ?)",
            (source_url, choice, reviewer, reason),
        )
        return dict(db.execute("SELECT * FROM review WHERE source_url = ?", (source_url,)).fetchone())


def withdraw(database, source_url, reason):
    permalink(source_url)
    if reason not in WITHDRAWAL_REASONS:
        raise ValueError("Expected source_deleted or permission_revoked")
    with write(database) as db:
        db.execute(
            "INSERT INTO withdrawal (source_url, reason) VALUES (?, ?) ON CONFLICT (source_url) DO NOTHING",
            (source_url, reason),
        )
        withdrawal = db.execute("SELECT * FROM withdrawal WHERE source_url = ?", (source_url,)).fetchone()
        if withdrawal["reason"] != reason:
            raise ValueError("A withdrawal is already recorded for this source permalink")
        return dict(withdrawal)


def report(database, *, public):
    rows = []
    if database.exists():
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN")
            if db.execute("SELECT 1 FROM sqlite_schema WHERE name = 'discovery'").fetchone():
                rows = db.execute(ENTRIES + " ORDER BY d.original_url, d.source_url").fetchall()
    entries = []
    for row in rows:
        status, reason = outcome(row)
        if public:
            if status == "pending":
                continue
            entry = {"status": status, "reason": reason}
            if status == "approved":
                entry.update(source_url=row["source_url"], published_at=row["published_at"])
        else:
            entry = {field: row[field] for field in (
                "source_url", "original_url", "source_format", "published_at", "submitted_at",
            )}
            entry["consent"] = {
                "authority": row["authority"], "reference": row["consent_reference"], "scope": row["scope"],
            }
            entry.update(status=status, reason=reason)
            entry["review"] = (
                {field: row[field] for field in ("choice", "reviewer", "reason", "reviewed_at")}
                if row["choice"] else None
            )
            entry["withdrawal"] = (
                {"reason": row["withdrawal_reason"], "recorded_at": row["withdrawal_at"]}
                if row["withdrawal_reason"] else None
            )
        entries.append(entry)
    return {
        "schema": "fastest.ai/discovery-public/v1" if public else "fastest.ai/discovery-queue/v1",
        "entries": entries,
    }


def withholding_reason(row):
    if row["withdrawal_reason"]:
        return row["withdrawal_reason"]
    if row["source_url"] != row["original_url"]:
        return "cross_post"
    if row["scope"] == "discovery_only":
        return "discovery_only"
    return None


def outcome(row):
    restricted = withholding_reason(row)
    if restricted:
        return "withheld", restricted
    if row["choice"] == "approve":
        return "approved", "source_link_approved"
    if row["choice"] == "withhold":
        return "withheld", "editor_withheld"
    return "pending", "review_required"
