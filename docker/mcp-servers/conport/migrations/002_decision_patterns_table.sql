-- ============================================================================
-- ConPort Phase 3 Migration: Decision Patterns Table
-- ============================================================================
--
-- Creates decision_patterns table for auto-detected pattern storage.
-- Supports tag clustering, decision chains, timing patterns, energy correlation.
--
-- Created: 2025-10-17
-- Part of: ConPort Enhancement Phase 3 (Pattern Learning)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Create Decision Patterns Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,

    -- Pattern identification
    pattern_type VARCHAR(30) NOT NULL
        CHECK (pattern_type IN ('tag_cluster', 'decision_chain', 'timing_pattern', 'energy_correlation')),
    pattern_signature JSONB NOT NULL,  -- Defines the pattern (tag set, chain steps, etc.)
    pattern_name VARCHAR(255),         -- Human-readable name

    -- Occurrence statistics
    occurrence_count INT DEFAULT 1,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    mixed_count INT DEFAULT 0,

    -- Decision characteristics
    avg_confidence DECIMAL(3,2),
    avg_decision_time_minutes DECIMAL(6,2),
    avg_implementation_time_days DECIMAL(6,2),
    avg_cognitive_load DECIMAL(3,2),

    -- Temporal tracking
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- AI/ML metadata
    pattern_confidence DECIMAL(3,2)  -- How confident are we this is a real pattern?
        CHECK (pattern_confidence IS NULL OR (pattern_confidence >= 0.0 AND pattern_confidence <= 1.0)),
    recommendations JSONB DEFAULT '[]',  -- Generated recommendations
    adhd_insights JSONB DEFAULT '{}',   -- ADHD-specific insights

    -- Housekeeping
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(workspace_id, pattern_type, pattern_signature)
);

-- Indexes for pattern queries
CREATE INDEX IF NOT EXISTS idx_patterns_workspace ON decision_patterns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON decision_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_signature ON decision_patterns USING GIN(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON decision_patterns(pattern_confidence DESC)
    WHERE pattern_confidence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_patterns_last_seen ON decision_patterns(last_seen DESC);

COMMENT ON TABLE decision_patterns IS 'Auto-detected decision patterns for recommendations and success prediction';
COMMENT ON COLUMN decision_patterns.pattern_signature IS 'JSONB defining the pattern (e.g., tag set, chain sequence, timing window)';
COMMENT ON COLUMN decision_patterns.pattern_confidence IS 'Statistical confidence this is a real pattern (0.0-1.0)';
COMMENT ON COLUMN decision_patterns.recommendations IS 'Array of actionable recommendations based on this pattern';
COMMENT ON COLUMN decision_patterns.adhd_insights IS 'ADHD-specific insights (optimal timing, energy requirements, etc.)';

-- ============================================================================
-- Auto-update timestamp trigger
-- ============================================================================

CREATE TRIGGER update_patterns_modtime
    BEFORE UPDATE ON decision_patterns
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- ============================================================================
-- Pattern Statistics View (for quick queries)
-- ============================================================================

CREATE VIEW pattern_statistics AS
SELECT
    p.workspace_id,
    p.pattern_type,
    COUNT(*) as pattern_count,
    AVG(p.occurrence_count) as avg_occurrences,
    AVG(p.pattern_confidence) as avg_confidence,
    SUM(p.occurrence_count) as total_occurrences
FROM decision_patterns p
WHERE p.pattern_confidence > 0.7  -- Only high-confidence patterns
GROUP BY p.workspace_id, p.pattern_type;

COMMENT ON VIEW pattern_statistics IS 'Aggregated pattern statistics by workspace and type';

-- ============================================================================
-- Migration Metadata
-- ============================================================================

INSERT INTO custom_data (workspace_id, category, key, value, created_at)
VALUES (
    '_system',
    'migrations',
    '002_decision_patterns_table',
    jsonb_build_object(
        'applied_at', NOW(),
        'description', 'Decision Patterns table for Phase 3 pattern learning',
        'backward_compatible', true,
        'tables_added', jsonb_build_array('decision_patterns'),
        'views_added', jsonb_build_array('pattern_statistics'),
        'indexes_added', 5
    ),
    NOW()
)
ON CONFLICT (workspace_id, category, key) DO UPDATE
SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;

-- ============================================================================
-- Post-Migration Validation
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'decision_patterns') THEN
        RAISE EXCEPTION 'Migration validation failed: decision_patterns table not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'pattern_statistics') THEN
        RAISE EXCEPTION 'Migration validation failed: pattern_statistics view not created';
    END IF;

    RAISE NOTICE '✅ Migration 002 validated: decision_patterns table and views created';
END $$;
