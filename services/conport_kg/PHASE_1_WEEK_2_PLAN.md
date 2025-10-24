# Phase 1 Week 2: PostgreSQL RLS + Workspace Isolation

**Week**: 2 of 11
**Phase**: 1 - Authentication & Authorization
**Dates**: 2025-10-28 to 2025-11-01 (5 days)
**Effort**: 40 hours
**Team**: 1 backend developer

---

## Week Overview

**Objective**: Implement database-level workspace isolation using PostgreSQL Row-Level Security

**Deliverables**:
1. RLS policies on all ConPort tables (rls_policies.sql - 200 lines)
2. Workspace_id added to AGE graph vertices (migration - 100 lines)
3. Query refactoring for workspace filtering (500 lines modified)
4. RBAC middleware for API authorization (rbac_middleware.py - 150 lines)
5. Cross-workspace isolation tests (500 lines, 50+ tests)

**Total Output**: 1,450 lines (650 production + 500 tests + 300 refactoring)
**Success Criteria**: Zero cross-workspace data leakage in 100+ test scenarios

---

## Day-by-Day Breakdown

### Day 6 (Monday): PostgreSQL RLS Policies

**Morning (4 hours): RLS Policy Creation**

**Objective**: Implement Row-Level Security policies for defense-in-depth

**Task 6.1**: Create rls_policies.sql (200 lines)

```sql
-- RLS Policies for Multi-Tenant Isolation
-- Based on AWS best practices and ConPort-KG 2.0 design

-- ============================================================================
-- Enable RLS on All Tables
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Session Variables for Current Context
-- ============================================================================

-- Application sets these variables on each request:
-- SET LOCAL app.current_user_id = '123';
-- SET LOCAL app.current_workspace_id = '/Users/hue/code/project';

-- ============================================================================
-- RLS Policies for users table
-- ============================================================================

-- Users can only see their own account
CREATE POLICY user_self_access ON users
  FOR ALL
  USING (id = current_setting('app.current_user_id', true)::integer);

-- ============================================================================
-- RLS Policies for user_workspaces table
-- ============================================================================

-- Users can see memberships for workspaces they belong to
CREATE POLICY workspace_member_access ON user_workspaces
  FOR ALL
  USING (
    workspace_id IN (
      SELECT workspace_id
      FROM user_workspaces
      WHERE user_id = current_setting('app.current_user_id', true)::integer
    )
  );

-- ============================================================================
-- RLS Policies for refresh_tokens table
-- ============================================================================

-- Users can only access their own refresh tokens
CREATE POLICY token_owner_access ON refresh_tokens
  FOR ALL
  USING (user_id = current_setting('app.current_user_id', true)::integer);

-- ============================================================================
-- RLS Policies for audit_logs table
-- ============================================================================

-- Users can only see their own audit logs
CREATE POLICY audit_self_access ON audit_logs
  FOR SELECT
  USING (user_id = current_setting('app.current_user_id', true)::integer);

-- Admins can see all audit logs in their workspaces
CREATE POLICY audit_admin_access ON audit_logs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_workspaces
      WHERE user_id = current_setting('app.current_user_id', true)::integer
        AND (
          permissions->>'manage_users' = 'true'
          OR permissions->>'manage_workspace' = 'true'
        )
    )
  );

-- ============================================================================
-- AGE Graph RLS Policies
-- ============================================================================

-- Note: AGE stores vertices/edges in special tables
-- Need to add workspace_id column first (Day 6 afternoon task)

-- Decisions vertex (will be created after migration)
-- CREATE POLICY decision_workspace_access ON ag_catalog."Decision"
--   FOR ALL
--   USING (
--     workspace_id = current_setting('app.current_workspace_id', true)
--   );
```

**Acceptance Criteria**:
- [ ] RLS enabled on 4 core tables
- [ ] Policies enforce user isolation
- [ ] Session variables documented
- [ ] AGE graph strategy documented

---

**Afternoon (4 hours): AGE Graph Migration**

**Task 6.2**: Add workspace_id to AGE graph tables (migration script)

