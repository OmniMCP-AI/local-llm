"""PostgreSQL storage for consented pilot journeys and operator attribution."""

import json
from pathlib import Path
import re
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore, _sql_text


class EngagementStorageError(RuntimeError):
    """The engagement service could not access its PostgreSQL records."""


class EngagementStore:
    def __init__(self, service):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", service):
            raise ValueError("use a libpq service name for the engagement database")
        self._postgres = ReleaseStore(f"service={service}")

    def _query(self, sql):
        try:
            return self._postgres._query(sql)
        except (ReleaseError, OSError, TimeoutExpired):
            raise EngagementStorageError("PostgreSQL pilot engagement operation failed") from None

    def migrate(self):
        self._query(Path(__file__).with_name("engagement-schema.sql").read_text(encoding="utf-8"))

    def bind(self, record):
        fields = ("attribution_key", "mode", "start_date", "release_id", "manifest_sha256",
                  "evidence_destination", "receipt_id", "post_url", "published_at")
        values = ", ".join(_sql_text(record[field]) + cast for field, cast in zip(
            fields, ("::uuid", "", "::date", "::uuid", "", "", "", "", "::timestamptz"), strict=True,
        ))
        added = self._query(f"""
            INSERT INTO fastest_pilot_engagement.binding AS retained ({", ".join(fields)})
            VALUES ({values})
            ON CONFLICT (attribution_key) DO UPDATE SET attribution_key = excluded.attribution_key
            WHERE retained = excluded
            RETURNING receipt_id;
        """)
        if added != record["receipt_id"]:
            raise ValueError("engagement key is already bound to a different approved post")

    def available(self, key, mode):
        found = self._query(f"""
            SELECT row_to_json(available) FROM fastest_pilot_engagement.available
            WHERE attribution_key = {_sql_text(key)}::uuid AND mode = {_sql_text(mode)};
        """)
        return json.loads(found) if found else None

    def arrive(self, key, mode, visit):
        return self._query(
            f"SELECT fastest_pilot_engagement.arrive({_sql_text(key)}::uuid, "
            f"{_sql_text(mode)}, {_sql_text(visit)}::uuid);"
        ) == "t"

    def complete(self, key, mode, visit, comparison):
        return self._query(
            f"SELECT fastest_pilot_engagement.complete({_sql_text(key)}::uuid, "
            f"{_sql_text(mode)}, {_sql_text(visit)}::uuid, {_sql_text(comparison)}::uuid);"
        ) == "t"

    def export(self, start, mode):
        query = Path(__file__).with_name("engagement-export.sql").read_text(encoding="utf-8")
        return json.loads(self._query(f"""
            WITH bindings AS (
                SELECT * FROM fastest_pilot_engagement.binding
                WHERE mode = {_sql_text(mode)} AND start_date = {_sql_text(start)}::date
            )
            {query}
        """))
