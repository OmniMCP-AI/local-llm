"""Private PostgreSQL checkpoints for scheduled editorial slots."""

import re
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore, _sql_text

from .approval import decode_sealed, json_bytes, seal


class SlotStorageError(ValueError):
    """A scheduled editorial slot could not be accessed or updated."""


def slot_reference(scheduled_at):
    return f"postgresql:fastest_editorial_slots.slot:{scheduled_at}"


class SlotStore:
    def __init__(self, service):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", service):
            raise ValueError("use a libpq service name for the scheduler database")
        self._postgres = ReleaseStore(f"service={service}")

    def _query(self, sql):
        try:
            return self._postgres._query(sql)
        except (ReleaseError, OSError, TimeoutExpired):
            raise SlotStorageError("PostgreSQL editorial slot operation failed") from None

    def read(self, scheduled_at):
        found = self._query(f"""
            SELECT record FROM fastest_editorial_slots.slot
            WHERE scheduled_at = {_sql_text(scheduled_at)}::timestamptz;
        """)
        if found:
            return decode_sealed(found, "run_id", "PostgreSQL editorial slot")

    def save(self, run):
        previous = run.get("run_id")
        record = seal({key: value for key, value in run.items() if key != "run_id"}, "run_id")
        timestamp = f"{_sql_text(run['scheduled_at'])}::timestamptz"
        body = f"{_sql_text(json_bytes(record).decode())}::jsonb"
        if previous is None:
            statement = f"""
                INSERT INTO fastest_editorial_slots.slot (scheduled_at, record) VALUES ({timestamp}, {body})
                ON CONFLICT DO NOTHING
            """
        else:
            statement = f"""
                UPDATE fastest_editorial_slots.slot SET record = {body}
                WHERE scheduled_at = {timestamp} AND record->>'run_id' = {_sql_text(previous)}
            """
        saved = self._query(f"{statement} RETURNING record->>'run_id';")
        if saved != record["run_id"]:
            raise SlotStorageError("scheduler slot changed during this attempt")
        run["run_id"] = saved

    def between(self, start, end):
        records = self._query(f"""
            SELECT record FROM fastest_editorial_slots.slot
            WHERE scheduled_at >= {_sql_text(start.isoformat())}::timestamptz
              AND scheduled_at < {_sql_text(end.isoformat())}::timestamptz
            ORDER BY scheduled_at;
        """)
        return [
            decode_sealed(line, "run_id", "PostgreSQL editorial slot")
            for line in records.split("\n") if line
        ]
