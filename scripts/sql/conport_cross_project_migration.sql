-- ConPort Cross-Project Memory Migration
-- Extends ConPort from product-focused to cross-project memory hub
-- Adds three neutral namespaces: decisions/*, work/*, artifacts/*

-- Create namespace tables for cross-project memory
-- These are neutral and can be used across different projects/contexts

-- =====================================================
-- DECISIONS NAMESPACE: decisions/*
-- Atomic decision nodes with why, when, who, links
-- =====================================================

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,  -- Format: decisions/2025-11-01-uuid
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    rationale TEXT,
    implementation_details TEXT,
    who TEXT,  -- AI agent or human identifier
    when_ts TIMESTAMPTZ DEFAULT NOW(),
    links JSONB DEFAULT '[]'::jsonb,  -- Related entities (work items, artifacts, etc.)
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,  -- Additional context
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- WORK NAMESPACE: work/*
-- "Upcoming" queue and "done" history
-- =====================================================

CREATE TABLE IF NOT EXISTS work_items (
    id TEXT PRIMARY KEY,  -- Format: work/project-id-123
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'upcoming',  -- upcoming, in_progress, done, blocked
    priority TEXT DEFAULT 'medium',  -- low, medium, high, critical
    due_date DATE,
    source TEXT DEFAULT 'manual',  -- manual, leantime, task-orchestrator, ai
    source_ref TEXT,  -- Reference to external system (ticket ID, etc.)
    tags TEXT[] DEFAULT '{}',
    cognitive_load INTEGER DEFAULT 5,  -- ADHD complexity rating 1-10
    energy_required TEXT DEFAULT 'medium',  -- low, medium, high
    links JSONB DEFAULT '[]'::jsonb,  -- Related decisions, artifacts
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- =====================================================
-- ARTIFACTS NAMESPACE: artifacts/*
-- Screenshots, diffs, logs, PRs, etc.
-- =====================================================

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,  -- Format: artifacts/screenshot-uuid
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,  -- screenshot, diff, log, pr, trace, etc.
    title TEXT NOT NULL,
    description TEXT,
    path TEXT,  -- Local file path or S3 URL
    hash TEXT,  -- Content hash for integrity
    size_bytes BIGINT,
    mime_type TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    links JSONB DEFAULT '[]'::jsonb,  -- Related decisions, work items
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ  -- For temporary artifacts
);

-- =====================================================
-- KNOWLEDGE GRAPH EDGES
-- Cross-references between entities
-- =====================================================

CREATE TABLE IF NOT EXISTS knowledge_edges (
    id SERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,  -- decision, work_item, artifact
    source_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- implements, validates, depends_on, etc.
    description TEXT,
    weight REAL DEFAULT 1.0,  -- Strength of relationship
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure relationship is unique and prevent self-references
    UNIQUE(source_type, source_id, target_type, target_id, relationship_type),
    CHECK (source_type != target_type OR source_id != target_id)
);

-- =====================================================
-- VECTOR EMBEDDINGS FOR SEMANTIC SEARCH
-- Cross-project semantic retrieval
-- =====================================================

CREATE TABLE IF NOT EXISTS semantic_chunks (
    id TEXT PRIMARY KEY,  -- Format: semantic/decision-uuid-chunk-1
    entity_type TEXT NOT NULL,  -- decision, work_item, artifact
    entity_id TEXT NOT NULL,
    content TEXT NOT NULL,  -- Chunked text content
    embedding VECTOR(384),  -- Voyage embedding dimensions
    chunk_index INTEGER DEFAULT 0,  -- For multi-chunk entities
    total_chunks INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Decisions indexes
CREATE INDEX IF NOT EXISTS idx_decisions_workspace_created ON decisions(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_tags ON decisions USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_decisions_who ON decisions(who);
CREATE INDEX IF NOT EXISTS idx_decisions_links ON decisions USING gin(links);

-- Work items indexes
CREATE INDEX IF NOT EXISTS idx_work_items_workspace_status ON work_items(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_work_items_due_date ON work_items(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_work_items_priority ON work_items(priority);
CREATE INDEX IF NOT EXISTS idx_work_items_source ON work_items(source);
CREATE INDEX IF NOT EXISTS idx_work_items_cognitive_load ON work_items(cognitive_load);
CREATE INDEX IF NOT EXISTS idx_work_items_tags ON work_items USING gin(tags);

-- Artifacts indexes
CREATE INDEX IF NOT EXISTS idx_artifacts_workspace_kind ON artifacts(workspace_id, kind);
CREATE INDEX IF NOT EXISTS idx_artifacts_path ON artifacts(path);
CREATE INDEX IF NOT EXISTS idx_artifacts_expires ON artifacts(expires_at) WHERE expires_at IS NOT NULL;

-- Knowledge graph indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_relationship ON knowledge_edges(relationship_type);

-- Semantic search indexes
CREATE INDEX IF NOT EXISTS idx_semantic_chunks_entity ON semantic_chunks(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_semantic_chunks_vector ON semantic_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- =====================================================
-- MIGRATION TRIGGERS
-- Auto-update timestamps
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to new tables
DROP TRIGGER IF EXISTS update_decisions_updated_at ON decisions;
CREATE TRIGGER update_decisions_updated_at
    BEFORE UPDATE ON decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_work_items_updated_at ON work_items;
CREATE TRIGGER update_work_items_updated_at
    BEFORE UPDATE ON work_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- BACKWARD COMPATIBILITY
-- Map existing tables to new namespaces where possible
-- =====================================================

-- Note: Existing decisions, progress_entries tables remain for backward compatibility
-- New cross-project operations use the new namespace tables above
-- Migration scripts can copy existing data to new tables if needed

-- =====================================================
-- INITIAL DATA SEEDING
-- Example entries to demonstrate the schema
-- =====================================================

-- Insert example decision (uncomment to seed)
-- INSERT INTO decisions (id, workspace_id, title, rationale, who, tags)
-- VALUES ('decisions/2025-11-01-init', 'default', 'Adopt Task Orchestrator + ConPort architecture',
--         'Provides tactical execution with memory persistence for ADHD-optimized workflows',
--         'system', ARRAY['architecture', 'adhd-optimization']);

-- Insert example work item
-- INSERT INTO work_items (id, workspace_id, title, status, priority, source)
-- VALUES ('work/dopemux-init-1', 'default', 'Set up Task Orchestrator integration',
--         'upcoming', 'high', 'manual');

COMMENT ON TABLE decisions IS 'Cross-project decision log with rationale and links';
COMMENT ON TABLE work_items IS 'Unified work queue across projects and contexts';
COMMENT ON TABLE artifacts IS 'File artifacts with metadata and relationships';
COMMENT ON TABLE knowledge_edges IS 'Knowledge graph relationships between entities';
COMMENT ON TABLE semantic_chunks IS 'Vector embeddings for cross-project semantic search';