```python
# migrations/add_workspace_id_to_graph.py

"""
Migration: Add workspace_id to AGE graph vertices
Part of multi-tenant isolation strategy
"""

import psycopg2
from auth.database import DATABASE_URL

def migrate_add_workspace_id():
    """Add workspace_id column to Decision vertices in AGE graph"""

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Step 1: Add workspace_id column to Decision vertex type
        cur.execute("""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                SET d.workspace_id = '/Users/hue/code/dopemux-mvp'  -- Default workspace
                RETURN count(d) as updated_count
            $$) as (count agtype);
        """)

        result = cur.fetchone()
        print(f"Updated {result[0]} Decision vertices with workspace_id")

        # Step 2: Create index on workspace_id for performance
        # (AGE doesn't support secondary indexes on properties yet)
        # Will rely on application-level filtering until AGE 2.0

        conn.commit()
        print("✓ Migration complete")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_add_workspace_id()
```

**Task 6.3**: Write RLS policy tests (test_rls_policies.py - 300 lines)

```python
# tests/integration/test_rls_policies.py

"""
Test PostgreSQL Row-Level Security policies
"""

import pytest
from sqlalchemy import text

class TestUserRLS:
    """Test RLS policies on users table"""

    @pytest.mark.integration
    def test_user_can_only_see_own_account(self, test_db):
        """Test user can only see their own account"""
        # Create 2 users
        user1 = create_user(test_db, "user1@example.com")
        user2 = create_user(test_db, "user2@example.com")

        # Set session as user1
        test_db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))

        # Query users - should only see self
        users = test_db.query(User).all()
        assert len(users) == 1
        assert users[0].id == user1.id

    @pytest.mark.integration
    def test_user_cannot_see_other_users(self, test_db):
        """Test RLS prevents seeing other users"""
        user1 = create_user(test_db, "user1@example.com")
        user2 = create_user(test_db, "user2@example.com")

        # Set session as user1
        test_db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))

        # Try to query user2 directly
        other_user = test_db.query(User).filter(User.id == user2.id).first()
        assert other_user is None  # RLS blocks access
```

**Acceptance Criteria**:
- [ ] workspace_id added to all Decision vertices
- [ ] Migration script tested on development database
- [ ] RLS policy tests written (50+ tests)
- [ ] Zero cross-workspace data leakage in tests

---

### Day 7 (Tuesday): Query Refactoring

**Full Day (8 hours): Workspace-Scoped Queries**

**Objective**: Refactor all ConPort queries to filter by workspace_id

**Task 7.1**: Refactor queries/overview.py (12 methods, ~150 lines modified)

Before:
```python
def get_recent_decisions(self, limit=3):
    cypher = f"""
        SELECT * FROM cypher('conport_knowledge', $$
            MATCH (d:Decision)
            RETURN d
            ORDER BY d.timestamp DESC
            LIMIT {limit}
        $$) as (decision agtype);
    """
```

After:
```python
def get_recent_decisions(self, workspace_id: str, limit=3):
    cypher = f"""
        SELECT * FROM cypher('conport_knowledge', $$
            MATCH (d:Decision)
            WHERE d.workspace_id = '{workspace_id}'
            RETURN d
            ORDER BY d.timestamp DESC
            LIMIT {limit}
        $$) as (decision agtype);
    """
```

**Files to Refactor**:
- queries/overview.py (12 methods)
- queries/exploration.py (8 methods)
- queries/deep_context.py (10 methods)
- orchestrator.py (5 methods)

**Total**: 35 query methods × ~15 lines each = 500 lines modified

**Acceptance Criteria**:
- [ ] All queries accept workspace_id parameter
- [ ] All Cypher queries filter by workspace_id
- [ ] No regression in existing functionality
- [ ] Performance tests show <10ms overhead

---

### Day 8 (Wednesday): RBAC Middleware

**Morning (4 hours): Authorization Middleware**

**Task 8.1**: Create middleware/rbac_middleware.py (200 lines)

