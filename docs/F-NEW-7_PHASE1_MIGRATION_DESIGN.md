# F-NEW-7 Phase 1: Multi-Tenancy Migration Design

**Status**: Schema analyzed, migration strategy designed
**Date**: 2025-10-25
**Based on**: Zen planner roadmap (Decision #310)

---

## Current Schema Analysis

### Tables with workspace_id (Already Multi-Workspace)
- `workspace_contexts` - Line 12-22
- `decisions` - Line 31-42 (310 records)
- `progress_entries` - Line 58-77
- `session_snapshots` - Line 82-98
- `custom_data` - (lines 100+)

**KEY INSIGHT**: workspace_id ALREADY EXISTS!
Multi-workspace support is already built. We just need user_id for multi-user.

---

## What's Missing for Multi-Tenancy

### Required Additions

**1. user_id column** - Add to all tables
- Default: "default" for existing data
- Type: VARCHAR(100) NOT NULL DEFAULT 'default'
- Index: Composite (user_id, workspace_id)

**2. users table** - User profiles
```sql
CREATE TABLE users (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**3. workspaces table** - Workspace metadata + ownership
```sql
CREATE TABLE workspaces (
    id VARCHAR(255) PRIMARY KEY,
    owner_user_id VARCHAR(100) REFERENCES users(id),
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**4. user_workspace_access** - Permissions
```sql
CREATE TABLE user_workspace_access (
    user_id VARCHAR(100) REFERENCES users(id),
    workspace_id VARCHAR(255) REFERENCES workspaces(id),
    role VARCHAR(20) CHECK (role IN ('owner', 'write', 'read')),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, workspace_id)
);
```

---

## Migration Strategy

### Phase 1A: Add Columns (Non-Breaking)

**Migration 003: Add user_id columns**
```sql
-- Add user_id with default value (non-breaking!)
ALTER TABLE decisions
ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'default';

ALTER TABLE progress_entries
ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'default';

ALTER TABLE workspace_contexts
ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'default';

ALTER TABLE session_snapshots
ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'default';

ALTER TABLE custom_data
ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT 'default';
```

**Impact**: ZERO (all existing queries still work, default user assigned)

---

### Phase 1B: Create New Tables

**Migration 004: Create users and workspaces tables**
```sql
CREATE TABLE users (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE workspaces (
    id VARCHAR(255) PRIMARY KEY,
    owner_user_id VARCHAR(100) REFERENCES users(id),
    name VARCHAR(255),
    description TEXT,
    path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_workspace_access (
    user_id VARCHAR(100) REFERENCES users(id),
    workspace_id VARCHAR(255) REFERENCES workspaces(id),
    role VARCHAR(20) CHECK (role IN ('owner', 'write', 'read')),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, workspace_id)
);

-- Seed default user
INSERT INTO users (id, display_name) VALUES ('default', 'Default User');

-- Create workspace entries for existing workspace_ids
INSERT INTO workspaces (id, owner_user_id, name)
SELECT DISTINCT workspace_id, 'default', workspace_id
FROM decisions;
```

**Impact**: New tables, existing data unchanged

---

### Phase 1C: Add Indexes (Performance)

**Migration 005: Composite indexes for multi-tenancy**
```sql
-- Composite indexes (user_id, workspace_id)
CREATE INDEX idx_decisions_user_workspace
ON decisions(user_id, workspace_id, created_at DESC);

CREATE INDEX idx_progress_user_workspace
ON progress_entries(user_id, workspace_id, status);

CREATE INDEX idx_sessions_user_workspace
ON session_snapshots(user_id, workspace_id, session_start DESC);

-- User-only queries
CREATE INDEX idx_decisions_user ON decisions(user_id, created_at DESC);
CREATE INDEX idx_progress_user ON progress_entries(user_id, status);
```

**Impact**: Better query performance for multi-user scenarios

---

### Phase 1D: Update Application Code

**ConPort MCP Server Changes**:
1. Add user_id parameter to all tool calls
2. Filter all queries by user_id
3. Validate user has access to workspace
4. Default to 'default' user for backward compatibility

**Example**:
```python
# Before:
decisions = await db.fetch("SELECT * FROM decisions WHERE workspace_id = $1", workspace_id)

# After:
decisions = await db.fetch(
    "SELECT * FROM decisions WHERE user_id = $1 AND workspace_id = $2",
    user_id, workspace_id
)
```

---

## Data Preservation

**Existing Data** (assigned to "default" user):
- 310 decisions
- Progress entries
- Session snapshots
- Custom data

**Migration Safety**:
- All defaults preserve existing behavior
- No data deletion
- Backward compatible
- Rollback: Just remove user_id columns

---

## Testing Strategy

**Test 1**: Single user (existing behavior)
- Default user can access all existing data
- No performance regression
- All queries still work

**Test 2**: Multi-user isolation
- User A cannot see User B's data
- Workspace ownership enforced
- Permission checks working

**Test 3**: Performance
- Queries still <200ms
- Composite indexes effective
- No regression from v1

---

## ADHD-Optimized Rollout

**Day 1 (Morning)**: Migrations 003-004 (schema + tables)
**Day 1 (Afternoon)**: Migration 005 (indexes)
**Day 2 (Morning)**: Application code updates
**Day 2 (Afternoon)**: Testing & validation

**Checkpoints**:
- After each migration: Test existing queries still work
- After app changes: Integration tests
- End of Day 2: Multi-user demo

---

## Success Criteria

- [ ] All 5 tables have user_id column
- [ ] users, workspaces, user_workspace_access tables created
- [ ] 310 decisions accessible by "default" user
- [ ] Composite indexes created
- [ ] Zero data loss
- [ ] Performance <200ms maintained

---

**Ready to Implement**: Migration scripts designed, safe rollout plan validated
