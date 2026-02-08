---
id: F002_IMPLEMENTATION_PLAN
title: F002_Implementation_Plan
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: F002_Implementation_Plan (explanation) for dopemux documentation and developer
  workflows.
---
# F002 Multi-Session Support - Implementation Plan

**Date**: 2025-10-18
**Status**: Design Complete - Ready to Build
**Approach**: Ultrathink Analysis (Manual - Zen MCPs offline)

---

## Architecture Decision

### Chosen Approach: Serena-Specific Session Manager

**Rationale**:
- Lightweight for critical-path statusline performance
- ADHD-optimized specifically for ConPort integration
- Focused on worktree + multi-session coordination
- Avoids MetaMCP coupling

**Trade-offs Accepted**:
- Some code duplication vs MetaMCP SessionManager
- Maintenance overhead (worth it for performance)

---

## Implementation Components (6 Modules)

### Component 1: Session ID Generator
**File**: `services/serena/v2/session_id_generator.py`

**Purpose**: Generate unique collision-resistant session IDs

**Features**:
- Transcript-based naming (Claude Code session dirs)
- Millisecond timestamp suffix for uniqueness
- UUID fallback if transcript unavailable
- Format: `session_abc123_1696435200123`

**Implementation**:
```python
class SessionIDGenerator:
    def generate(transcript_path: str = None) -> str:
        timestamp_ms = int(datetime.now().timestamp() * 1000)

        if transcript_path:
            transcript_id = Path(transcript_path).parent.name
            return f"session_{transcript_id}_{timestamp_ms}"
        else:
            return f"session_{uuid.uuid4().hex[:12]}_{timestamp_ms}"
```

**Collision Resistance**: Millisecond precision + UUID = virtually impossible

---

### Component 2: Worktree Detector
**File**: `services/serena/v2/worktree_detector.py`

**Purpose**: Detect git worktree info and map to main workspace

**Features**:
- Python implementation (no bash dependency)
- Detects: main repo path, current worktree, branch
- Returns workspace_id (always main repo) + worktree metadata
- Handles non-git, single-repo, multi-worktree cases

**Implementation**:
```python
class WorktreeDetector:
    def detect(current_dir: Path) -> WorktreeInfo:
        # 1. Check if git repo
        # 2. Run git worktree list
        # 3. Determine main repo path
        # 4. Identify current worktree type

        return WorktreeInfo(
            workspace_id=main_repo_path,    # Always main repo
            worktree_path=current_path,      # Current worktree or None
            branch=current_branch,
            worktree_type="main"|"worktree"|"single"|"not_git"
        )
```

**Edge Cases Handled**:
- Not in git repo → use current_dir as workspace_id
- Single repo (no worktrees) → worktree_path = None
- Main worktree → worktree_path = workspace_id
- Secondary worktree → worktree_path = current dir

---

### Component 3: Session Lifecycle Manager
**File**: `services/serena/v2/session_lifecycle_manager.py`

**Purpose**: Manage session start, update, complete, cleanup

**Features**:
- Session creation with ConPort integration
- Periodic heartbeat updates (every 30s)
- Session completion with duration tracking
- Stale session cleanup (24h auto-expire)

**Key Methods**:
```python
class SessionLifecycleManager:
    async def start_session(worktree_info, initial_focus) -> SessionState
    async def update_session(session_id, focus, content_patch)
    async def complete_session(session_id, summary)
    async def cleanup_stale_sessions(workspace_id, max_age_hours=24)
    async def validate_worktree_paths(workspace_id)  # Edge case 3
```

**ConPort Integration**:
- Stores in `active_context` table
- Uses composite key: (workspace_id, session_id)
- Updates `last_updated` timestamp on every change

---

### Component 4: Multi-Session Dashboard
**File**: `services/serena/v2/multi_session_dashboard.py`

**Purpose**: Format startup display of all active sessions

**Features**:
- Queries all active sessions for workspace
- Groups by worktree (main, feature-auth, bugfix-login)
- Shows time since last activity
- ADHD-optimized: max 10 sessions shown (prevent overwhelm)

**Output Format**:
```
🔄 ACTIVE SESSIONS
─────────────────────────────────────────────

Main worktree (main):
   • [active] Code review
   • [active] Documentation (Terminal 2) ⚠️ multiple

Worktree: feature-auth (feature/auth):
   • [30m ago] JWT implementation

Worktree: bugfix-login (bugfix/login):
   • [2h ago] Debugging redirect

Total: 4 active session(s), 2 worktree(s)

💡 Continue current session or switch worktree?
```

**ADHD Accommodations**:
- Progressive disclosure (summary → details on request)
- Time anchors ([30m ago], [2h ago])
- Warning for multiple sessions same worktree
- Clear next action suggestion

---

### Component 5: ConPort Schema Migrator
**File**: `services/serena/v2/migrations/002_add_session_support.sql`

**Purpose**: Migrate active_context to support multi-session

**Migration Steps**:
1. Add columns (session_id, worktree_path, branch, last_updated, status)
2. Create composite primary key (workspace_id, session_id)
3. Create performance indexes
4. Add status constraints

**Backward Compatibility**:
- All new columns have defaults (session_id='default')
- Existing rows migrate automatically
- Old single-session queries still work during transition

