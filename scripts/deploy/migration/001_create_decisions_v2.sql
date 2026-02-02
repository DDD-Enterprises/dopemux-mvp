-- ConPort Schema Upgrade: decisions_v2 Table
-- Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)
-- Creates upgraded schema with INTEGER IDs, JSONB fields, and AGE compatibility

CREATE TABLE decisions_v2 (
    -- PRIMARY KEY: SERIAL (auto-incrementing INTEGER) for AGE compatibility
    id SERIAL PRIMARY KEY,

    -- Core fields (preserved from original schema)
    workspace_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    rationale TEXT NOT NULL,

    -- NEW: AGE-required fields
    status VARCHAR(20) NOT NULL DEFAULT 'accepted' CHECK (
        status IN ('accepted', 'proposed', 'deprecated', 'superseded')
    ),
    implementation TEXT,

    -- Format updates: TEXT[] → JSONB
    tags JSONB DEFAULT '[]'::jsonb,
    alternatives JSONB DEFAULT '[]'::jsonb,

    -- Preserved fields from original schema
    confidence_level VARCHAR(20) DEFAULT 'medium' CHECK (
        confidence_level IN ('low', 'medium', 'high', 'certain')
    ),
    decision_type VARCHAR(50) DEFAULT 'implementation' CHECK (
        decision_type IN ('architecture', 'implementation', 'process', 'tool')
    ),

    -- Graph metadata (NEW)
    graph_version INTEGER DEFAULT 1 NOT NULL,
    hop_distance INTEGER,

    -- Timestamps (preserved)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Temporary mapping column for migration
    old_uuid UUID UNIQUE NOT NULL
);

-- Create indexes for optimal query performance
CREATE INDEX idx_decisions_v2_workspace ON decisions_v2(workspace_id);
CREATE INDEX idx_decisions_v2_status ON decisions_v2(status);
CREATE INDEX idx_decisions_v2_created ON decisions_v2(created_at DESC);
CREATE INDEX idx_decisions_v2_tags ON decisions_v2 USING GIN(tags);
CREATE INDEX idx_decisions_v2_decision_type ON decisions_v2(decision_type);
CREATE INDEX idx_decisions_v2_old_uuid ON decisions_v2(old_uuid);

-- Full-text search index
CREATE INDEX idx_decisions_v2_search ON decisions_v2 USING GIN(
    to_tsvector('english', summary || ' ' || rationale)
);

-- Trigger for automatic timestamp updates
CREATE TRIGGER update_decisions_v2_modtime
    BEFORE UPDATE ON decisions_v2
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

COMMENT ON TABLE decisions_v2 IS 'Upgraded decision schema with INTEGER PKs and JSONB fields for AGE migration';
COMMENT ON COLUMN decisions_v2.id IS 'Auto-incrementing INTEGER primary key (AGE-compatible)';
COMMENT ON COLUMN decisions_v2.status IS 'Decision status derived from confidence_level during migration';
COMMENT ON COLUMN decisions_v2.old_uuid IS 'Temporary mapping to original UUID for relationship migration';
