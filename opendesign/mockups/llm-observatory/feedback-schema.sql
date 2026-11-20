CREATE TABLE IF NOT EXISTS feedback_submission (
  id TEXT PRIMARY KEY NOT NULL,
  request_id TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  message TEXT NOT NULL,
  context_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'reviewed'))
);

CREATE TABLE IF NOT EXISTS feedback_resolution (
  receipt_id TEXT PRIMARY KEY NOT NULL REFERENCES feedback_submission(id),
  public_path TEXT NOT NULL
);
