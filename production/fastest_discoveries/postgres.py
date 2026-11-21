import json
from pathlib import Path
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore, _sql_text

from . import store


class DiscoveryStorageError(RuntimeError):
    """PostgreSQL could not complete the discovery operation."""


def _query(database, sql):
    try:
        return ReleaseStore(database)._query(sql)
    except (ReleaseError, OSError, TimeoutExpired):
        raise DiscoveryStorageError(
            "PostgreSQL discovery operation failed. Check the connection, schema and permissions."
        ) from None


def _call(database, function, *arguments, write=False):
    statement = f"SELECT fastest_discoveries.{function}({', '.join(arguments)});"
    if write:
        statement = f"BEGIN ISOLATION LEVEL READ COMMITTED;\n{statement}\nCOMMIT;"
    response = json.loads(_query(database, statement))
    if isinstance(response, dict) and "error" in response:
        raise ValueError(response["error"])
    return response


def migrate(database):
    _query(database, Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    return {"schema": "fastest_discoveries"}


def import_sqlite(database, source):
    history = store.read_history(source)
    return _call(database, "import_history", f"{_sql_text(json.dumps(history, ensure_ascii=False))}::jsonb", write=True)


def submit(database, body):
    submission = dict(zip(store.SUBMISSION_FIELDS, store.validate_submission(body), strict=True))
    return _call(database, "submit", f"{_sql_text(json.dumps(submission, ensure_ascii=False))}::jsonb", write=True)


def review(database, source_url, choice, reviewer, reason):
    store.validate_review(source_url, choice, reviewer, reason)
    return _call(database, "review", *map(_sql_text, (source_url, choice, reviewer, reason)), write=True)


def withdraw(database, source_url, reason):
    store.validate_withdrawal(source_url, reason)
    return _call(database, "withdraw", _sql_text(source_url), _sql_text(reason), write=True)


def report(database, *, public):
    if public:
        return _call(database, "public_report")
    return store.format_report(_call(database, "queue_entries"), public=False)
