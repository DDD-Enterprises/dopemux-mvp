PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_databases (
    source_db_slug TEXT PRIMARY KEY,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_schema_class TEXT NOT NULL CHECK (source_schema_class IN ('modern', 'legacy', 'unknown')),
    source_mtime_utc TEXT NOT NULL,
    source_table TEXT NOT NULL DEFAULT 'DATABASE_INDEX.csv',
    source_row_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    bytes INTEGER NOT NULL DEFAULT 0,
    table_count INTEGER NOT NULL DEFAULT 0,
    work_items_count INTEGER NOT NULL DEFAULT 0,
    dependencies_count INTEGER NOT NULL DEFAULT 0,
    notes_count INTEGER NOT NULL DEFAULT 0,
    role_transitions_count INTEGER NOT NULL DEFAULT 0,
    queue_count INTEGER NOT NULL DEFAULT 0,
    work_count INTEGER NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    blocked_count INTEGER NOT NULL DEFAULT 0,
    terminal_count INTEGER NOT NULL DEFAULT 0,
    adjudication_class TEXT NOT NULL,
    canonical_treatment TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_work_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    parent_source_row_id TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    role TEXT NOT NULL,
    status_label TEXT,
    priority TEXT,
    complexity TEXT,
    tags TEXT,
    item_type TEXT,
    claimed_by TEXT,
    claim_expires_at TEXT,
    created_at TEXT,
    modified_at TEXT,
    role_changed_at TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    description_redacted TEXT,
    UNIQUE (source_db_slug, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS source_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    from_source_row_id TEXT NOT NULL,
    from_title TEXT,
    to_source_row_id TEXT NOT NULL,
    to_title TEXT,
    dependency_type TEXT,
    unblock_at TEXT,
    created_at TEXT,
    UNIQUE (source_db_slug, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS source_note_indexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    item_source_row_id TEXT NOT NULL,
    item_title TEXT,
    note_key TEXT NOT NULL,
    note_role TEXT,
    body_len INTEGER,
    body_sha256 TEXT,
    actor_id TEXT,
    actor_kind TEXT,
    actor_proof TEXT,
    verification_status TEXT,
    created_at TEXT,
    modified_at TEXT,
    UNIQUE (source_db_slug, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS source_role_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    item_source_row_id TEXT NOT NULL,
    item_title TEXT,
    from_role TEXT,
    to_role TEXT,
    from_status_label TEXT,
    to_status_label TEXT,
    trigger TEXT,
    summary TEXT,
    actor_id TEXT,
    actor_kind TEXT,
    actor_proof TEXT,
    verification_status TEXT,
    transitioned_at TEXT,
    UNIQUE (source_db_slug, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS source_root_overviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    root_source_row_id TEXT NOT NULL,
    root_role TEXT,
    root_status_label TEXT,
    priority TEXT,
    tags TEXT,
    title TEXT NOT NULL,
    child_queue INTEGER NOT NULL DEFAULT 0,
    child_work INTEGER NOT NULL DEFAULT 0,
    child_review INTEGER NOT NULL DEFAULT 0,
    child_blocked INTEGER NOT NULL DEFAULT 0,
    child_terminal INTEGER NOT NULL DEFAULT 0,
    direct_children INTEGER NOT NULL DEFAULT 0,
    UNIQUE (source_db_slug, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS reconciliation_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_ref TEXT,
    created_at_utc TEXT NOT NULL,
    UNIQUE (source_db_slug, decision_type, source_table, source_row_id)
);

CREATE TABLE IF NOT EXISTS canonical_current_work_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_db_slug TEXT NOT NULL REFERENCES source_databases(source_db_slug) ON DELETE CASCADE,
    source_database_path TEXT NOT NULL,
    source_schema_hash TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_mtime_utc TEXT NOT NULL,
    import_run_id TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    canonical_identity TEXT NOT NULL,
    role TEXT NOT NULL,
    status_label TEXT,
    priority TEXT,
    tags TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    decision_id INTEGER NOT NULL REFERENCES reconciliation_decisions(id) ON DELETE RESTRICT,
    UNIQUE (canonical_identity)
);

CREATE INDEX IF NOT EXISTS idx_source_work_items_title
    ON source_work_items(title);

CREATE INDEX IF NOT EXISTS idx_source_work_items_db_role
    ON source_work_items(source_db_slug, role);

CREATE INDEX IF NOT EXISTS idx_reconciliation_decisions_type
    ON reconciliation_decisions(decision_type, decision);
