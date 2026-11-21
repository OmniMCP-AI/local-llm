BEGIN;

CREATE SCHEMA IF NOT EXISTS fastest_github_intake;

CREATE TABLE IF NOT EXISTS fastest_github_intake.issue (
    repository text NOT NULL CHECK (repository = 'OmniMCP-AI/local-llm'),
    issue_id bigint NOT NULL CHECK (issue_id > 0),
    issue_number bigint NOT NULL CHECK (issue_number > 0),
    kind text NOT NULL CHECK (kind IN ('benchmark_request', 'result_correction')),
    status text NOT NULL CHECK (status IN ('open', 'closed', 'deleted')),
    revision timestamptz NOT NULL,
    url text GENERATED ALWAYS AS ('https://github.com/' || repository || '/issues/' || issue_number::text) STORED,
    PRIMARY KEY (repository, issue_id),
    UNIQUE (repository, issue_number)
);

COMMIT;
