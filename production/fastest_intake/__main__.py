"""Import private source candidates for editorial and provenance review."""

import argparse
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from subprocess import TimeoutExpired

from fastest_release import ReleaseError, ReleaseStore, _sql_text

from .image_pilot import ingest_image_pilot


def table_counts(store):
    return json.loads(store._query("""
        SELECT json_build_object(
            'batches', (SELECT count(*) FROM fastest_intake.batch),
            'source_probes', (SELECT count(*) FROM fastest_intake.source_probe),
            'price_candidates', (SELECT count(*) FROM fastest_intake.price_candidate),
            'model_evaluations', (SELECT count(*) FROM fastest_intake.model_evaluation),
            'tariff_candidates', (SELECT count(*) FROM fastest_intake.tariff_candidate)
        );
    """))


def ingest(store, bundle):
    required = {"checked_at", "note", "sources", "prices", "evaluations"}
    if not isinstance(bundle, dict) or bundle.keys() - {"tariffs"} != required:
        raise ValueError("Expected checked_at, note, sources, prices, evaluations, and optional tariffs.")
    if datetime.fromisoformat(bundle["checked_at"]).utcoffset() is None:
        raise ValueError("checked_at must specify a time zone.")
    for key, identity in (("sources", "source"), ("prices", "id"), ("evaluations", "id"), ("tariffs", "id")):
        rows = bundle.get(key, [])
        if not isinstance(rows, list) or len(rows) > 10_000:
            raise ValueError(f"{key} must be a list of up to 10,000 records.")
        ids = {row.get(identity) for row in rows if isinstance(row, dict) and isinstance(row.get(identity), str)}
        if "" in ids or len(ids) != len(rows):
            raise ValueError(f"{key} must have distinct, nonempty {identity} values.")
    captured = {row["source"] for row in bundle["sources"] if row.get("status") == "captured"}
    for tariff in bundle.get("tariffs", []):
        source = tariff.get("source")
        if not isinstance(source, str) or source not in captured:
            raise ValueError("Each tariff candidate must reference a captured source probe in its batch.")
    packed = json.dumps(bundle, sort_keys=True, ensure_ascii=False, allow_nan=False)
    batch_id = sha256(packed.encode("utf-8")).hexdigest()
    payload = _sql_text(packed)
    store._query(f"""
        BEGIN;
        CREATE TEMP TABLE intake_payload (document jsonb NOT NULL) ON COMMIT DROP;
        INSERT INTO intake_payload VALUES ({payload}::jsonb);
        INSERT INTO fastest_intake.batch
        SELECT '{batch_id}', (document->>'checked_at')::timestamptz, document->>'note'
        FROM intake_payload ON CONFLICT DO NOTHING;
        INSERT INTO fastest_intake.source_probe
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'sources')
            AS item(source text, url text, status text, note text)
        ON CONFLICT DO NOTHING;
        INSERT INTO fastest_intake.price_candidate
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'prices')
            AS item(id text, source text, locator text, gpu_id text, board text, channel text,
                    market text, currency text, amount numeric, kind text, condition text, source_date date,
                    listing_url text, qualification text)
        ON CONFLICT DO NOTHING;
        INSERT INTO fastest_intake.model_evaluation
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'evaluations')
            AS item(id text, source text, locator text, model text, revision text, benchmark text,
                    benchmark_version text, metric text, amount numeric, unit text, evidence_class text, context jsonb)
        ON CONFLICT DO NOTHING;
        INSERT INTO fastest_intake.tariff_candidate
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'tariffs')
            AS item(id text, source text, locator text, kind text, provider text, offering text,
                    revision text, market text, region text, currency text, amount numeric, unit text,
                    component text, effective_from date, effective_until date, qualification text)
        ON CONFLICT DO NOTHING;
        COMMIT;
    """)
    return {"batch_id": batch_id, **table_counts(store)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    parser.add_argument("command", choices=("migrate", "ingest", "ingest-image-pilot", "stats"))
    parser.add_argument("source", type=Path, nargs="?", help="Capture bundle JSON or private image packet directory.")
    args = parser.parse_args()
    if args.database_url is None:
        parser.error("Set FASTEST_DATABASE_URL or pass --database-url.")
    if (args.command in ("ingest", "ingest-image-pilot")) != (args.source is not None):
        parser.error("Supply a source path for ingest or ingest-image-pilot.")
    store = ReleaseStore(args.database_url)
    try:
        if args.command == "migrate":
            store._query(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
        elif args.command == "ingest":
            print(json.dumps(ingest(store, json.loads(args.source.read_text(encoding="utf-8")))))
        elif args.command == "ingest-image-pilot":
            print(json.dumps(ingest_image_pilot(store, args.source)))
        else:
            print(json.dumps(table_counts(store)))
    except (OSError, ReleaseError, TimeoutExpired, TypeError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
