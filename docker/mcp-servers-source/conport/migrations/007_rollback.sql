-- Rollback Migration 007: Remove Worktree Multi-Instance Support
-- Purpose: Safely revert to single-instance mode
-- Date: 2025-10-04

BEGIN;

-- =====================================================================
-- VALIDATION BEFORE ROLLBACK
-- =====================================================================

DO $$
DECLARE
    isolated_tasks INTEGER;
BEGIN
    -- Check if there are tasks with instance_id set
    SELECT COUNT(*) INTO isolated_tasks
    FROM progress_entries
    WHERE instance_id IS NOT NULL;

    IF isolated_tasks > 0 THEN
        RAISE WARNING 'Rollback will affect % isolated tasks', isolated_tasks;
        RAISE WARNING 'These tasks will become visible to all worktrees';
    END IF;

    RAISE NOTICE 'Proceeding with rollback...';
END $$;

-- =====================================================================
-- REMOVE INDEXES
-- =====================================================================

DROP INDEX IF EXISTS idx_progress_workspace_instance;
DROP INDEX IF EXISTS idx_progress_instance;

-- =====================================================================
-- REMOVE COLUMNS
-- =====================================================================

-- Remove instance_id from progress_entries
ALTER TABLE progress_entries DROP COLUMN IF EXISTS instance_id;

-- Remove created_by_instance from decisions
ALTER TABLE decisions DROP COLUMN IF EXISTS created_by_instance;

-- Remove instance_id from workspace_contexts
ALTER TABLE workspace_contexts DROP COLUMN IF EXISTS instance_id;

-- Restore original unique index on workspace_contexts
DROP INDEX IF EXISTS idx_workspace_contexts_workspace_instance;
CREATE UNIQUE INDEX idx_workspace_contexts_workspace_id ON workspace_contexts(workspace_id);

-- =====================================================================
-- VALIDATION AFTER ROLLBACK
-- =====================================================================

DO $$
DECLARE
    progress_column_exists INTEGER;
    decision_column_exists INTEGER;
BEGIN
    -- Verify instance_id removed from progress_entries
    SELECT COUNT(*) INTO progress_column_exists
    FROM information_schema.columns
    WHERE table_name = 'progress_entries'
    AND column_name = 'instance_id';

    IF progress_column_exists > 0 THEN
        RAISE EXCEPTION 'Rollback failed: instance_id column still exists in progress_entries';
    END IF;

    -- Verify created_by_instance removed from decisions
    SELECT COUNT(*) INTO decision_column_exists
    FROM information_schema.columns
    WHERE table_name = 'decisions'
    AND column_name = 'created_by_instance';

    IF decision_column_exists > 0 THEN
        RAISE EXCEPTION 'Rollback failed: created_by_instance column still exists in decisions';
    END IF;

    RAISE NOTICE 'Rollback 007 completed successfully';
    RAISE NOTICE 'System reverted to single-instance mode';
END $$;

COMMIT;

-- =====================================================================
-- POST-ROLLBACK NOTES
-- =====================================================================

-- After rollback:
--   - All tasks visible globally (no isolation)
--   - DOPEMUX_INSTANCE_ID environment variable ignored
--   - System behaves as single-instance mode
--   - No data loss (all tasks preserved)
