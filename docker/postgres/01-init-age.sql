-- Initialize Apache AGE extension for ConPort knowledge graph
-- This script runs automatically when the postgres container starts

-- Create AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load the AGE extension into the current session
LOAD 'age';

-- Set search path to include ag_catalog
SET search_path = ag_catalog, "$user", public;

-- Create the knowledge graph
SELECT create_graph('knowledge_graph');

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE '✅ Apache AGE extension initialized successfully';
    RAISE NOTICE '📊 Graph: knowledge_graph created';
END $$;
