-- Migration 007: Minimal Worktree Multi-Instance Support
-- Purpose: Add instance_id columns for worktree isolation (MVP - Simple Version)
-- Date: 2025-10-04
-- Decision: #179

BEGIN;

-- =====================================================================
-- ADD INSTANCE TRACKING COLUMNS
-- =====================================================================

-- Add instance_id to progress_entries
-- NULL = shared across all worktrees (COMPLETED/BLOCKED tasks)
-- Value = isolated to specific worktree (IN_PROGRESS/PLANNED tasks)
ALTER TABLE progress_entries ADD COLUMN instance_id VARCHAR(255);

-- Add created_by_instance to decisions for provenance tracking
ALTER TABLE decisions ADD COLUMN created_by_instance VARCHAR(255);

-- Add instance_id to workspace_contexts for per-instance active context
-- Allows each worktree to have independent active_context
ALTER TABLE workspace_contexts ADD COLUMN instance_id VARCHAR(255);

-- Make (workspace_id, instance_id) unique
-- Main worktree: instance_id = NULL
-- Linked worktrees: instance_id = "worktree-name"
DROP INDEX IF EXISTS idx_workspace_contexts_workspace_id;
CREATE UNIQUE INDEX idx_workspace_contexts_workspace_instance
    ON workspace_contexts(workspace_id, COALESCE(instance_id, ''));

-- =====================================================================
-- ENSURE DATA INTEGRITY
-- =====================================================================

-- Ensure workspace_id is always set (required for multi-worktree queries)
ALTER TABLE progress_entries ALTER COLUMN workspace_id SET NOT NULL;

-- =====================================================================
-- PERFORMANCE INDEXES
-- =====================================================================

-- Index for instance-based queries
CREATE INDEX idx_progress_instance ON progress_entries(instance_id);

-- Composite index for common query pattern (workspace + instance)
CREATE INDEX idx_progress_workspace_instance ON progress_entries(workspace_id, instance_id);

-- =====================================================================
-- DATA MIGRATION
-- =====================================================================

-- Set existing progress entries to shared (instance_id = NULL)
-- This makes all existing tasks visible to all worktrees
UPDATE progress_entries
SET instance_id = NULL
WHERE instance_id IS NULL;

-- Set existing decisions to main worktree provenance
UPDATE decisions
SET created_by_instance = NULL
WHERE created_by_instance IS NULL;

-- =====================================================================
-- VALIDATION
-- =====================================================================

-- Verify migration completed successfully
DO $$
DECLARE
    progress_count INTEGER;
    decision_count INTEGER;
BEGIN
    -- Check progress_entries column exists
    SELECT COUNT(*) INTO progress_count
    FROM information_schema.columns
    WHERE table_name = 'progress_entries'
    AND column_name = 'instance_id';

    IF progress_count = 0 THEN
        RAISE EXCEPTION 'Migration failed: instance_id column not added to progress_entries';
    END IF;

    -- Check decisions column exists
    SELECT COUNT(*) INTO decision_count
    FROM information_schema.columns
    WHERE table_name = 'decisions'
    AND column_name = 'created_by_instance';

    IF decision_count = 0 THEN
        RAISE EXCEPTION 'Migration failed: created_by_instance column not added to decisions';
    END IF;

    RAISE NOTICE 'Migration 007 completed successfully';
    RAISE NOTICE 'Progress entries: % rows migrated', (SELECT COUNT(*) FROM progress_entries);
    RAISE NOTICE 'Decisions: % rows migrated', (SELECT COUNT(*) FROM decisions);
END $$;

COMMIT;

-- =====================================================================
-- USAGE NOTES
-- =====================================================================

-- Single Worktree (Existing Behavior):
--   instance_id = NULL for all tasks
--   All tasks visible globally
--
-- Multi-Worktree (New Behavior):
--   Set DOPEMUX_INSTANCE_ID environment variable
--   IN_PROGRESS/PLANNED: instance_id = $DOPEMUX_INSTANCE_ID (isolated)
--   COMPLETED/BLOCKED: instance_id = NULL (shared)
--
-- Query Pattern:
--   SELECT * FROM progress_entries
--   WHERE workspace_id = $1
--   AND (instance_id IS NULL OR instance_id = $2)
