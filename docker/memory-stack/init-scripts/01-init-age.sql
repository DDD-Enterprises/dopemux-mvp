-- PostgreSQL AGE Initialization Script for CONPORT-KG-2025
-- Epic DB-001: Database Foundation
-- Created: 2025-10-02

-- Load AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Set search path to include AGE catalog for all future connections
ALTER DATABASE dopemux_knowledge_graph SET search_path = ag_catalog, "$user", public;

-- Create graph for ConPort knowledge genealogy
SELECT create_graph('conport_knowledge');

-- Grant permissions to application user
GRANT USAGE ON SCHEMA ag_catalog TO dopemux_age;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ag_catalog TO dopemux_age;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ag_catalog TO dopemux_age;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA ag_catalog TO dopemux_age;

-- Create additional schemas for future expansion
CREATE SCHEMA IF NOT EXISTS conport_metadata;
GRANT ALL PRIVILEGES ON SCHEMA conport_metadata TO dopemux_age;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'AGE extension initialized successfully';
    RAISE NOTICE 'Graph "conport_knowledge" created';
    RAISE NOTICE 'Ready for decision node migration from ConPort';
END $$;
