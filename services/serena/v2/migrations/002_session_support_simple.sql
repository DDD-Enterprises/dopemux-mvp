-- Migration: 002_session_support_simple.sql
-- Simplified version - add columns one at a time
-- Database: dopemux_knowledge_graph, Table: ag_catalog.workspace_contexts

BEGIN;

-- Add columns individually
ALTER TABLE ag_catalog.workspace_contexts ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT 'default';
ALTER TABLE ag_catalog.workspace_contexts ADD COLUMN IF NOT EXISTS worktree_path TEXT DEFAULT NULL;
ALTER TABLE ag_catalog.workspace_contexts ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT NULL;
ALTER TABLE ag_catalog.workspace_contexts ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- Update existing rows
UPDATE ag_catalog.workspace_contexts SET session_id = 'default' WHERE session_id IS NULL OR session_id = '';
UPDATE ag_catalog.workspace_contexts SET status = 'active' WHERE status IS NULL OR status = '';

-- Create unique index (skip if exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_workspace_session_unique') THEN
        CREATE UNIQUE INDEX idx_workspace_session_unique ON ag_catalog.workspace_contexts(workspace_id, session_id);
    END IF;
END $$;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_ws_ctx_updated ON ag_catalog.workspace_contexts(workspace_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_ws_ctx_status ON ag_catalog.workspace_contexts(workspace_id, status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_ws_ctx_worktree ON ag_catalog.workspace_contexts(workspace_id, worktree_path) WHERE worktree_path IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ws_ctx_branch ON ag_catalog.workspace_contexts(workspace_id, branch) WHERE branch IS NOT NULL;

-- Create session_history table
CREATE TABLE IF NOT EXISTS ag_catalog.session_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    worktree_path TEXT,
    branch TEXT,
    active_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    UNIQUE (workspace_id, session_id),
    CHECK (duration_minutes >= 0),
    CHECK (completed_at IS NULL OR completed_at >= created_at)
);

CREATE INDEX IF NOT EXISTS idx_sess_hist_ws ON ag_catalog.session_history(workspace_id, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_sess_hist_branch ON ag_catalog.session_history(workspace_id, branch) WHERE branch IS NOT NULL;

COMMIT;

-- VACUUM must be outside transaction
VACUUM ANALYZE ag_catalog.workspace_contexts;

-- Verification
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'ag_catalog' AND table_name = 'workspace_contexts'
ORDER BY ordinal_position;
