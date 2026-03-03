-- Migration 003: Multi-Tenancy Foundation
-- Phase A-C: Add user_id columns + Create user management tables
--
-- SAFETY: Zero-downtime, backward compatible, fully rollback-able
-- Duration: ~5 minutes execution
-- Validated by: Zen thinkdeep expert analysis (Decision #311)

-- =====================================================================
-- PHASE A: Add user_id Columns (Nullable with Default)
-- =====================================================================
-- Impact: ZERO (all existing queries still work with defaults)

ALTER TABLE decisions
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'default';

ALTER TABLE progress_entries
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'default';

ALTER TABLE workspace_contexts
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'default';

ALTER TABLE session_snapshots
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'default';

ALTER TABLE custom_data
ADD COLUMN IF NOT EXISTS user_id VARCHAR(100) DEFAULT 'default';

-- Note: entity_relationships and search_cache deliberately excluded
-- They inherit ownership from source entities or are workspace-scoped optimizations

-- =====================================================================
-- PHASE B: Create User Management Tables
-- =====================================================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR(255) PRIMARY KEY,
    owner_user_id VARCHAR(100) REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_workspace_access (
    user_id VARCHAR(100) REFERENCES users(id) ON DELETE CASCADE,
    workspace_id VARCHAR(255) REFERENCES workspaces(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'write', 'read')) DEFAULT 'write',
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, workspace_id)
);

-- Indexes for user management
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_access_user ON user_workspace_access(user_id);
CREATE INDEX IF NOT EXISTS idx_access_workspace ON user_workspace_access(workspace_id);

-- =====================================================================
-- PHASE C: Seed Default User + Workspace Metadata
-- =====================================================================

-- Create default user (if not exists)
INSERT INTO users (id, display_name, email)
VALUES ('default', 'Default User', 'default@localhost')
ON CONFLICT (id) DO NOTHING;

-- Create workspace records for all existing workspace_ids
INSERT INTO workspaces (id, owner_user_id, name, description)
SELECT DISTINCT
    workspace_id,
    'default',
    workspace_id,
    'Migrated from ConPort v1'
FROM decisions
ON CONFLICT (id) DO NOTHING;

-- Grant default user access to all workspaces
INSERT INTO user_workspace_access (user_id, workspace_id, role)
SELECT 'default', id, 'owner'
FROM workspaces
ON CONFLICT (user_id, workspace_id) DO NOTHING;

-- =====================================================================
-- VALIDATION QUERIES
-- =====================================================================

-- Verify migration success
DO $$
DECLARE
    decisions_count INTEGER;
    users_count INTEGER;
    workspaces_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO decisions_count FROM decisions WHERE user_id = 'default';
    SELECT COUNT(*) INTO users_count FROM users WHERE id = 'default';
    SELECT COUNT(*) INTO workspaces_count FROM workspaces WHERE owner_user_id = 'default';

    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 003 Validation:';
    RAISE NOTICE '   Decisions with user_id=default: %', decisions_count;
    RAISE NOTICE '   Default user exists: %', (users_count > 0);
    RAISE NOTICE '   Workspaces created: %', workspaces_count;
    RAISE NOTICE '';

    IF decisions_count = 0 THEN
        RAISE WARNING '⚠️ No decisions found - may need to update existing records';
    END IF;

    IF users_count = 0 THEN
        RAISE EXCEPTION '❌ Default user not created';
    END IF;
END $$;

-- =====================================================================
-- ROLLBACK INSTRUCTIONS
-- =====================================================================
-- If needed, run: docker/mcp-servers/conport/migrations/003_rollback.sql
--
-- Quick rollback:
-- ALTER TABLE decisions DROP COLUMN IF EXISTS user_id;
-- ALTER TABLE progress_entries DROP COLUMN IF EXISTS user_id;
-- ALTER TABLE workspace_contexts DROP COLUMN IF EXISTS user_id;
-- ALTER TABLE session_snapshots DROP COLUMN IF EXISTS user_id;
-- ALTER TABLE custom_data DROP COLUMN IF EXISTS user_id;
-- DROP TABLE IF EXISTS user_workspace_access;
-- DROP TABLE IF EXISTS workspaces;
-- DROP TABLE IF EXISTS users;
