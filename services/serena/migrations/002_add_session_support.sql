-- Migration: 002_add_session_support.sql
-- Purpose: Add multi-session support to ConPort active_context table
-- Version: F002 v1.0
-- Date: 2025-10-18
-- Author: Claude Code
-- Status: Ready for deployment

-- ============================================================================
-- MIGRATION OVERVIEW
-- ============================================================================
-- Changes:
--   1. Add session_id, worktree_path, branch, last_updated, status columns
--   2. Change primary key from workspace_id to (workspace_id, session_id)
--   3. Create performance indexes
--   4. Add status constraints
--
-- Backward Compatibility:
--   - All new columns have defaults (session_id='default')
--   - Existing rows migrate automatically
--   - Old single-session queries still work during transition period
--
-- Rollback: See rollback section at end of file
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add New Columns with Defaults
-- ============================================================================
-- This allows existing data to migrate seamlessly

ALTER TABLE active_context
    ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS worktree_path TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- Update last_updated for existing rows (set to NOW if not already set)
UPDATE active_context
SET last_updated = NOW()
WHERE last_updated IS NULL;

-- ============================================================================
-- STEP 2: Create New Composite Primary Key
-- ============================================================================
-- Change from workspace_id alone to (workspace_id, session_id)

-- Drop existing primary key constraint
ALTER TABLE active_context
    DROP CONSTRAINT IF EXISTS active_context_pkey CASCADE;

-- Add new composite primary key
ALTER TABLE active_context
    ADD PRIMARY KEY (workspace_id, session_id);

-- ============================================================================
-- STEP 3: Create Performance Indexes
-- ============================================================================

-- Index for querying all sessions in workspace ordered by last activity
CREATE INDEX IF NOT EXISTS idx_active_context_workspace_updated
    ON active_context(workspace_id, last_updated DESC);

-- Partial index for active sessions only (performance optimization)
CREATE INDEX IF NOT EXISTS idx_active_context_status
    ON active_context(workspace_id, status)
    WHERE status = 'active';

-- Index for worktree-based queries
CREATE INDEX IF NOT EXISTS idx_active_context_worktree
    ON active_context(workspace_id, worktree_path)
    WHERE worktree_path IS NOT NULL;

-- Index for branch-based queries
CREATE INDEX IF NOT EXISTS idx_active_context_branch
    ON active_context(workspace_id, branch)
    WHERE branch IS NOT NULL;

-- ============================================================================
-- STEP 4: Add Constraints
-- ============================================================================

-- Status must be one of: active, completed, invalid_worktree
ALTER TABLE active_context
    ADD CONSTRAINT IF NOT EXISTS check_status
    CHECK (status IN ('active', 'completed', 'invalid_worktree'));

-- last_updated must not be in the future
ALTER TABLE active_context
    ADD CONSTRAINT IF NOT EXISTS check_last_updated
    CHECK (last_updated <= NOW());

-- ============================================================================
-- STEP 5: Create session_history Table
-- ============================================================================
-- Archive completed sessions for analytics

CREATE TABLE IF NOT EXISTS session_history (
    workspace_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    worktree_path TEXT,
    branch TEXT,
    content JSONB,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_minutes INTEGER,
    PRIMARY KEY (workspace_id, session_id),
    CONSTRAINT check_duration CHECK (duration_minutes >= 0),
    CONSTRAINT check_completion_order CHECK (
        completed_at IS NULL OR completed_at >= created_at
    )
);

