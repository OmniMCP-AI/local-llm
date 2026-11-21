"""Append reviewed regional price observations and read immutable dated releases."""

import json
from pathlib import Path
import uuid

from fastest_release import ReleaseError, ReleaseStore, _sql_text

from . import validation
from .artifacts import ARTIFACT_NAMES, build_artifact
from .result import METHOD, build_result
from .validation import PriceError


class PriceReleaseNotFound(PriceError):
    """The requested price release does not exist."""


def _document(value):
    return f"{_sql_text(json.dumps(value, ensure_ascii=False))}::jsonb"


def _approve(cohort):
    return f"SELECT fastest_prices.approve({_document(cohort)});"


def _capture(cohort_id, capture):
    return f"SELECT fastest_prices.record_capture({_sql_text(cohort_id)}, {_document(capture)});"


class PriceStore:
    def __init__(self, database_url):
        self._postgres = ReleaseStore(database_url)

    def _query(self, sql):
        try:
            return self._postgres._query(sql)
        except ReleaseError as error:
            raise PriceError(str(error)) from error

    def migrate(self):
        for migration in ("schema.sql", "refresh.sql"):
            self._query(Path(__file__).with_name(migration).read_text(encoding="utf-8"))

    def approve(self, cohort):
        validation.cohort(cohort)
        return self._query(_approve(cohort))

    def capture(self, cohort_id, capture):
        validation.capture(capture)
        return int(self._query(_capture(cohort_id, capture)))

    def ingest(self, bundle):
        validation.bundle(bundle)
        cohort = bundle["cohort"]
        statements = [_approve(cohort), *(_capture(cohort["id"], capture) for capture in bundle["captures"])]
        self._query("\n".join(["BEGIN;", *statements, "COMMIT;"]))
        return cohort["id"]

    def publish(self, cohort_id, start, as_of):
        start, as_of = validation.period(start, as_of)
        return self._query(
            f"SELECT fastest_prices.publish({_sql_text(cohort_id)}, '{start}'::date, '{as_of}'::date, {_sql_text(METHOD)});"
        )

    def read(self, release_id):
        try:
            release_key = uuid.UUID(release_id)
        except (TypeError, ValueError, AttributeError) as error:
            raise PriceError("release ID must be a UUID") from error
        payload = self._query(f"SELECT fastest_prices.read_release('{release_key}'::uuid);")
        if not payload:
            raise PriceReleaseNotFound("Price release does not exist")
        return build_result(json.loads(payload))

    def artifact(self, release_id, name):
        if name not in ARTIFACT_NAMES:
            raise PriceError(f"Unknown price artifact: {name}")
        return build_artifact(self.read(release_id), name)

    def withdraw(self, cohort_id, reason):
        validation._text(reason, "withdrawal reason")
        key = _sql_text(cohort_id)
        self._query(f"""
            BEGIN;
            SELECT 1 FROM fastest_prices.cohort WHERE id = {key} FOR UPDATE;
            INSERT INTO fastest_prices.withdrawal (cohort_id, reason)
            VALUES ({key}, {_sql_text(reason)}) ON CONFLICT DO NOTHING;
            COMMIT;
        """)
