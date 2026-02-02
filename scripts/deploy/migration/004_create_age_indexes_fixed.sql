-- AGE Index Creation (Fixed for Actual Schema)
-- Part of CONPORT-KG-2025 Simplified Migration (Decision #113)
-- Indexes on JSONB properties column for optimal query performance

-- =====================================================================
-- VERTEX INDEXES (Decision nodes)
-- =====================================================================

-- Properties are stored in JSONB 'properties' column
-- Need GIN index for efficient JSONB querying

-- Primary GIN index on all properties
CREATE INDEX IF NOT EXISTS idx_decision_properties
    ON conport_knowledge."Decision"
    USING GIN (properties);

-- Specific property indexes for common queries
CREATE INDEX IF NOT EXISTS idx_decision_id
    ON conport_knowledge."Decision"
    USING BTREE ((properties->>'id')::integer);

CREATE INDEX IF NOT EXISTS idx_decision_timestamp
    ON conport_knowledge."Decision"
    USING BTREE (properties->>'timestamp');

-- Tags array search (GIN on JSONB array)
CREATE INDEX IF NOT EXISTS idx_decision_tags
    ON conport_knowledge."Decision"
    USING GIN ((properties->'tags'));

-- =====================================================================
-- EDGE INDEXES (All relationship types)
-- =====================================================================

-- AGE edge tables: {label}_edges format
-- Each has: id, start_id, end_id, properties

-- BUILDS_UPON edges (4 edges)
CREATE INDEX IF NOT EXISTS idx_builds_upon_start
    ON conport_knowledge."BUILDS_UPON"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_builds_upon_end
    ON conport_knowledge."BUILDS_UPON"
    USING BTREE (end_id);

-- FULFILLS edges (2 edges)
CREATE INDEX IF NOT EXISTS idx_fulfills_start
    ON conport_knowledge."FULFILLS"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_fulfills_end
    ON conport_knowledge."FULFILLS"
    USING BTREE (end_id);

-- VALIDATES edges (2 edges)
CREATE INDEX IF NOT EXISTS idx_validates_start
    ON conport_knowledge."VALIDATES"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_validates_end
    ON conport_knowledge."VALIDATES"
    USING BTREE (end_id);

-- EXTENDS edges (1 edge)
CREATE INDEX IF NOT EXISTS idx_extends_start
    ON conport_knowledge."EXTENDS"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_extends_end
    ON conport_knowledge."EXTENDS"
    USING BTREE (end_id);

-- ENABLES edges (1 edge)
CREATE INDEX IF NOT EXISTS idx_enables_start
    ON conport_knowledge."ENABLES"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_enables_end
    ON conport_knowledge."ENABLES"
    USING BTREE (end_id);

-- CORRECTS edges (1 edge)
CREATE INDEX IF NOT EXISTS idx_corrects_start
    ON conport_knowledge."CORRECTS"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_corrects_end
    ON conport_knowledge."CORRECTS"
    USING BTREE (end_id);

-- DEPENDS_ON edges (1 edge)
CREATE INDEX IF NOT EXISTS idx_depends_on_start
    ON conport_knowledge."DEPENDS_ON"
    USING BTREE (start_id);

CREATE INDEX IF NOT EXISTS idx_depends_on_end
    ON conport_knowledge."DEPENDS_ON"
    USING BTREE (end_id);

-- =====================================================================
-- ANALYZE FOR QUERY PLANNER
-- =====================================================================

ANALYZE conport_knowledge."Decision";
ANALYZE conport_knowledge."BUILDS_UPON";
ANALYZE conport_knowledge."FULFILLS";
ANALYZE conport_knowledge."VALIDATES";
ANALYZE conport_knowledge."EXTENDS";
ANALYZE conport_knowledge."ENABLES";
ANALYZE conport_knowledge."CORRECTS";
ANALYZE conport_knowledge."DEPENDS_ON";

-- Summary
SELECT
    'Decision vertices' as category,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'conport_knowledge'
  AND tablename = 'Decision'

UNION ALL

SELECT
    'Edge tables' as category,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'conport_knowledge'
  AND tablename IN ('BUILDS_UPON', 'FULFILLS', 'VALIDATES', 'EXTENDS', 'ENABLES', 'CORRECTS', 'DEPENDS_ON');
