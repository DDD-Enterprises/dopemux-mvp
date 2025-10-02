-- AGE Index Creation Script
-- Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)
-- Creates 12 indexes (6 vertex + 6 edge) for <150ms p95 query performance

-- =====================================================================
-- VERTEX INDEXES (Decision nodes)
-- =====================================================================

-- Primary access by ID
CREATE INDEX IF NOT EXISTS idx_decision_vertex_id
    ON conport_knowledge."Decision"
    USING BTREE (id);

-- Status filtering (accepted, superseded, deprecated, proposed)
CREATE INDEX IF NOT EXISTS idx_decision_status
    ON conport_knowledge."Decision"
    USING BTREE (status);

-- Temporal queries (recent decisions, time-based genealogy)
CREATE INDEX IF NOT EXISTS idx_decision_timestamp
    ON conport_knowledge."Decision"
    USING BTREE (timestamp DESC);

-- Tag-based searches (JSONB array operations)
CREATE INDEX IF NOT EXISTS idx_decision_tags
    ON conport_knowledge."Decision"
    USING GIN (tags);

-- ADHD progressive disclosure (complexity-based filtering)
-- Partial index for nullable field
CREATE INDEX IF NOT EXISTS idx_decision_hop_distance
    ON conport_knowledge."Decision"
    USING BTREE (hop_distance)
    WHERE hop_distance IS NOT NULL;

-- Workspace filtering for multi-workspace support
CREATE INDEX IF NOT EXISTS idx_decision_workspace
    ON conport_knowledge."Decision"
    USING BTREE (workspace_id);

-- =====================================================================
-- EDGE INDEXES (Relationships)
-- =====================================================================

-- Note: AGE creates edge tables automatically with format: "{label}_edges"
-- Index names will vary based on actual edge labels

-- Core graph traversal (source node → target node)
-- This index pattern applies to all edge types:
-- SUPERSEDES_edges, DEPENDS_ON_edges, IMPLEMENTS_edges, etc.

-- Example for generic edge traversal:
-- These will need to be created for each specific edge type after edges are loaded

-- Start node lookup (for outgoing edge queries)
-- CREATE INDEX IF NOT EXISTS idx_{label}_start_id
--     ON conport_knowledge."{label}_edges"
--     USING BTREE (start_id);

-- End node lookup (for incoming edge queries)
-- CREATE INDEX IF NOT EXISTS idx_{label}_end_id
--     ON conport_knowledge."{label}_edges"
--     USING BTREE (end_id);

-- Bidirectional traversal (composite index)
-- CREATE INDEX IF NOT EXISTS idx_{label}_bidirectional
--     ON conport_knowledge."{label}_edges"
--     USING BTREE (start_id, end_id);

-- Edge properties for metadata queries
-- CREATE INDEX IF NOT EXISTS idx_{label}_properties
--     ON conport_knowledge."{label}_edges"
--     USING GIN (properties);

-- =====================================================================
-- DYNAMIC INDEX CREATION
-- =====================================================================

-- After edges are loaded, run this query to create indexes for all edge types:

DO $$
DECLARE
    edge_table text;
BEGIN
    FOR edge_table IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'conport_knowledge'
          AND tablename LIKE '%_edges'
    LOOP
        -- Start ID index
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_start_id ON conport_knowledge.%I USING BTREE (start_id)',
                      edge_table, edge_table);

        -- End ID index
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_end_id ON conport_knowledge.%I USING BTREE (end_id)',
                      edge_table, edge_table);

        -- Bidirectional composite index
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_bidirectional ON conport_knowledge.%I USING BTREE (start_id, end_id)',
                      edge_table, edge_table);

        -- Properties GIN index
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_properties ON conport_knowledge.%I USING GIN (properties)',
                      edge_table, edge_table);

        RAISE NOTICE 'Created indexes for %', edge_table;
    END LOOP;
END $$;

-- =====================================================================
-- ANALYZE FOR QUERY PLANNER
-- =====================================================================

-- Update table statistics for optimal query planning
ANALYZE conport_knowledge."Decision";

-- Analyze all edge tables
DO $$
DECLARE
    edge_table text;
BEGIN
    FOR edge_table IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'conport_knowledge'
          AND tablename LIKE '%_edges'
    LOOP
        EXECUTE format('ANALYZE conport_knowledge.%I', edge_table);
        RAISE NOTICE 'Analyzed %', edge_table;
    END LOOP;
END $$;

-- Print summary
SELECT
    'Vertex indexes' as category,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'conport_knowledge'
  AND tablename = 'Decision'

UNION ALL

SELECT
    'Edge indexes' as category,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'conport_knowledge'
  AND tablename LIKE '%_edges';
