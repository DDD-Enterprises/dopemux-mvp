-- PostgreSQL Row-Level Security Policies
-- Phase 1 Week 2 Day 6
-- Multi-tenant workspace isolation with defense-in-depth

-- Based on:
-- - AWS RLS best practices (https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
-- - Crunchy Data RLS guide
-- - ConPort-KG 2.0 security requirements

-- ============================================================================
-- Session Variables Documentation
-- ============================================================================

-- Application MUST set these variables on each database connection:
--
-- SET LOCAL app.current_user_id = '<user_id>';
-- SET LOCAL app.current_workspace_id = '<workspace_id>';
--
-- These variables are used by RLS policies to enforce access control.
-- "LOCAL" scope means variables reset after transaction (security).

-- ============================================================================
-- Enable RLS on All Tables
-- ============================================================================

-- Users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- User workspaces table
ALTER TABLE user_workspaces ENABLE ROW LEVEL SECURITY;

-- Refresh tokens table
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;

-- Audit logs table
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Workspaces table (if exists)
ALTER TABLE IF EXISTS workspaces ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies: users table
-- ============================================================================

-- Policy 1: Users can see only their own account
DROP POLICY IF EXISTS user_self_access ON users;
CREATE POLICY user_self_access ON users
    FOR ALL  -- SELECT, INSERT, UPDATE, DELETE
    USING (id = current_setting('app.current_user_id', true)::integer);

-- Policy 2: Allow user creation (registration) without auth
DROP POLICY IF EXISTS user_creation_public ON users;
CREATE POLICY user_creation_public ON users
    FOR INSERT
    WITH CHECK (true);  -- Anyone can register

-- Note: We combine USING and WITH CHECK:
-- - USING: Rows visible to SELECT/UPDATE/DELETE
-- - WITH CHECK: Rows allowed for INSERT/UPDATE

COMMENT ON POLICY user_self_access ON users IS 'Users can only access their own account data';
COMMENT ON POLICY user_creation_public ON users IS 'Allow public user registration';

-- ============================================================================
-- RLS Policies: user_workspaces table
-- ============================================================================

-- Policy: Users can see memberships for workspaces they belong to
DROP POLICY IF EXISTS workspace_member_access ON user_workspaces;
CREATE POLICY workspace_member_access ON user_workspaces
    FOR ALL
    USING (
        -- User can see workspace membership if they're a member
        workspace_id IN (
            SELECT workspace_id
            FROM user_workspaces
            WHERE user_id = current_setting('app.current_user_id', true)::integer
        )
    );

-- Note: This allows users to see who else is in their workspaces
-- Stricter policy would be: user_id = current_user_id (only own memberships)

COMMENT ON POLICY workspace_member_access ON user_workspaces IS 'Users see memberships in their workspaces';

-- ============================================================================
-- RLS Policies: refresh_tokens table
-- ============================================================================

-- Policy: Users can only access their own refresh tokens
DROP POLICY IF EXISTS token_owner_access ON refresh_tokens;
CREATE POLICY token_owner_access ON refresh_tokens
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true)::integer);

COMMENT ON POLICY token_owner_access ON refresh_tokens IS 'Users can only access their own tokens';

-- ============================================================================
-- RLS Policies: audit_logs table
-- ============================================================================

-- Policy 1: Users can see their own audit logs
DROP POLICY IF EXISTS audit_self_access ON audit_logs;
CREATE POLICY audit_self_access ON audit_logs
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', true)::integer);

-- Policy 2: Workspace admins can see all audit logs in their workspaces
DROP POLICY IF EXISTS audit_admin_access ON audit_logs;
CREATE POLICY audit_admin_access ON audit_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM user_workspaces uw
            WHERE uw.user_id = current_setting('app.current_user_id', true)::integer
              AND (
                  uw.permissions->>'manage_users' = 'true'
                  OR uw.permissions->>'manage_workspace' = 'true'
              )
        )
    );

