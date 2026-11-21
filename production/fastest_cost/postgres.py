"""Publish exact allowlists of reviewed tariff components from private intake."""

from datetime import datetime, timezone
import json
import re
from subprocess import TimeoutExpired

from fastest_pilot_bundle import digest, json_text
from fastest_release import ReleaseError, _sql_text
from fastest_release.validation import keys, plain_text, valid_expiry

from .reviewed import CostInputError, active_tariff_references, canonical_uuid, require


TARIFF_PIN = re.compile(r"[0-9a-f]{64}")


def _unique_fields(pairs):
    record = dict(pairs)
    require(len(record) == len(pairs), "Approval JSON requires unique object fields.")
    return record


def approve(store, path):
    approval = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_fields)
    keys(approval, "schema_version decision_id expires_at candidates", "tariff reference approval")
    require(type(approval["schema_version"]) is int and approval["schema_version"] == 1,
            "Unsupported tariff reference approval schema version.")
    decision = approval["decision_id"]
    expires = approval["expires_at"]
    now = datetime.now(timezone.utc)
    require(canonical_uuid(decision), "A tariff approval requires a canonical decision UUID.")
    require(valid_expiry(expires) and datetime.fromisoformat(expires) > now,
            "A tariff approval requires a future UTC expiry.")
    selection = approval["candidates"]
    require(isinstance(selection, list) and 1 <= len(selection) <= 128,
            "Select 1 to 128 tariff candidates for review.")
    for item in selection:
        keys(item, "batch_id source id source_label", "reviewed tariff candidate")
        require(all(plain_text(value) for value in item.values()) and TARIFF_PIN.fullmatch(item["batch_id"]),
                "Select each tariff candidate by exact batch digest, source and ID, with a public source label.")
    selection.sort(key=lambda item: (item["batch_id"], item["source"], item["id"]))
    require(len({item["id"] for item in selection}) == len(selection), "Duplicate tariff reference ID.")
    selected = _sql_text(json_text(selection))
    components = json.loads(store._query(f"""
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'id', tariff.id, 'kind', tariff.kind, 'provider', tariff.provider,
            'offering', tariff.offering, 'revision', tariff.revision, 'market', tariff.market,
            'region', tariff.region, 'currency', tariff.currency, 'amount', tariff.amount::text,
            'unit', tariff.unit, 'component', tariff.component,
            'effective_from', to_char(tariff.effective_from, 'YYYY-MM-DD'),
            'effective_until', to_char(tariff.effective_until, 'YYYY-MM-DD'),
            'qualification', tariff.qualification, 'source', chosen.source_label,
            'checked_at', to_char(batch.checked_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            'citation', jsonb_build_object('locator', probe.url, 'revision', tariff.revision)
        ) ORDER BY chosen.ordinal), '[]'::jsonb)
        FROM ROWS FROM (
            jsonb_to_recordset({selected}::jsonb) AS (batch_id text, source text, id text, source_label text)
        ) WITH ORDINALITY AS chosen(batch_id, source, id, source_label, ordinal)
        JOIN fastest_intake.tariff_candidate AS tariff USING (batch_id, source, id)
        JOIN fastest_intake.source_probe AS probe USING (batch_id, source)
        JOIN fastest_intake.batch AS batch ON batch.id = tariff.batch_id
        WHERE probe.status = 'captured';
    """))
    require(len(components) == len(selection), "Every selection must match a captured tariff candidate.")
    authorization = {"status": "approved", "decision_id": decision, "expires_at": expires}
    manifest = {"schema_version": 1, "authorization": authorization, "references": components}
    pin = digest(json_text({"selection": selection, "manifest": manifest}))
    active_tariff_references({**manifest, "revision": pin}, now)
    retained_pin = store._query(f"""
        INSERT INTO fastest_intake.tariff_reference_review (pin, decision_id, expires_at, selection, components)
        VALUES ('{pin}', '{decision}', '{expires}', {selected}::jsonb, {_sql_text(json_text(components))}::jsonb)
        ON CONFLICT DO NOTHING;
        SELECT pin FROM fastest_intake.tariff_reference_review WHERE decision_id = '{decision}';
    """)
    require(retained_pin == pin, "This decision ID already identifies a different tariff approval.")
    return pin


def read_pin(store, pin):
    try:
        payload = store._query(f"SELECT fastest_cost_public.read_tariff_references({_sql_text(pin)});")
        return active_tariff_references(json.loads(payload), datetime.now(timezone.utc)) if payload else None
    except (ReleaseError, TimeoutExpired, OSError, ValueError) as error:
        raise CostInputError("Unable to read the pinned PostgreSQL tariff references.") from error


def withdraw(store, pin):
    require(TARIFF_PIN.fullmatch(pin), "Withdrawal requires an exact lowercase tariff approval SHA-256.")
    retained_pin = store._query(f"""
        WITH approval AS (
            SELECT pin FROM fastest_intake.tariff_reference_review WHERE pin = '{pin}'
        ), withdrawal AS (
            INSERT INTO fastest_intake.tariff_reference_withdrawal (pin)
            SELECT pin FROM approval ON CONFLICT (pin) DO NOTHING
        )
        SELECT pin FROM approval;
    """)
    require(retained_pin, "No tariff approval was found for withdrawal.")