-- Indexes for session_history
CREATE INDEX IF NOT EXISTS idx_session_history_workspace
    ON session_history(workspace_id, completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_history_branch
    ON session_history(workspace_id, branch)
    WHERE branch IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_session_history_duration
    ON session_history(workspace_id, duration_minutes DESC)
    WHERE duration_minutes IS NOT NULL;

-- ============================================================================
-- STEP 6: Create Helper Views (Optional)
-- ============================================================================

-- View: Active sessions with formatted time
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT
    workspace_id,
    session_id,
    worktree_path,
    branch,
    content->>'current_focus' as focus,
    EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60 as minutes_ago,
    status,
    last_updated
FROM active_context
WHERE status = 'active'
  AND last_updated > NOW() - INTERVAL '24 hours'
ORDER BY last_updated DESC;

-- View: Session statistics per workspace
CREATE OR REPLACE VIEW v_workspace_session_stats AS
SELECT
    workspace_id,
    COUNT(*) as total_active_sessions,
    COUNT(DISTINCT worktree_path) as unique_worktrees,
    MAX(last_updated) as most_recent_activity,
    MIN(last_updated) as oldest_session
FROM active_context
WHERE status = 'active'
GROUP BY workspace_id;

-- ============================================================================
-- STEP 7: Optimize Table
-- ============================================================================

VACUUM ANALYZE active_context;
VACUUM ANALYZE session_history;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMIT;

-- Migration success log
DO $$
BEGIN
    RAISE NOTICE 'Migration 002_add_session_support.sql completed successfully';
    RAISE NOTICE 'Active context now supports multi-session with composite key (workspace_id, session_id)';
    RAISE NOTICE 'New table session_history created for archiving';
    RAISE NOTICE 'All existing rows migrated with session_id=default';
END $$;

-- ============================================================================
-- ROLLBACK PLAN (Run if migration needs to be reverted)
-- ============================================================================
-- IMPORTANT: Only run this if absolutely necessary
-- Data may be lost if sessions were created after migration

/*
BEGIN;

-- Drop new constraints
ALTER TABLE active_context DROP CONSTRAINT IF EXISTS check_status;
ALTER TABLE active_context DROP CONSTRAINT IF EXISTS check_last_updated;

-- Restore original primary key
ALTER TABLE active_context DROP CONSTRAINT IF EXISTS active_context_pkey;
ALTER TABLE active_context ADD PRIMARY KEY (workspace_id);

-- Drop new columns
ALTER TABLE active_context DROP COLUMN IF EXISTS session_id;
ALTER TABLE active_context DROP COLUMN IF EXISTS worktree_path;
ALTER TABLE active_context DROP COLUMN IF EXISTS branch;
ALTER TABLE active_context DROP COLUMN IF EXISTS last_updated;
ALTER TABLE active_context DROP COLUMN IF EXISTS status;

-- Drop new indexes
DROP INDEX IF EXISTS idx_active_context_workspace_updated;
DROP INDEX IF EXISTS idx_active_context_status;
DROP INDEX IF EXISTS idx_active_context_worktree;
DROP INDEX IF EXISTS idx_active_context_branch;

-- Drop new table
DROP TABLE IF EXISTS session_history;

-- Drop views
DROP VIEW IF EXISTS v_active_sessions;
DROP VIEW IF EXISTS v_workspace_session_stats;

COMMIT;

-- Rollback complete
*/

-- ============================================================================
-- TESTING QUERIES (Run these to verify migration)
-- ============================================================================

-- Test 1: Check schema
/*
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'active_context'
ORDER BY ordinal_position;
*/

-- Test 2: Check primary key
/*
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'active_context';
*/

-- Test 3: Check indexes
/*
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'active_context';
*/

-- Test 4: Check existing data migrated
/*
SELECT workspace_id, session_id, status, last_updated
FROM active_context
LIMIT 10;
*/

-- Test 5: Test multi-session insert
/*
INSERT INTO active_context (workspace_id, session_id, content, branch, status)
VALUES
    ('/test/repo', 'session_test1_123', '{"focus": "Test 1"}', 'main', 'active'),
    ('/test/repo', 'session_test2_456', '{"focus": "Test 2"}', 'feature/test', 'active');

SELECT * FROM active_context WHERE workspace_id = '/test/repo';

-- Cleanup test data
DELETE FROM active_context WHERE workspace_id = '/test/repo';
*/
