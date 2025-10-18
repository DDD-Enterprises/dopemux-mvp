-- ============================================================================
-- ConPort Phase 1 Migration: Enhanced Decision Model
-- ============================================================================
--
-- Adds 14 new metadata fields to decisions table for:
-- - Confidence tracking and impact assessment
-- - Alternatives and success criteria
-- - Outcome tracking and lessons learned
-- - ADHD-specific metrics (cognitive load, decision time, energy level)
-- - Review workflow support
--
-- All fields are NULLABLE for backward compatibility
-- Existing decisions continue to work without modification
--
-- Created: 2025-10-17
-- Part of: ConPort Enhancement roadmap Phase 1
-- ============================================================================

BEGIN;

-- ============================================================================
-- Add Enhanced Decision Metadata Fields
-- ============================================================================

-- Context and confidence fields
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS impact_score DECIMAL(3,2)
        CHECK (impact_score IS NULL OR (impact_score >= 0.0 AND impact_score <= 1.0));

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS reversibility VARCHAR(20)
        CHECK (reversibility IS NULL OR reversibility IN ('easy', 'moderate', 'difficult', 'irreversible'));

COMMENT ON COLUMN decisions.impact_score IS 'Estimated impact (0.0-1.0): How significant is this decision?';
COMMENT ON COLUMN decisions.reversibility IS 'How easy is it to undo this decision?';

-- Alternatives and success criteria
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS alternatives_considered JSONB DEFAULT '[]';

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS success_criteria JSONB DEFAULT '[]';

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS review_date TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN decisions.alternatives_considered IS 'Array of alternative approaches that were considered but not chosen';
COMMENT ON COLUMN decisions.success_criteria IS 'Array of measurable criteria to evaluate if this decision was successful';
COMMENT ON COLUMN decisions.review_date IS 'Scheduled date to review this decision and assess outcomes';

-- Outcome tracking
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS outcome_status VARCHAR(20)
        CHECK (outcome_status IS NULL OR outcome_status IN ('pending', 'successful', 'failed', 'mixed', 'abandoned'));

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS outcome_notes TEXT;

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS outcome_date TIMESTAMP WITH TIME ZONE;

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS lessons_learned JSONB DEFAULT '[]';

COMMENT ON COLUMN decisions.outcome_status IS 'What happened after implementing this decision?';
COMMENT ON COLUMN decisions.outcome_notes IS 'Free-form notes about the actual outcome';
COMMENT ON COLUMN decisions.outcome_date IS 'When we learned the outcome (completion date)';
COMMENT ON COLUMN decisions.lessons_learned IS 'Array of insights gained from this decision';

-- ADHD-specific metadata
ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS cognitive_load DECIMAL(3,2)
        CHECK (cognitive_load IS NULL OR (cognitive_load >= 0.0 AND cognitive_load <= 1.0));

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS decision_time_minutes DECIMAL(6,2)
        CHECK (decision_time_minutes IS NULL OR decision_time_minutes > 0);

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS energy_level VARCHAR(10)
        CHECK (energy_level IS NULL OR energy_level IN ('low', 'medium', 'high'));

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS requires_followup BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN decisions.cognitive_load IS 'How mentally demanding was this decision? (0.0=trivial, 1.0=exhausting)';
COMMENT ON COLUMN decisions.decision_time_minutes IS 'How long did it take to make this decision?';
COMMENT ON COLUMN decisions.energy_level IS 'Energy level when decision was made (correlates with quality)';
COMMENT ON COLUMN decisions.requires_followup IS 'Flag for decisions needing future review or action';

-- Update confidence_level to use numeric scale (backward compatible)
-- Note: Existing VARCHAR values ('low', 'medium', 'high') will be migrated
-- via data migration script after schema change

COMMENT ON COLUMN decisions.confidence_level IS 'How confident are we in this decision? (low/medium/high or 0.0-1.0)';

