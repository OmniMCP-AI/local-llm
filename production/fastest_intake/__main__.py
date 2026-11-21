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
from .serving_capture import ingest_serving_capture


def table_counts(store):
    return json.loads(store._query("""
        SELECT json_build_object(
            'batches', (SELECT count(*) FROM fastest_intake.batch),
            'source_probes', (SELECT count(*) FROM fastest_intake.source_probe),
            'price_candidates', (SELECT count(*) FROM fastest_intake.price_candidate),
            'model_evaluations', (SELECT count(*) FROM fastest_intake.model_evaluation),
            'tariff_candidates', (SELECT count(*) FROM fastest_intake.tariff_candidate),
            'inference_trials', (SELECT count(*) FROM fastest_intake.inference_trial),
            'serving_capture_runs', (SELECT count(*) FROM fastest_intake.serving_capture_run),
            'serving_capture_attempts', (SELECT count(*) FROM fastest_intake.serving_capture_attempt)
        );
    """))


def ingest(store, bundle):
    required = {"checked_at", "note", "sources", "prices", "evaluations"}
    if not isinstance(bundle, dict) or bundle.keys() - {"tariffs", "inference_trials"} != required:
        raise ValueError(
            "Expected checked_at, note, sources, prices, evaluations, and optional tariffs and inference_trials."
        )
    if datetime.fromisoformat(bundle["checked_at"]).utcoffset() is None:
        raise ValueError("checked_at must specify a time zone.")
    for key, identity in (("sources", "source"), ("prices", "id"), ("evaluations", "id"),
                          ("tariffs", "id"), ("inference_trials", "id")):
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
    for trial in bundle.get("inference_trials", []):
        source = trial.get("source")
        if not isinstance(source, str) or source not in captured:
            raise ValueError("Each inference trial must reference a captured source probe in its batch.")
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
            (batch_id, id, source, locator, gpu_id, board, channel, market, currency, amount,
             kind, condition, source_date, listing_url, qualification, seller_business_name,
             listing_status, shipping_amount, tax_amount)
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'prices')
            AS item(id text, source text, locator text, gpu_id text, board text, channel text,
                    market text, currency text, amount numeric, kind text, condition text, source_date date,
                    listing_url text, qualification text, seller_business_name text, listing_status text,
                    shipping_amount numeric, tax_amount numeric)
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
        INSERT INTO fastest_intake.inference_trial
            (batch_id, id, source, locator, outcome, gpu_count, gpu_ids, model, model_revision,
             artifact, artifact_revision, runtime, runtime_revision, backend, quantization,
             context_tokens, observed_on, metric, amount, unit, statistic, sample_count,
             reported_uncertainty, uncertainty_kind, placement, transport, context, qualification)
        SELECT '{batch_id}', item.* FROM intake_payload,
        jsonb_to_recordset(document->'inference_trials')
            AS item(id text, source text, locator text, outcome text, gpu_count integer, gpu_ids text[],
                    model text, model_revision text, artifact text, artifact_revision text, runtime text,
                    runtime_revision text, backend text, quantization text, context_tokens integer,
                    observed_on date, metric text, amount numeric, unit text, statistic text,
                    sample_count integer, reported_uncertainty numeric, uncertainty_kind text,
                    placement text, transport text, context jsonb, qualification text)
        ON CONFLICT DO NOTHING;
        COMMIT;
    """)
    return {"batch_id": batch_id, **table_counts(store)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("FASTEST_DATABASE_URL"))
    imports = ("ingest", "ingest-image-pilot", "ingest-serving-capture")
    parser.add_argument("command", choices=("migrate", *imports, "stats"))
    parser.add_argument("source", type=Path, nargs="?", help="Capture bundle JSON or private packet directory.")
    args = parser.parse_args()
    if args.database_url is None:
        parser.error("Set FASTEST_DATABASE_URL or pass --database-url.")
    if (args.command in imports) != (args.source is not None):
        parser.error("Supply a source path only for an ingest command.")
    store = ReleaseStore(args.database_url)
    try:
        if args.command == "migrate":
            store._query(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
        elif args.command == "ingest":
            print(json.dumps(ingest(store, json.loads(args.source.read_text(encoding="utf-8")))))
        elif args.command == "ingest-image-pilot":
            print(json.dumps(ingest_image_pilot(store, args.source)))
        elif args.command == "ingest-serving-capture":
            print(json.dumps(ingest_serving_capture(store, args.source)))
        else:
            print(json.dumps(table_counts(store)))
    except (OSError, ReleaseError, TimeoutExpired, TypeError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
