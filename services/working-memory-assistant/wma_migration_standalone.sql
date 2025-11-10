-- Working Memory Assistant Standalone Database Migration
-- WMA has its own PostgreSQL database (dopemux_knowledge_graph)
-- No foreign key dependencies on ConPort tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- WMA Context Snapshots Table
-- Stores compressed context snapshots for fast recovery
CREATE TABLE IF NOT EXISTS wma_context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL UNIQUE, -- Human-readable identifier
    user_id TEXT, -- ADHD user identifier
    session_id TEXT, -- Current work session

    -- Context metadata
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context_type TEXT NOT NULL CHECK (context_type IN ('manual', 'auto', 'attention_shift', 'scheduled')),
    emotional_weight NUMERIC(3,2) CHECK (emotional_weight >= 0 AND emotional_weight <= 1), -- 0.0-1.0 scale
    complexity_score NUMERIC(3,2) CHECK (complexity_score >= 0 AND complexity_score <= 1), -- ADHD cognitive load

    -- Snapshot data (compressed JSON)
    snapshot_data JSONB NOT NULL, -- Compressed context state
    snapshot_size_bytes INTEGER, -- Size tracking for memory management

    -- ADHD-aware prioritization
    attention_state TEXT CHECK (attention_state IN ('focused', 'scattered', 'transitioning')),
    energy_level TEXT CHECK (energy_level IN ('high', 'medium', 'low')),
    cognitive_load NUMERIC(3,2), -- Real-time load from ADHD Engine

    -- Recovery metadata
    recovery_count INTEGER DEFAULT 0,
    last_recovered_at TIMESTAMP WITH TIME ZONE,
    average_recovery_time_ms INTEGER,

    -- Integration metadata (references stored as text for external systems)
    linked_decision_id TEXT, -- Reference to ConPort decision ID
    linked_progress_id TEXT, -- Reference to ConPort progress entry ID

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WMA Recovery Sessions Table
-- Tracks recovery attempts and outcomes for analytics
CREATE TABLE IF NOT EXISTS wma_recovery_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id UUID REFERENCES wma_context_snapshots(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL,

    -- Recovery attempt metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    recovery_time_ms INTEGER, -- How long recovery took
    success BOOLEAN DEFAULT FALSE,

    -- Recovery context
    recovery_type TEXT NOT NULL CHECK (recovery_type IN ('full', 'progressive', 'selective')),
    user_feedback TEXT, -- Post-recovery feedback
    recovery_steps JSONB, -- Steps taken during recovery

    -- Performance metrics
    context_restored_percent NUMERIC(5,2), -- % of context successfully restored
    user_satisfaction_rating INTEGER CHECK (user_satisfaction_rating >= 1 AND user_satisfaction_rating <= 5),

    -- ADHD metrics during recovery
    attention_state_during_recovery TEXT CHECK (attention_state_during_recovery IN ('focused', 'scattered', 'transitioning')),
    cognitive_load_during_recovery NUMERIC(3,2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WMA Pattern Recognition Table
-- Learns from successful recoveries to improve future snapshots
CREATE TABLE IF NOT EXISTS wma_recovery_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id TEXT NOT NULL,

    -- Pattern identification
    pattern_hash TEXT NOT NULL UNIQUE, -- Hash of pattern characteristics
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('context_type', 'attention_shift', 'emotional_weight', 'complexity_threshold')),

    -- Pattern data
    pattern_data JSONB NOT NULL, -- Learned pattern characteristics
    success_rate NUMERIC(5,2), -- % of successful recoveries using this pattern
    usage_count INTEGER DEFAULT 0,

    -- Learning metadata
    first_observed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WMA Integration Links Table
-- Links WMA snapshots to external systems (ConPort, etc.)
CREATE TABLE IF NOT EXISTS wma_integration_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_id UUID REFERENCES wma_context_snapshots(id) ON DELETE CASCADE,

    -- External system links
    external_system TEXT NOT NULL, -- 'conport', 'serena', 'adhd_engine', etc.
    external_item_type TEXT NOT NULL, -- 'decision', 'progress_entry', 'system_pattern', etc.
    external_item_id TEXT NOT NULL, -- ID in external system

    -- Relationship metadata
    relationship_type TEXT NOT NULL,
    relationship_strength NUMERIC(3,2) CHECK (relationship_strength >= 0 AND relationship_strength <= 1),
    description TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_wma_snapshots_workspace_timestamp ON wma_context_snapshots(workspace_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_wma_snapshots_user_session ON wma_context_snapshots(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_wma_snapshots_emotional_complexity ON wma_context_snapshots(emotional_weight, complexity_score);
CREATE INDEX IF NOT EXISTS idx_wma_recovery_sessions_snapshot ON wma_recovery_sessions(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_wma_recovery_sessions_success_time ON wma_recovery_sessions(success, recovery_time_ms);
CREATE INDEX IF NOT EXISTS idx_wma_patterns_workspace_type ON wma_recovery_patterns(workspace_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_wma_integration_links_snapshot ON wma_integration_links(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_wma_integration_links_external ON wma_integration_links(external_system, external_item_type, external_item_id);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_wma_snapshots_fts ON wma_context_snapshots USING GIN (to_tsvector('english', snapshot_data::text));
CREATE INDEX IF NOT EXISTS idx_wma_recovery_fts ON wma_recovery_sessions USING GIN (to_tsvector('english', user_feedback));

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_wma_snapshots_updated_at BEFORE UPDATE ON wma_context_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wma_patterns_updated_at BEFORE UPDATE ON wma_recovery_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for analytics and reporting

-- Recovery performance view
CREATE OR REPLACE VIEW wma_recovery_performance AS
SELECT
    ws.workspace_id,
    COUNT(wrs.id) as total_recoveries,
    AVG(wrs.recovery_time_ms) as avg_recovery_time_ms,
    AVG(wrs.context_restored_percent) as avg_context_restored_percent,
    AVG(wrs.user_satisfaction_rating) as avg_satisfaction_rating,
    COUNT(CASE WHEN wrs.success THEN 1 END)::float / COUNT(*) as success_rate
FROM wma_context_snapshots ws
LEFT JOIN wma_recovery_sessions wrs ON ws.id = wrs.snapshot_id
GROUP BY ws.workspace_id;

-- Context snapshot analytics view
CREATE OR REPLACE VIEW wma_snapshot_analytics AS
SELECT
    workspace_id,
    context_type,
    COUNT(*) as snapshot_count,
    AVG(emotional_weight) as avg_emotional_weight,
    AVG(complexity_score) as avg_complexity_score,
    AVG(recovery_count) as avg_recovery_count,
    AVG(average_recovery_time_ms) as avg_recovery_time_ms
FROM wma_context_snapshots
GROUP BY workspace_id, context_type;

-- Migration metadata
COMMENT ON TABLE wma_context_snapshots IS 'Core WMA context snapshots with ADHD-aware prioritization and external system integration';
COMMENT ON TABLE wma_recovery_sessions IS 'Recovery attempt tracking for performance analytics and improvement';
COMMENT ON TABLE wma_recovery_patterns IS 'ML pattern recognition for optimizing future snapshots';
COMMENT ON TABLE wma_integration_links IS 'Links to external systems like ConPort for knowledge graph integration';

-- Grant permissions (adjust as needed for your deployment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO wma_user;
-- GRANT USAGE ON SCHEMA public TO wma_user;