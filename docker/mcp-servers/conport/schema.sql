-- ConPort ADHD Memory Persistence Schema
-- Optimized for context preservation and decision tracking

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================================
-- WORKSPACE CONTEXTS
-- =====================================================================

CREATE TABLE workspace_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    active_context TEXT,
    last_activity TEXT,
    session_time VARCHAR(50),
    focus_state VARCHAR(50),
    session_milestone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_workspace_contexts_workspace_id ON workspace_contexts(workspace_id);
CREATE INDEX idx_workspace_contexts_updated_at ON workspace_contexts(updated_at);

-- =====================================================================
-- DECISIONS & RATIONALE
-- =====================================================================

CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    rationale TEXT NOT NULL,
    alternatives JSONB DEFAULT '[]',
    tags TEXT[] DEFAULT '{}',
    confidence_level VARCHAR(20) DEFAULT 'medium',
    decision_type VARCHAR(50) DEFAULT 'implementation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_decisions_workspace_id ON decisions(workspace_id);
CREATE INDEX idx_decisions_created_at ON decisions(created_at DESC);
CREATE INDEX idx_decisions_type ON decisions(decision_type);
CREATE INDEX idx_decisions_tags ON decisions USING GIN(tags);

-- Full-text search index for decisions
CREATE INDEX idx_decisions_search ON decisions USING GIN(
    to_tsvector('english', summary || ' ' || rationale)
);

-- =====================================================================
-- PROGRESS TRACKING
-- =====================================================================

CREATE TABLE progress_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'CANCELLED')),
    percentage INTEGER DEFAULT 0 CHECK (percentage >= 0 AND percentage <= 100),
    linked_decision_id UUID REFERENCES decisions(id),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_progress_workspace_id ON progress_entries(workspace_id);
CREATE INDEX idx_progress_status ON progress_entries(status);
CREATE INDEX idx_progress_created_at ON progress_entries(created_at DESC);
CREATE INDEX idx_progress_decision_link ON progress_entries(linked_decision_id);

-- =====================================================================
-- SESSION TRACKING (ADHD-specific)
-- =====================================================================

CREATE TABLE session_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    focus_duration_minutes INTEGER,
    interruption_count INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    context_switches INTEGER DEFAULT 0,
    session_quality VARCHAR(20) CHECK (session_quality IN ('poor', 'fair', 'good', 'excellent')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_workspace_id ON session_snapshots(workspace_id);
CREATE INDEX idx_sessions_start_time ON session_snapshots(session_start DESC);

-- =====================================================================
-- KNOWLEDGE GRAPH RELATIONSHIPS
-- =====================================================================

CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,     -- 'decision', 'progress', 'context'
    source_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'implements', 'blocks', 'relates_to', 'caused_by'
    strength DECIMAL(3,2) DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_relationships_workspace_id ON entity_relationships(workspace_id);
CREATE INDEX idx_relationships_source ON entity_relationships(source_type, source_id);
CREATE INDEX idx_relationships_target ON entity_relationships(target_type, target_id);
CREATE INDEX idx_relationships_type ON entity_relationships(relationship_type);

-- =====================================================================
-- ADHD-OPTIMIZED SEARCH & DISCOVERY
-- =====================================================================

CREATE TABLE search_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL, -- MD5 hash of normalized query
    results JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 hour'
);

CREATE INDEX idx_search_cache_hash ON search_cache(workspace_id, query_hash);
CREATE INDEX idx_search_cache_expires ON search_cache(expires_at);

-- =====================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================================

-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workspace_contexts_modtime
    BEFORE UPDATE ON workspace_contexts
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_decisions_modtime
    BEFORE UPDATE ON decisions
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_progress_modtime
    BEFORE UPDATE ON progress_entries
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Auto-complete progress entries when percentage reaches 100%
CREATE OR REPLACE FUNCTION auto_complete_progress()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.percentage = 100 AND OLD.percentage < 100 THEN
        NEW.status = 'COMPLETED';
        NEW.completed_at = NOW();
    ELSIF NEW.percentage < 100 AND OLD.status = 'COMPLETED' THEN
        NEW.status = 'IN_PROGRESS';
        NEW.completed_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER auto_complete_progress_trigger
    BEFORE UPDATE ON progress_entries
    FOR EACH ROW EXECUTE FUNCTION auto_complete_progress();

-- =====================================================================
-- USEFUL VIEWS FOR ADHD WORKFLOW
-- =====================================================================

-- Recent activity summary for quick context loading
CREATE VIEW recent_activity AS
SELECT
    'decision' as activity_type,
    id,
    workspace_id,
    summary as description,
    created_at,
    'decision' as icon
FROM decisions
UNION ALL
SELECT
    'progress' as activity_type,
    id,
    workspace_id,
    description,
    updated_at as created_at,
    CASE status
        WHEN 'COMPLETED' THEN 'check'
        WHEN 'IN_PROGRESS' THEN 'clock'
        WHEN 'BLOCKED' THEN 'alert'
        ELSE 'task'
    END as icon
FROM progress_entries
ORDER BY created_at DESC;

-- Active work view for ADHD focus
CREATE VIEW active_work AS
SELECT
    p.id,
    p.workspace_id,
    p.description,
    p.status,
    p.percentage,
    p.priority,
    p.created_at,
    d.summary as related_decision,
    d.rationale as decision_context
FROM progress_entries p
LEFT JOIN decisions d ON p.linked_decision_id = d.id
WHERE p.status IN ('IN_PROGRESS', 'PLANNED')
ORDER BY
    CASE p.priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    p.created_at;

-- =====================================================================
-- INITIAL DATA MIGRATION (from mock data)
-- =====================================================================

-- Insert initial context for existing workspace
INSERT INTO workspace_contexts (workspace_id, active_context, last_activity, session_time, focus_state)
VALUES ('dopemux-mvp', 'Unified Architecture - Implementation Phase', 'ConPort database persistence implementation', '90 minutes', 'deep work')
ON CONFLICT (workspace_id) DO UPDATE SET
    active_context = EXCLUDED.active_context,
    last_activity = EXCLUDED.last_activity,
    session_time = EXCLUDED.session_time,
    focus_state = EXCLUDED.focus_state,
    updated_at = NOW();

-- Insert initial decision from our analysis
INSERT INTO decisions (workspace_id, summary, rationale, decision_type, tags)
VALUES ('dopemux-mvp',
        'Implement hybrid database backend for ConPort persistence',
        'Provides real ADHD memory persistence while maintaining current stability. Uses PostgreSQL for durability and Redis for fast 30-second auto-saves.',
        'architecture',
        ARRAY['architecture', 'persistence', 'adhd-optimization'])
ON CONFLICT DO NOTHING;

-- Insert initial progress entry
INSERT INTO progress_entries (workspace_id, description, status, percentage, priority)
VALUES ('dopemux-mvp',
        'ConPort database persistence implementation',
        'IN_PROGRESS',
        75,
        'high')
ON CONFLICT DO NOTHING;

-- Grant permissions to dopemux user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dopemux;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dopemux;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO dopemux;