"""Retain approved, publishable aggregate input revisions for image-team reports."""

import json
from pathlib import Path
import re
from subprocess import TimeoutExpired

from fastest_pilot_bundle import digest, json_text
from fastest_release import ReleaseError, ReleaseStore, _sql_text

from .intake import validate


def _query(database, sql):
    try:
        return ReleaseStore(database)._query(sql)
    except (ReleaseError, OSError, TimeoutExpired):
        raise ValueError(
            "PostgreSQL image-team operation failed. Check the connection, migration and operator permissions."
        ) from None


def migrate(database):
    _query(database, Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))


def _unique_fields(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Scenario JSON must have unique object fields.")
    return result


def ingest_approved(database, scenario):
    data = json.loads(scenario.read_text(encoding="utf-8"), object_pairs_hook=_unique_fields)
    if not isinstance(data, dict) or data.get("kind") != "consented":
        raise ValueError("Approved import requires a consented aggregate scenario.")
    validate(data)
    pin = digest(json_text(data))
    # JSON preserves assumption order so the report matches the original file's HTML and Markdown.
    payload = _sql_text(json.dumps(data, ensure_ascii=False, allow_nan=False))
    _query(database, f"""
        INSERT INTO fastest_intake.image_team_scenario (pin, scenario)
        VALUES ('{pin}', {payload}::json)
        ON CONFLICT (pin) DO NOTHING;
    """)
    return pin


def _check_pin(pin):
    if re.fullmatch(r"[a-f0-9]{64}", pin) is None:
        raise ValueError("An exact lowercase scenario SHA-256 is required.")


def read_scenario(database, pin):
    _check_pin(pin)
    payload = _query(database, f"""
        SELECT approved.scenario
        FROM fastest_intake.image_team_scenario AS approved
        LEFT JOIN fastest_intake.image_team_withdrawal AS withdrawn USING (pin)
        WHERE approved.pin = '{pin}' AND withdrawn.pin IS NULL;
    """)
    if not payload:
        raise ValueError("No active approved image-team scenario is available for this pin.")
    data = json.loads(payload, object_pairs_hook=_unique_fields)
    if data.get("kind") != "consented" or digest(json_text(data)) != pin:
        raise ValueError("Stored image-team scenario does not match its approved pin.")
    return data


def withdraw(database, pin):
    _check_pin(pin)
    approved_pin = _query(database, f"""
        WITH approved AS (
            SELECT pin FROM fastest_intake.image_team_scenario WHERE pin = '{pin}'
        ), withdrawn AS (
            INSERT INTO fastest_intake.image_team_withdrawal (pin)
            SELECT pin FROM approved ON CONFLICT (pin) DO NOTHING
        )
        SELECT pin FROM approved;
    """)
    if not approved_pin:
        raise ValueError("No approved image-team scenario was found for withdrawal.")