-- ============================================================================
-- Create Decision Relationships Table (Decision Genealogy)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    source_decision_id UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    target_decision_id UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    relationship_type VARCHAR(30) NOT NULL
        CHECK (relationship_type IN (
            'builds_upon',
            'supersedes',
            'conflicts_with',
            'validates',
            'implements',
            'questions'
        )),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_decision_id, target_decision_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_decision_rel_source ON decision_relationships(source_decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_rel_target ON decision_relationships(target_decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_rel_type ON decision_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_decision_rel_workspace ON decision_relationships(workspace_id);

COMMENT ON TABLE decision_relationships IS 'Decision genealogy: tracks how decisions relate to each other';

-- ============================================================================
-- Create ADHD Metrics Table (replaces custom_data for energy tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS adhd_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    user_session_id VARCHAR(100),
    metric_type VARCHAR(30) NOT NULL
        CHECK (metric_type IN ('energy', 'focus', 'attention', 'interruption', 'context_switch')),
    value DECIMAL(5,2) NOT NULL,
    level VARCHAR(10),  -- For categorical values (low/medium/high)
    context_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_adhd_metrics_workspace ON adhd_metrics(workspace_id);
CREATE INDEX IF NOT EXISTS idx_adhd_metrics_type ON adhd_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_adhd_metrics_created ON adhd_metrics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adhd_metrics_session ON adhd_metrics(user_session_id);

COMMENT ON TABLE adhd_metrics IS 'Time-series ADHD metrics for energy, focus, and attention tracking';

-- ============================================================================
-- Create Review Reminders Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS review_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    decision_id UUID NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    reminder_type VARCHAR(30) NOT NULL
        CHECK (reminder_type IN ('implementation', 'outcome', 'periodic', 'low_confidence')),
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_reminders_decision ON review_reminders(decision_id);
CREATE INDEX IF NOT EXISTS idx_review_reminders_scheduled ON review_reminders(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_review_reminders_completed ON review_reminders(completed);
CREATE INDEX IF NOT EXISTS idx_review_reminders_workspace ON review_reminders(workspace_id);

COMMENT ON TABLE review_reminders IS 'Scheduled reminders to review decisions at appropriate times';

-- ============================================================================
-- Indexes for Enhanced Queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON decisions(outcome_status) WHERE outcome_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_review_date ON decisions(review_date) WHERE review_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_energy ON decisions(energy_level) WHERE energy_level IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_impact ON decisions(impact_score DESC) WHERE impact_score IS NOT NULL;

-- ============================================================================
-- Updated Views for Enhanced Data
-- ============================================================================

-- Drop old recent_activity view and recreate with enhanced fields
DROP VIEW IF EXISTS recent_activity;

CREATE VIEW recent_activity AS
SELECT
    'decision' as activity_type,
    id,
    workspace_id,
    summary as description,
    created_at,
    'decision' as icon,
    decision_type,
    confidence_level,
    outcome_status
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
    END as icon,
    NULL as decision_type,
    NULL as confidence_level,
    NULL as outcome_status
FROM progress_entries
ORDER BY created_at DESC;

-- Create view for decisions needing review
CREATE VIEW decisions_needing_review AS
SELECT
    d.id,
    d.workspace_id,
    d.summary,
    d.decision_type,
    d.confidence_level,
    d.created_at,
    d.review_date,
    d.outcome_status,
    EXTRACT(DAY FROM (NOW() - d.created_at)) as age_days,
    CASE
        WHEN d.created_at < NOW() - INTERVAL '90 days' THEN 'overdue'
        WHEN d.created_at < NOW() - INTERVAL '60 days' THEN 'due_soon'
        WHEN d.created_at < NOW() - INTERVAL '30 days' THEN 'review_suggested'
        ELSE 'recent'
    END as review_priority,
    CASE
        WHEN d.outcome_status IS NOT NULL THEN FALSE
        WHEN 'needs-review' = ANY(d.tags) THEN TRUE
        WHEN d.created_at < NOW() - INTERVAL '30 days' THEN TRUE
        ELSE FALSE
    END as needs_review
FROM decisions d
WHERE
    d.outcome_status IS NULL OR d.outcome_status = 'pending'
ORDER BY d.created_at ASC;

COMMENT ON VIEW decisions_needing_review IS 'Decisions that need review based on age, tags, or outcome status';

-- ============================================================================
-- Data Migration Helpers
-- ============================================================================

-- Migrate existing energy logs from custom_data to adhd_metrics
-- This will be run by separate data migration script after schema change

-- ============================================================================
-- Migration Metadata
-- ============================================================================

-- Record migration execution
INSERT INTO custom_data (workspace_id, category, key, value, created_at)
VALUES (
    '_system',
    'migrations',
    '001_enhanced_decision_model',
    jsonb_build_object(
        'applied_at', NOW(),
        'description', 'Enhanced Decision Model with 14 new fields',
        'backward_compatible', true,
        'tables_added', jsonb_build_array('decision_relationships', 'adhd_metrics', 'review_reminders'),
        'columns_added', 14,
        'indexes_added', 8,
        'views_updated', 2
    ),
    NOW()
)
ON CONFLICT (workspace_id, category, key) DO UPDATE
SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;

-- ============================================================================
-- Post-Migration Validation
-- ============================================================================

-- Verify new columns exist
DO $$
DECLARE
    missing_columns TEXT[];
    expected_columns TEXT[] := ARRAY[
        'impact_score', 'reversibility', 'alternatives_considered', 'success_criteria',
        'review_date', 'outcome_status', 'outcome_notes', 'outcome_date',
        'lessons_learned', 'cognitive_load', 'decision_time_minutes',
        'energy_level', 'requires_followup'
    ];
    col TEXT;
BEGIN
    FOREACH col IN ARRAY expected_columns
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'decisions'
            AND column_name = col
        ) THEN
            missing_columns := array_append(missing_columns, col);
        END IF;
    END LOOP;

    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Migration validation failed: missing columns: %', missing_columns;
    ELSE
        RAISE NOTICE '✅ Migration 001 validated: all 13 enhanced columns present';
    END IF;
END $$;

-- Verify new tables exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'decision_relationships') THEN
        RAISE EXCEPTION 'Migration validation failed: decision_relationships table not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'adhd_metrics') THEN
        RAISE EXCEPTION 'Migration validation failed: adhd_metrics table not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'review_reminders') THEN
        RAISE EXCEPTION 'Migration validation failed: review_reminders table not created';
    END IF;

    RAISE NOTICE '✅ Migration 001 validated: all 3 new tables present';
END $$;