```python
# middleware/rbac_middleware.py

"""
RBAC Middleware for ConPort-KG API
Enforces workspace permissions on all endpoints
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class WorkspaceAuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce workspace permissions.

    Checks:
    1. User is authenticated (has valid JWT)
    2. User is member of requested workspace
    3. User has required permission for operation
    """

    async def dispatch(self, request: Request, call_next):
        # Extract workspace_id from request
        workspace_id = request.query_params.get('workspace_id')

        if not workspace_id:
            # No workspace_id = public endpoint
            return await call_next(request)

        # Get current user from JWT (set by auth dependency)
        user = getattr(request.state, 'current_user', None)

        if not user:
            raise HTTPException(401, "Authentication required")

        # Check workspace membership
        # ... implementation

        # Set session variables for RLS
        db = request.state.db
        db.execute(f"SET LOCAL app.current_user_id = '{user.id}'")
        db.execute(f"SET LOCAL app.current_workspace_id = '{workspace_id}'")

        return await call_next(request)
```

**Afternoon (4 hours): Permission Decorators**

**Task 8.2**: Create auth/permissions.py (150 lines)

```python
# auth/permissions.py

"""
Permission decorators for route handlers
"""

from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(permission: str):
    """
    Decorator to require specific workspace permission.

    Usage:
        @router.delete("/decisions/{id}")
        @require_permission("delete_decisions")
        async def delete_decision(id: int, current_user = Depends(get_current_user)):
            # Only called if user has delete_decisions permission
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get workspace_id from kwargs
            workspace_id = kwargs.get('workspace_id')
            current_user = kwargs.get('current_user')

            # Check permission
            service = UserService()
            has_perm = await service.check_workspace_permission(
                db, current_user.id, workspace_id, permission
            )

            if not has_perm:
                raise HTTPException(403, f"Missing permission: {permission}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Acceptance Criteria**:
- [ ] Middleware enforces workspace access
- [ ] Session variables set for RLS
- [ ] Permission decorators working
- [ ] API routes protected

---

### Day 9 (Thursday): Integration Testing

**Full Day (8 hours): Security Validation**

**Task 9.1**: Create tests/integration/test_workspace_isolation.py (400 lines)

```python
# tests/integration/test_workspace_isolation.py

"""
Test cross-workspace isolation (security critical)
"""

class TestCrossWorkspaceIsolation:
    """Test that users cannot access other workspaces' data"""

    def test_user_cannot_query_other_workspace_decisions(self):
        """Test RLS prevents cross-workspace decision access"""
        # User A in workspace A
        # User B in workspace B
        # User A queries workspace B decisions
        # Expected: Empty results (RLS blocks)
        pass

    def test_user_cannot_create_decision_in_other_workspace(self):
        """Test user cannot create decisions in unauthorized workspace"""
        pass

    # ... 50+ isolation tests
```

**Task 9.2**: Performance regression testing (100 lines)

Test that RLS adds <10ms overhead per query.

**Acceptance Criteria**:
- [ ] 50+ cross-workspace isolation tests
- [ ] 100% passing (zero data leakage)
- [ ] Performance overhead <10ms
- [ ] RLS policies validated

---

### Day 10 (Friday): Week 2 Validation

**Morning (4 hours): Security Audit**

**Task 10.1**: Run comprehensive security tests
- Cross-workspace isolation (50 tests)
- Permission enforcement (30 tests)
- RLS policy effectiveness (20 tests)

**Task 10.2**: Update security score assessment
- Before: 6/10
- After Week 2: 7/10 (database-level isolation)

**Afternoon (4 hours): Week 2 Demo + Documentation**

**Task 10.3**: Create Week 2 summary document
**Task 10.4**: Prepare demo for stakeholders
**Task 10.5**: Plan Week 3 (Event Bus infrastructure)

**Acceptance Criteria**:
- [ ] All security tests passing
- [ ] Security score 7/10 achieved
- [ ] Week 2 demo prepared
- [ ] Ready for Week 3 (Event Bus)

---

## Week 2 Success Criteria

- [ ] RLS policies enforcing workspace isolation
- [ ] All queries workspace-scoped
- [ ] Zero cross-workspace data leakage
- [ ] Security score: 7/10
- [ ] Performance: <10ms RLS overhead
- [ ] 150+ total tests passing
- [ ] Ready for Phase 2 (Agent Integration)

---

**Week 2 Target**: 1,450 lines
**Expected Total After Week 2**: 6,350 lines
**11-Week Progress After Week 2**: 18% complete
