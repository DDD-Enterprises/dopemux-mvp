-- Migration 004: Unified Query Performance Indexes
-- F-NEW-7 Phase 2: Enable <200ms cross-workspace queries
--
-- Prerequisites: Migration 003 (user_id columns must exist)
-- Impact: Performance optimization, no data changes
-- Rollback: Safe to drop indexes

-- =====================================================================
-- Composite Indexes for Cross-Workspace Search
-- =====================================================================

-- Index 1: User + Full-Text Search (Primary use case)
-- Enables: Fast cross-workspace FTS for a user
-- Query: WHERE user_id = ? AND to_tsvector(...) @@ plainto_tsquery(?)
CREATE INDEX IF NOT EXISTS idx_decisions_user_fts
ON public.decisions USING GIN (to_tsvector('english', summary || ' ' || COALESCE(rationale, '')));

-- Index 2: User + Workspace + Recency
-- Enables: Recent decisions per user per workspace
-- Query: WHERE user_id = ? AND workspace_id = ? ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_decisions_user_workspace_recent
ON public.decisions(user_id, workspace_id, created_at DESC);

-- Index 3: User-scoped workspace list (for quick workspace enumeration)
-- Enables: Fast DISTINCT workspace_id queries
-- Query: SELECT DISTINCT workspace_id WHERE user_id = ?
CREATE INDEX IF NOT EXISTS idx_decisions_user_workspace
ON public.decisions(user_id, workspace_id);

-- =====================================================================
-- Progress Entries Indexes (for workspace summaries)
-- =====================================================================

-- Index 4: User + Workspace + Status (for aggregations)
CREATE INDEX IF NOT EXISTS idx_progress_user_workspace_status
ON public.progress_entries(user_id, workspace_id, status);

-- Index 5: User + Recent activity
CREATE INDEX IF NOT EXISTS idx_progress_user_recent
ON public.progress_entries(user_id, created_at DESC);

-- =====================================================================
-- Custom Data Indexes (for cross-workspace custom queries)
-- =====================================================================

-- Index 6: User + Category (for custom data queries)
CREATE INDEX IF NOT EXISTS idx_custom_data_user_category
ON public.custom_data(user_id, category);

-- =====================================================================
-- Validation
-- =====================================================================

DO $$
DECLARE
    idx_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname LIKE 'idx_%user%';

    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 004 Validation:';
    RAISE NOTICE '   User-scoped indexes created: %', idx_count;
    RAISE NOTICE '   Expected: 6 indexes minimum';
    RAISE NOTICE '';

    IF idx_count < 6 THEN
        RAISE WARNING '⚠️ Some indexes may not have been created';
    END IF;
END $$;

-- =====================================================================
-- Performance Impact Estimation
-- =====================================================================

-- Analyze tables for query planner
ANALYZE public.decisions;
ANALYZE public.progress_entries;
ANALYZE public.custom_data;

-- =====================================================================
-- Rollback Instructions
-- =====================================================================
-- If needed, run:
--
-- DROP INDEX IF EXISTS public.idx_decisions_user_fts;
-- DROP INDEX IF EXISTS public.idx_decisions_user_workspace_recent;
-- DROP INDEX IF EXISTS public.idx_decisions_user_workspace;
-- DROP INDEX IF EXISTS public.idx_progress_user_workspace_status;
-- DROP INDEX IF EXISTS public.idx_progress_user_recent;
-- DROP INDEX IF EXISTS public.idx_custom_data_user_category;
