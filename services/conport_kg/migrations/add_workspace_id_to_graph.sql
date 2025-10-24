-- Migration: Add workspace_id to AGE Graph Vertices
-- Phase 1 Week 2 Day 6
-- Enables multi-tenant workspace isolation in knowledge graph

-- ============================================================================
-- Add workspace_id to Decision Vertices
-- ============================================================================

-- Step 1: Add workspace_id property to all existing Decision vertices
-- Default to primary workspace for existing data
SELECT * FROM cypher('conport_knowledge', $$
    MATCH (d:Decision)
    WHERE d.workspace_id IS NULL
    SET d.workspace_id = '/Users/hue/code/dopemux-mvp'
    RETURN count(d) as updated_count
$$) as (count agtype);

-- Note: AGE does not support CREATE INDEX on vertex properties (as of AGE 1.6)
-- Filtering will rely on Cypher WHERE clauses
-- Performance impact: Minimal for <10K decisions per workspace

-- ============================================================================
-- Create Workspace Metadata Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

COMMENT ON TABLE workspaces IS 'Workspace metadata and settings';

-- ============================================================================
-- Insert Default Workspace
-- ============================================================================

INSERT INTO workspaces (id, name, description)
VALUES (
    '/Users/hue/code/dopemux-mvp',
    'Dopemux MVP',
    'Primary development workspace'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- Migration Validation Query
-- ============================================================================

-- Verify all decisions have workspace_id
SELECT * FROM cypher('conport_knowledge', $$
    MATCH (d:Decision)
    WHERE d.workspace_id IS NULL
    RETURN count(d) as missing_workspace_id
$$) as (count agtype);

-- Expected: count = 0 (all decisions have workspace_id)

-- ============================================================================
-- Rollback Script (if needed)
-- ============================================================================

-- To rollback this migration:
-- SELECT * FROM cypher('conport_knowledge', $$
--     MATCH (d:Decision)
--     REMOVE d.workspace_id
--     RETURN count(d)
-- $$) as (count agtype);
--
-- DROP TABLE IF EXISTS workspaces;
