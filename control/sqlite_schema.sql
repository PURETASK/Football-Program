-- NFL FIDOS Stage 21 foundation schema.
-- Canonical records are versioned; audit events are append-only.
CREATE TABLE IF NOT EXISTS canonical_records (
  collection TEXT NOT NULL,
  record_id TEXT NOT NULL,
  revision INTEGER NOT NULL,
  data_json TEXT NOT NULL,
  saved_at TEXT NOT NULL,
  saved_by TEXT NOT NULL,
  organization_id TEXT,
  PRIMARY KEY (collection, record_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  collection TEXT NOT NULL,
  record_id TEXT NOT NULL,
  revision INTEGER NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL,
  occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_events(collection, record_id, revision);
CREATE INDEX IF NOT EXISTS idx_canonical_organization ON canonical_records(organization_id);