**Rollback Plan**:
```sql
-- Rollback if needed
BEGIN;
ALTER TABLE active_context DROP CONSTRAINT IF EXISTS active_context_pkey;
ALTER TABLE active_context ADD PRIMARY KEY (workspace_id);
ALTER TABLE active_context DROP COLUMN IF EXISTS session_id;
-- ... drop other columns
COMMIT;
```

---

### Component 6: Session Integration Layer
**File**: `services/serena/v2/session_manager.py` (main coordinator)

**Purpose**: Coordinate all session components

**Features**:
- Initializes session on Serena startup
- Integrates worktree detection + session ID generation
- Manages lifecycle (start/update/complete)
- Provides dashboard data for statusline
- Handles all 5 edge cases from spec

**Integration Points**:
- ConPort MCP client (for database operations)
- Worktree detector (for workspace info)
- Session ID generator (for unique IDs)
- Multi-session dashboard (for display)

---

## Database Schema Changes

### active_context Migration

**Before**:
```sql
workspace_id (PK) | content (JSONB)
```

**After**:
```sql
workspace_id | session_id | worktree_path | branch | last_updated | status | content (JSONB)
(PK: workspace_id + session_id)
```

### New session_history Table

**Schema**:
```sql
workspace_id | session_id | worktree_path | branch | content | created_at | completed_at | duration_minutes
(PK: workspace_id + session_id)
```

**Purpose**: Archive completed sessions for analytics

---

## Implementation Order

### Phase 1: Foundation (Build Components)
1. ✅ Session ID Generator (50 lines)
2. ✅ Worktree Detector (150 lines)
3. ✅ Dashboard Formatter (200 lines)

### Phase 2: Lifecycle (Session Management)
1. ✅ Session Lifecycle Manager (300 lines)
2. ✅ Session Manager Coordinator (250 lines)

### Phase 3: Database (Schema Migration)
1. ✅ Create migration SQL script
2. ✅ Test migration on dev database

### Phase 4: Integration (Wire Everything Together)
1. ✅ Add MCP tools for session operations
2. ✅ Update statusline.sh to use sessions
3. ✅ Integrate into Serena v2 startup

### Phase 5: Validation
1. ✅ Test single session (backward compat)
2. ✅ Test multi-session (2-3 Claude instances)
3. ✅ Test worktree detection
4. ✅ Test session dashboard

---

## Edge Cases Handled

1. **Session ID collisions**: Millisecond timestamp + UUID
2. **Orphaned sessions**: Auto-cleanup after 24h
3. **Deleted worktrees**: Path validation on startup
4. **Multiple sessions same worktree**: Allow with warning
5. **Branch mismatch**: Detect and auto-update

---

## ADHD Optimizations

### Context Preservation
- Session state persists across interruptions
- Each session maintains independent focus
- Shared knowledge graph (decisions, progress)

### Parallel Work
- Multiple sessions = multiple contexts
- Worktrees = physical separation
- No mental context-switching overhead

### Startup Clarity
- Dashboard shows all active work immediately
- Time anchors help resume ([30m ago])
- Grouped by worktree for mental clarity

### Performance
- Dashboard query: < 50ms target
- Session update: < 100ms target
- Statusline refresh: < 150ms total (includes session query)

---

## Risk Assessment

### Low Risk
✅ Worktree detection (git commands, well-tested)
✅ Session ID generation (simple logic)
✅ Dashboard formatting (pure display logic)

### Medium Risk
⚠️ Database migration (need testing on dev first)
⚠️ Composite primary key change (data integrity)
⚠️ ConPort MCP integration (API changes)

### High Risk
🔴 None - all components have fallbacks and rollback plans

---

## Testing Strategy

### Unit Tests
- `test_session_id_generator.py` (collision resistance)
- `test_worktree_detector.py` (all 4 detection types)
- `test_dashboard_formatter.py` (display logic)
- `test_lifecycle_manager.py` (start/update/complete)

### Integration Tests
- `test_multi_session_integration.py` (2+ sessions)
- `test_worktree_integration.py` (main + 2 worktrees)
- `test_migration.py` (backward compatibility)

### Manual Testing
- Open 2-3 Claude Code instances
- Verify each gets unique session_id
- Check dashboard shows all sessions
- Test worktree switching
- Validate ConPort data isolation

---

## Success Metrics

### Functionality
- ✅ 2-10 concurrent sessions supported
- ✅ Worktrees map to unified workspace_id
- ✅ Dashboard shows all active work
- ✅ Session isolation working

### Performance
- ✅ Startup dashboard: < 50ms
- ✅ Session update: < 100ms
- ✅ Statusline refresh: < 150ms

### ADHD Impact
- ✅ Context preserved across interruptions
- ✅ Parallel work without mental overhead
- ✅ Clear visibility of all active work
- ✅ Easy session switching

---

## Next Actions

**Immediate** (Start Building):
1. Create `session_id_generator.py`
2. Create `worktree_detector.py`
3. Create `multi_session_dashboard.py`

**After Foundation**:
4. Create `session_lifecycle_manager.py`
5. Create `session_manager.py` (coordinator)
6. Create migration SQL

**Integration**:
7. Add MCP tools
8. Test thoroughly
9. Document usage

---

**Estimated Effort**: 3-4 hours for complete F002 implementation
**Complexity**: Medium (database migration is main risk)
**ADHD Score**: 10.0 (enables parallel work without context loss)

**Ready to build?** Let's start with Component 1: Session ID Generator!
