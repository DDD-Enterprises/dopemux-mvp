-- ConPort Schema Upgrade: entity_relationships_v2 Table
-- Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)
-- Creates upgraded schema with INTEGER foreign keys and 8 relationship types

CREATE TABLE entity_relationships_v2 (
    id SERIAL PRIMARY KEY,
    workspace_id VARCHAR(255) NOT NULL,

    -- INTEGER foreign keys (was UUID in original schema)
    source_type VARCHAR(50) NOT NULL,
    source_id INTEGER NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,

    -- EXPANDED: 8 relationship types (was 4 in original schema)
    -- Supports full decision genealogy tracking
    relationship_type VARCHAR(50) NOT NULL CHECK (
        relationship_type IN (
            'SUPERSEDES',      -- Decision supersedes another
            'DEPENDS_ON',      -- Decision depends on another (was 'blocks')
            'IMPLEMENTS',      -- Decision implements another
            'EXTENDS',         -- Decision extends another
            'VALIDATES',       -- Decision validates another
            'CORRECTS',        -- Decision corrects another
            'BUILDS_UPON',     -- Decision builds upon another (was 'caused_by')
            'RELATES_TO'       -- General relationship
        )
    ),

    -- Relationship metadata
    strength DECIMAL(3,2) DEFAULT 1.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    properties JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Foreign key constraints to decisions_v2
    CONSTRAINT fk_source_decision
        FOREIGN KEY (source_id)
        REFERENCES decisions_v2(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_target_decision
        FOREIGN KEY (target_id)
        REFERENCES decisions_v2(id)
        ON DELETE CASCADE,

    -- Prevent duplicate relationships
    CONSTRAINT unique_relationship
        UNIQUE (source_id, target_id, relationship_type)
);

-- Create indexes for graph traversal performance
CREATE INDEX idx_rel_v2_workspace ON entity_relationships_v2(workspace_id);
CREATE INDEX idx_rel_v2_source ON entity_relationships_v2(source_type, source_id);
CREATE INDEX idx_rel_v2_target ON entity_relationships_v2(target_type, target_id);
CREATE INDEX idx_rel_v2_type ON entity_relationships_v2(relationship_type);
CREATE INDEX idx_rel_v2_strength ON entity_relationships_v2(strength DESC);
CREATE INDEX idx_rel_v2_properties ON entity_relationships_v2 USING GIN(properties);

-- Composite index for bidirectional traversal
CREATE INDEX idx_rel_v2_bidirectional ON entity_relationships_v2(source_id, target_id);

COMMENT ON TABLE entity_relationships_v2 IS 'Upgraded relationship schema with INTEGER FKs and 8 relationship types';
COMMENT ON COLUMN entity_relationships_v2.relationship_type IS 'Expanded from 4 to 8 types for full decision genealogy';
COMMENT ON COLUMN entity_relationships_v2.strength IS 'Relationship strength (0.0-1.0) for ADHD progressive disclosure';
