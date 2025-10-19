-- Migration: 002_add_session_support_adapted.sql
-- Purpose: Add multi-session support to ConPort workspace_contexts table
-- Adapted for existing ConPort schema (ag_catalog.workspace_contexts)
-- Version: F002 v1.0 (Adapted)
-- Date: 2025-10-18
-- Database: dopemux_knowledge_graph
-- User: dopemux_age

-- ============================================================================
-- MIGRATION OVERVIEW (Adapted for ConPort)
-- ============================================================================
-- Current Table: ag_catalog.workspace_contexts
-- Current Columns: id, workspace_id, active_context, last_activity,
--                  session_time, focus_state, session_milestone,
--                  created_at, updated_at
--
-- Changes:
--   1. Add session_id column (default 'default' for backward compat)
--   2. Add worktree_path, branch columns for F002
--   3. Add status column (active/completed/invalid_worktree)
--   4. Create unique constraint on (workspace_id, session_id)
--   5. Create performance indexes
--   6. Create session_history table for completed sessions
--
-- Note: Preserving existing id (UUID) as technical PK
--       Adding unique constraint on (workspace_id, session_id) for business logic
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add New Columns to workspace_contexts
-- ============================================================================

ALTER TABLE ag_catalog.workspace_contexts
    ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS worktree_path TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- Ensure existing row has default session_id
UPDATE ag_catalog.workspace_contexts
SET session_id = 'default'
WHERE session_id IS NULL OR session_id = '';

-- ============================================================================
-- STEP 2: Create Unique Constraint (Business Logic PK)
-- ============================================================================
-- Keep id as technical PK, add unique constraint for (workspace_id, session_id)

CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_session_unique
    ON ag_catalog.workspace_contexts(workspace_id, session_id);

-- ============================================================================
-- STEP 3: Create Performance Indexes
-- ============================================================================

-- Index for querying all sessions in workspace ordered by last activity
CREATE INDEX IF NOT EXISTS idx_workspace_contexts_workspace_updated
    ON ag_catalog.workspace_contexts(workspace_id, updated_at DESC);

-- Partial index for active sessions only
CREATE INDEX IF NOT EXISTS idx_workspace_contexts_status
    ON ag_catalog.workspace_contexts(workspace_id, status)
    WHERE status = 'active';

-- Index for worktree-based queries
CREATE INDEX IF NOT EXISTS idx_workspace_contexts_worktree
    ON ag_catalog.workspace_contexts(workspace_id, worktree_path)
    WHERE worktree_path IS NOT NULL;

-- Index for branch-based queries
CREATE INDEX IF NOT EXISTS idx_workspace_contexts_branch
    ON ag_catalog.workspace_contexts(workspace_id, branch)
    WHERE branch IS NOT NULL;

-- ============================================================================
-- STEP 4: Add Constraints
-- ============================================================================

-- Status must be valid
ALTER TABLE ag_catalog.workspace_contexts
    ADD CONSTRAINT IF NOT EXISTS check_status_valid
    CHECK (status IN ('active', 'completed', 'invalid_worktree'));

-- updated_at must not be in the future
ALTER TABLE ag_catalog.workspace_contexts
    ADD CONSTRAINT IF NOT EXISTS check_updated_at_valid
    CHECK (updated_at <= NOW());

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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
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

-- View: Active sessions with formatted time
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

-- View: Session statistics per workspace
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
-- STEP 7: Optimize Tables
-- ============================================================================

VACUUM ANALYZE ag_catalog.workspace_contexts;
VACUUM ANALYZE ag_catalog.session_history;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMIT;

-- Success log
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002_add_session_support_adapted.sql completed';
    RAISE NOTICE '   workspace_contexts now supports multi-session';
    RAISE NOTICE '   Added: session_id, worktree_path, branch, status columns';
    RAISE NOTICE '   Created: session_history table';
    RAISE NOTICE '   Created: v_active_sessions, v_workspace_session_stats views';
    RAISE NOTICE '   Unique constraint: (workspace_id, session_id)';
END $$;

-- ============================================================================
-- TESTING QUERIES
-- ============================================================================

-- Test 1: Check new columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'ag_catalog'
  AND table_name = 'workspace_contexts'
ORDER BY ordinal_position;

-- Test 2: Check existing data migrated
SELECT workspace_id, session_id, status, branch
FROM ag_catalog.workspace_contexts;

-- Test 3: Test multi-session insert
/*
INSERT INTO ag_catalog.workspace_contexts
    (workspace_id, session_id, active_context, branch, status, worktree_path)
VALUES
    ('dopemux-mvp', 'session_test1_123', 'Testing session 1', 'main', 'active', NULL),
    ('dopemux-mvp', 'session_test2_456', 'Testing session 2', 'feature/test', 'active', '/test/worktree');

SELECT * FROM ag_catalog.workspace_contexts WHERE workspace_id = 'dopemux-mvp';

-- Cleanup
DELETE FROM ag_catalog.workspace_contexts WHERE session_id LIKE 'session_test%';
*/

-- Test 4: Check views work
SELECT * FROM ag_catalog.v_active_sessions;
SELECT * FROM ag_catalog.v_workspace_session_stats;
