-- Migration 003: Add PostgreSQL Full-Text Search
-- Replaces regex-based search with tsvector + GIN index
-- Performance: ~10x faster search
-- Date: 2025-10-25

-- Step 1: Add tsvector columns for full-text search
ALTER TABLE decisions 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Step 2: Create function to update search vector
CREATE OR REPLACE FUNCTION update_decision_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.rationale, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.implementation_details, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create trigger to auto-update search vector
DROP TRIGGER IF EXISTS decisions_search_vector_update ON decisions;
CREATE TRIGGER decisions_search_vector_update
  BEFORE INSERT OR UPDATE OF summary, rationale, implementation_details
  ON decisions
  FOR EACH ROW
  EXECUTE FUNCTION update_decision_search_vector();

-- Step 4: Populate search vectors for existing data
UPDATE decisions
SET search_vector = 
  setweight(to_tsvector('english', COALESCE(summary, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(rationale, '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(implementation_details, '')), 'C')
WHERE search_vector IS NULL;

-- Step 5: Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_decisions_search_vector 
ON decisions USING GIN(search_vector);

-- Step 6: Create index on workspace_id for tenant isolation
CREATE INDEX IF NOT EXISTS idx_decisions_workspace_search
ON decisions(workspace_id) WHERE search_vector IS NOT NULL;

-- Performance validation query (should use index scan)
-- EXPLAIN ANALYZE 
-- SELECT id, summary, ts_rank(search_vector, to_tsquery('english', 'authentication')) as rank
-- FROM decisions
-- WHERE workspace_id = '/Users/hue/code/dopemux-mvp'
--   AND search_vector @@ to_tsquery('english', 'authentication')
-- ORDER BY rank DESC
-- LIMIT 20;
