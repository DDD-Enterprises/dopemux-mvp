-- DDDPG SQLite Cache Schema
-- Per-instance local cache for fast reads

-- Main decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    summary TEXT NOT NULL,
    rationale TEXT,
    implementation_details TEXT,
    
    -- Multi-instance support
    workspace_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'shared',  -- private, shared, global
    
    -- Classification
    status TEXT NOT NULL DEFAULT 'active',
    decision_type TEXT,
    tags TEXT,  -- JSON array
    
    -- User (optional - for auth mode)
    user_id TEXT,
    
    -- ADHD metadata
    cognitive_load INTEGER,
    
    -- Agent extensions
    agent_metadata TEXT,  -- JSON object
    code_references TEXT,  -- JSON array
    
    -- Graph relationships (stored as JSON array of IDs)
    related_decisions TEXT,  -- JSON array
    
    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT,
    
    -- Cache metadata
    cached_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cache_ttl INTEGER DEFAULT 3600  -- 1 hour TTL
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    summary, 
    rationale, 
    implementation_details,
    tags,
    content='decisions',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS decisions_ai AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, summary, rationale, implementation_details, tags)
    VALUES (new.id, new.summary, new.rationale, new.implementation_details, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS decisions_ad AFTER DELETE ON decisions BEGIN
    DELETE FROM decisions_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS decisions_au AFTER UPDATE ON decisions BEGIN
    DELETE FROM decisions_fts WHERE rowid = old.id;
    INSERT INTO decisions_fts(rowid, summary, rationale, implementation_details, tags)
    VALUES (new.id, new.summary, new.rationale, new.implementation_details, new.tags);
END;

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_workspace_instance ON decisions(workspace_id, instance_id);
CREATE INDEX IF NOT EXISTS idx_visibility ON decisions(visibility);
CREATE INDEX IF NOT EXISTS idx_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_created ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cached ON decisions(cached_at);

-- Work sessions table (optional - for ADHD tracking)
CREATE TABLE IF NOT EXISTS work_sessions (
    session_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    instance_id TEXT NOT NULL DEFAULT 'A',
    
    started_at TEXT NOT NULL,
    last_activity TEXT NOT NULL,
    ended_at TEXT,
    
    focus_level INTEGER,
    break_needed INTEGER DEFAULT 0,  -- Boolean
    context_preserved INTEGER DEFAULT 1,  -- Boolean
    
    current_file TEXT,
    current_decisions TEXT,  -- JSON array
    
    total_decisions_created INTEGER DEFAULT 0,
    total_decisions_viewed INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_session_workspace ON work_sessions(workspace_id, instance_id);
CREATE INDEX IF NOT EXISTS idx_session_active ON work_sessions(ended_at) WHERE ended_at IS NULL;