-- Note: audit_logs don't have workspace_id, so admin policy is permissive
-- In production, add workspace_id to audit_logs for finer control

COMMENT ON POLICY audit_self_access ON audit_logs IS 'Users see their own audit logs';
COMMENT ON POLICY audit_admin_access ON audit_logs IS 'Admins see workspace audit logs';

-- ============================================================================
-- RLS Policies: workspaces table (metadata)
-- ============================================================================

DROP POLICY IF EXISTS workspace_member_view ON workspaces;
CREATE POLICY workspace_member_view ON workspaces
    FOR SELECT
    USING (
        -- User can see workspace if they're a member
        id IN (
            SELECT workspace_id
            FROM user_workspaces
            WHERE user_id = current_setting('app.current_user_id', true)::integer
        )
    );

DROP POLICY IF EXISTS workspace_owner_modify ON workspaces;
CREATE POLICY workspace_owner_modify ON workspaces
    FOR UPDATE
    USING (
        -- Only owners can modify workspace settings
        id IN (
            SELECT workspace_id
            FROM user_workspaces
            WHERE user_id = current_setting('app.current_user_id', true)::integer
              AND role = 'owner'
        )
    );

COMMENT ON POLICY workspace_member_view ON workspaces IS 'Members can view workspace metadata';
COMMENT ON POLICY workspace_owner_modify ON workspaces IS 'Only owners can modify workspace settings';

-- ============================================================================
-- Testing RLS Policies
-- ============================================================================

-- Test script (run manually to verify RLS working):

/*
-- Create 2 test users
INSERT INTO users (email, username, password_hash) VALUES
    ('user1@example.com', 'user1', 'hash1'),
    ('user2@example.com', 'user2', 'hash2');

-- Add to different workspaces
INSERT INTO user_workspaces (user_id, workspace_id, role) VALUES
    (1, '/workspace-a', 'owner'),
    (2, '/workspace-b', 'owner');

-- Test as user 1 (should only see workspace A)
SET LOCAL app.current_user_id = '1';
SELECT * FROM user_workspaces;
-- Expected: Only workspace-a membership

-- Test as user 2 (should only see workspace B)
SET LOCAL app.current_user_id = '2';
SELECT * FROM user_workspaces;
-- Expected: Only workspace-b membership

-- Cleanup
ROLLBACK;
*/

-- ============================================================================
-- Performance Monitoring
-- ============================================================================

-- Check RLS policy execution time
-- Run EXPLAIN ANALYZE on queries to measure overhead

/*
EXPLAIN ANALYZE
SELECT * FROM user_workspaces
WHERE workspace_id = '/workspace-a';

-- Look for "Policy" in execution plan
-- Overhead should be <5ms for typical queries
*/

-- ============================================================================
-- Rollback Script (Disable RLS)
-- ============================================================================

/*
-- To disable RLS (for testing or emergency):
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_workspaces DISABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens DISABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces DISABLE ROW LEVEL SECURITY;

-- To drop all policies:
DROP POLICY IF EXISTS user_self_access ON users;
DROP POLICY IF EXISTS user_creation_public ON users;
DROP POLICY IF EXISTS workspace_member_access ON user_workspaces;
DROP POLICY IF EXISTS token_owner_access ON refresh_tokens;
DROP POLICY IF EXISTS audit_self_access ON audit_logs;
DROP POLICY IF EXISTS audit_admin_access ON audit_logs;
DROP POLICY IF EXISTS workspace_member_view ON workspaces;
DROP POLICY IF EXISTS workspace_owner_modify ON workspaces;
*/

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Log migration
INSERT INTO schema_version (version, description)
VALUES ('1.1.0', 'PostgreSQL RLS policies for multi-tenant isolation - Week 2 Day 6')
ON CONFLICT (version) DO NOTHING;

SELECT 'RLS policies applied successfully' as status;
