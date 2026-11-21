"""Private, versioned intake for contributor-reported benchmarks."""

import json
from pathlib import Path

from fastest_release import CONTRIBUTOR_RECEIPT_PATH, ReleaseNotFound, ReleaseStore, _sql_text
from fastest_release.validation import validate

from .validation import candidate, decode, identifier, review_decision, submission_issues, version_number


class ContributorStore:
    """Write editor-only intake records and read safe receipts."""

    def __init__(self, database_url):
        self.release = ReleaseStore(database_url)

    def migrate(self):
        self.release._query(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))

    def submit(self, raw):
        record = decode(raw)
        issues, owner = submission_issues(record)
        if not issues:
            metric = record["metric"]
            registered = self.release._query(f"""
                SELECT EXISTS (
                    SELECT FROM fastest_release.metric_definition
                    WHERE metric_key = {_sql_text(metric["id"])} AND version = {metric["version"]}
                      AND unit = {_sql_text(metric["unit"])} AND statistic = {_sql_text(metric["statistic"])}
                      AND boundary = {_sql_text(metric["boundary"])}
                );
            """)
            if registered != "t":
                issues.append("unregistered_metric")
        owner_sql = _sql_text(owner) if owner is not None else "NULL"
        receipt = self.release._query(f"""
            SELECT fastest_contributor.submit_record(
                '{record["submission_id"]}'::uuid, {record["version"]}, {owner_sql},
                {_sql_text(raw)}, {_sql_text(json.dumps(issues))}::jsonb
            );
        """)
        return self.status(receipt)

    def status(self, receipt):
        identifier(receipt, "Receipt")
        status = self.release._query(f"SELECT fastest_contributor.receipt_status('{receipt}'::uuid);")
        if not status:
            raise ReleaseNotFound("Contributor receipt")
        result = json.loads(status)
        result["status_url"] = f"{CONTRIBUTOR_RECEIPT_PATH}?id={result['receipt']}"
        return result

    def inspect(self, receipt, version):
        identifier(receipt, "Receipt")
        version_number(version)
        record = self.release._query(f"""
            SELECT jsonb_build_object(
                'submission', entry.document, 'issues', entry.issues, 'review', entry.review,
                'evidence_id', submission.evidence_id, 'received_at', entry.received_at
            )
            FROM fastest_contributor.submission AS submission
            JOIN fastest_contributor.entry AS entry USING (submission_id)
            WHERE submission.receipt = '{receipt}'::uuid AND entry.version = {version};
        """)
        if not record:
            raise ReleaseNotFound("Contributor submission version")
        return json.loads(record)

    def review(self, receipt, version, decision):
        review_decision(decision)
        entry = self.inspect(receipt, version)
        observation_sql = "NULL"
        if decision["outcome"] == "publish":
            if entry["issues"]:
                raise ValueError("Quarantined submissions require a valid amended version before publication")
            record = decode(entry["submission"])
            if decision["editor_id"].casefold() == record["authorization"]["contributor_id"].casefold():
                raise ValueError("Publication requires an independent editor")
            observation = candidate(record, entry["evidence_id"], decision["decision_id"])
            validate(observation)
            observation_sql = _sql_text(json.dumps(observation, ensure_ascii=False)) + "::jsonb"
        self.release._query(f"""
            SELECT fastest_contributor.review_entry(
                '{receipt}'::uuid, {version}, {_sql_text(json.dumps(decision))}::jsonb, {observation_sql}
            );
        """)
        return self.status(receipt)
