-- Migration: 002_add_session_support_final.sql
-- Purpose: Add multi-session support to ConPort workspace_contexts
-- Adapted for existing ConPort schema with PostgreSQL-compatible syntax
-- Version: F002 v1.0 (Final - PostgreSQL Compatible)
-- Date: 2025-10-18

BEGIN;

-- ============================================================================
-- STEP 1: Add New Columns
-- ============================================================================

ALTER TABLE ag_catalog.workspace_contexts
    ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS worktree_path TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- Ensure existing rows have default session_id
UPDATE ag_catalog.workspace_contexts
SET session_id = 'default'
WHERE session_id IS NULL OR session_id = '';

-- ============================================================================
-- STEP 2: Create Unique Constraint (with error handling)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'idx_workspace_session_unique'
    ) THEN
        CREATE UNIQUE INDEX idx_workspace_session_unique
            ON ag_catalog.workspace_contexts(workspace_id, session_id);
    END IF;
END $$;

-- ============================================================================
-- STEP 3: Create Performance Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_workspace_contexts_workspace_updated
    ON ag_catalog.workspace_contexts(workspace_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_workspace_contexts_status
    ON ag_catalog.workspace_contexts(workspace_id, status)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_workspace_contexts_worktree
    ON ag_catalog.workspace_contexts(workspace_id, worktree_path)
    WHERE worktree_path IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workspace_contexts_branch
    ON ag_catalog.workspace_contexts(workspace_id, branch)
    WHERE branch IS NOT NULL;

-- ============================================================================
-- STEP 4: Add Constraints (with error handling)
-- ============================================================================

DO $$
BEGIN
    -- Add status constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_status_valid'
          AND conrelid = 'ag_catalog.workspace_contexts'::regclass
    ) THEN
        ALTER TABLE ag_catalog.workspace_contexts
            ADD CONSTRAINT check_status_valid
            CHECK (status IN ('active', 'completed', 'invalid_worktree'));
    END IF;

    -- Add updated_at constraint if not exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_updated_at_valid'
          AND conrelid = 'ag_catalog.workspace_contexts'::regclass
    ) THEN
        ALTER TABLE ag_catalog.workspace_contexts
            ADD CONSTRAINT check_updated_at_valid
            CHECK (updated_at <= NOW());
    END IF;
END $$;

-- ============================================================================
-- STEP 5: Create session_history Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS ag_catalog.session_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    worktree_path TEXT,
    branch TEXT,
    active_context TEXT,
    session_time TEXT,
    focus_state TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    CONSTRAINT session_history_unique UNIQUE (workspace_id, session_id),
    CONSTRAINT check_duration_positive CHECK (duration_minutes >= 0),
    CONSTRAINT check_completion_order CHECK (
        completed_at IS NULL OR completed_at >= created_at
    )
);

-- Indexes for session_history
CREATE INDEX IF NOT EXISTS idx_session_history_workspace
    ON ag_catalog.session_history(workspace_id, completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_history_branch
    ON ag_catalog.session_history(workspace_id, branch)
    WHERE branch IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_session_history_duration
    ON ag_catalog.session_history(workspace_id, duration_minutes DESC)
    WHERE duration_minutes IS NOT NULL;

-- ============================================================================
-- STEP 6: Create Helper Views
-- ============================================================================

CREATE OR REPLACE VIEW ag_catalog.v_active_sessions AS
SELECT
    id,
    workspace_id,
    session_id,
    worktree_path,
    branch,
    active_context as focus,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as minutes_ago,
    status,
    updated_at,
    session_time,
    focus_state
FROM ag_catalog.workspace_contexts
WHERE status = 'active'
  AND updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;

CREATE OR REPLACE VIEW ag_catalog.v_workspace_session_stats AS
SELECT
    workspace_id,
    COUNT(*) as total_active_sessions,
    COUNT(DISTINCT worktree_path) as unique_worktrees,
    MAX(updated_at) as most_recent_activity,
    MIN(updated_at) as oldest_session
FROM ag_catalog.workspace_contexts
WHERE status = 'active'
GROUP BY workspace_id;

-- ============================================================================
-- STEP 7: Optimize
-- ============================================================================

VACUUM ANALYZE ag_catalog.workspace_contexts;

COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

\echo '✅ Migration completed! Verifying...'

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'ag_catalog'
  AND table_name = 'workspace_contexts'
ORDER BY ordinal_position;

\echo ''
\echo 'Existing data:'
SELECT workspace_id, session_id, status, branch FROM ag_catalog.workspace_contexts;

\echo ''
\echo '✅ F002 Migration Complete!'
