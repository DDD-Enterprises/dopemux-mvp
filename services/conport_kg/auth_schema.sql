-- ConPort-KG 2.0 Authentication Schema
-- Phase 1 Week 1 Day 2
-- Multi-tenant user management with workspace-based permissions

-- ============================================================================
-- Extension: Enable UUID generation
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table: users
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE users IS 'User accounts with authentication credentials';
COMMENT ON COLUMN users.email IS 'Unique email address (RFC 5322 validated)';
COMMENT ON COLUMN users.password_hash IS 'Argon2id password hash (never plaintext)';
COMMENT ON COLUMN users.is_active IS 'Account active status (false = disabled)';

-- ============================================================================
-- Table: user_workspaces
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_workspaces (
    user_id INTEGER NOT NULL,
    workspace_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member' NOT NULL,
    permissions JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    PRIMARY KEY (user_id, workspace_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

COMMENT ON TABLE user_workspaces IS 'User workspace memberships with role-based permissions';
COMMENT ON COLUMN user_workspaces.role IS 'User role: owner, admin, member, viewer';
COMMENT ON COLUMN user_workspaces.permissions IS 'Fine-grained permissions (JSONB for flexibility)';

-- ============================================================================
-- Table: refresh_tokens
-- ============================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for token rotation (stored hashed)';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA256 hash of refresh token (not stored plaintext)';
COMMENT ON COLUMN refresh_tokens.revoked IS 'Revocation status (true = logged out/invalidated)';

-- ============================================================================
-- Table: audit_logs
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

COMMENT ON TABLE audit_logs IS 'Security audit log for compliance and forensics';
COMMENT ON COLUMN audit_logs.action IS 'Action performed (e.g., login.success, user.created)';
COMMENT ON COLUMN audit_logs.details IS 'Additional event details (flexible JSONB)';
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP address (supports IPv6)';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- User workspaces indexes
CREATE INDEX IF NOT EXISTS idx_user_workspaces_user_id ON user_workspaces(user_id);
CREATE INDEX IF NOT EXISTS idx_user_workspaces_workspace_id ON user_workspaces(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_workspaces_role ON user_workspaces(role);

-- Refresh tokens indexes
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked) WHERE revoked = FALSE;

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- Triggers for Automatic Timestamp Updates
-- ============================================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger on users table
DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Constraints and Validation
-- ============================================================================

-- Ensure email is lowercase (normalize for uniqueness)
CREATE OR REPLACE FUNCTION normalize_email()
RETURNS TRIGGER AS $$
BEGIN
    NEW.email = LOWER(NEW.email);
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_normalize_email ON users;
CREATE TRIGGER trigger_normalize_email
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION normalize_email();

-- Ensure valid role values
ALTER TABLE user_workspaces
    ADD CONSTRAINT check_valid_role
    CHECK (role IN ('owner', 'admin', 'member', 'viewer'));

-- ============================================================================
-- Initial Data (Optional - for development)
-- ============================================================================

-- Create default workspace (if running in dev mode)
-- Commented out for production, uncomment for dev setup
-- INSERT INTO users (email, username, password_hash, is_active)
-- VALUES ('admin@dopemux.dev', 'admin', '$argon2id$...', TRUE)
-- ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- Cleanup Functions (Maintenance)
-- ============================================================================

-- Function to clean up expired refresh tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP
       OR (revoked = TRUE AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION cleanup_expired_tokens IS 'Delete expired and old revoked refresh tokens (run daily)';

-- Function to clean up old audit logs (optional retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Delete audit logs older than retention period (default 90 days)';

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- View: Active users with workspace count
CREATE OR REPLACE VIEW v_active_users AS
SELECT
    u.id,
    u.email,
    u.username,
    u.created_at,
    COUNT(uw.workspace_id) as workspace_count
FROM users u
LEFT JOIN user_workspaces uw ON u.id = uw.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.username, u.created_at;

COMMENT ON VIEW v_active_users IS 'Active users with workspace membership count';

-- View: Workspace user counts by role
CREATE OR REPLACE VIEW v_workspace_stats AS
SELECT
    workspace_id,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE role = 'owner') as owners,
    COUNT(*) FILTER (WHERE role = 'admin') as admins,
    COUNT(*) FILTER (WHERE role = 'member') as members,
    COUNT(*) FILTER (WHERE role = 'viewer') as viewers
FROM user_workspaces
GROUP BY workspace_id;

COMMENT ON VIEW v_workspace_stats IS 'User counts per workspace by role';

-- ============================================================================
-- Grant Permissions (Production Security)
-- ============================================================================

-- Note: In production, create dedicated app user with limited permissions
-- Example:
-- CREATE USER conport_app WITH PASSWORD 'secure_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO conport_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO conport_app;

-- ============================================================================
-- Schema Version Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial authentication schema - Phase 1 Week 1 Day 2')
ON CONFLICT (version) DO NOTHING;

COMMENT ON TABLE schema_version IS 'Track schema migrations and versions';
