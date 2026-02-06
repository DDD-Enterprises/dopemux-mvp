---
id: adr-180
title: 'ADR-180: Automatic Instance Resume After Crashes'
type: adr
owner: dopemux-core
date: 2025-10-04
status: proposed
adhd_cognitive_load: 0.5
adhd_attention_required: medium
tags:
- multi-instance
- session-recovery
- adhd-optimization
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
prelude: 'ADR-180: Automatic Instance Resume After Crashes (adr) for dopemux documentation
  and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-180: Automatic Instance Resume After Crashes

## Status

**Proposed** (Enhancement for multi-instance support)

**Depends On**: ADR-179 (ConPort Worktree Support)

## Context

Multi-instance support (implemented 2025-10-04) enables parallel ADHD-optimized development workflows. However, when an instance crashes or is terminated:

**Current Behavior** (MVP):
- Worktree persists on disk ✅
- ConPort data persists in PostgreSQL ✅
- Running services stop (port-based detection fails) ❌
- Instance registration lost (in-memory only) ❌
- User must manually resume or recreate ❌

**User Pain Point**:
```bash
# Instance B crashes
# User runs dopemux start again
# System doesn't know B existed
# Offers to create new instance
# But worktree B already exists!
# git worktree add → ERROR: worktree already exists
```

**ADHD Impact**: Context switching overhead increased, cognitive load for manual recovery.

## Decision

Implement **automatic instance resume detection** to enable zero-friction recovery from crashes.

### Core Components

**1. Instance State Persistence (ConPort)**

Store instance state in ConPort `custom_data` category:

```python
# Category: "instance_state"
# Key: instance_id (e.g., "B")
# Value: {
#   "instance_id": "B",
#   "port_base": 3030,
#   "worktree_path": "/Users/hue/code/dopemux-mvp/worktrees/B",
#   "git_branch": "feature/auth",
#   "created_at": "2025-10-04T10:00:00",
#   "last_active": "2025-10-04T12:30:00",
#   "status": "orphaned",  # active, stopped, orphaned
#   "last_working_directory": "/Users/hue/code/dopemux-mvp/worktrees/B/src",
#   "last_focus_context": "authentication"
# }
```

**2. Orphan Detection on `dopemux start`**

Enhanced startup flow:

```
dopemux start
    ↓
1. Detect running instances (health probe ports)
    ↓
2. Load persisted instance states from ConPort
    ↓
3. Find orphaned instances:
   - Worktree exists on disk
   - State shows "active" or "orphaned"
   - But health probe failed (no running services)
    ↓
4. Present options to user:
   a) Resume orphaned instance
   b) Start new instance
   c) Cleanup orphaned instance
```

**3. User Experience**

**Scenario 1: Instance Crashed (Orphan Detected)**

```bash
dopemux start

⚠️  Found orphaned instance:
┏━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Instance┃ Port ┃ Branch       ┃ Last Active          ┃
┡━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ B       │ 3030 │ feature/auth │ 5 minutes ago        │
└─────────┴──────┴──────────────┴──────────────────────┘

💡 Worktree exists but services stopped (likely crash)

Resume instance B? [Y/n]:
```

**If Yes:**
```bash
✅ Resuming instance B on port 3030
📁 Worktree: worktrees/B (feature/auth)
🔄 Restoring environment variables...
🚀 Starting services...
   - ConPort: port 3037 ✅
   - Serena: port 3036 ✅
   - Task-Master: port 3035 ✅

✅ Instance B resumed successfully!
📍 You were working on: authentication (JWT middleware)
```

**If No:**
```bash
Options:
1. Start new instance (C) on port 3060
2. Cleanup orphaned instance B and start fresh
3. Cancel

Choice [1-3]:
```

**Scenario 2: Clean Shutdown (No Orphans)**

```bash
# User Ctrl+C in instance B
# dopemux catches signal
# Marks instance as "stopped" in ConPort

dopemux start

✅ Found 1 running instance (A)

Previous session (B) cleanly stopped.

Resume instance B? [Y/n]:
```

**Scenario 3: Multiple Orphans**

```bash
dopemux start

⚠️  Found 2 orphaned instances and 1 running:

Running:
┏━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Instance┃ Port ┃ Branch ┃ Status  ┃
┡━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ A       │ 3000 │ main   │ ✅ Healthy│
└─────────┴──────┴────────┴─────────┘

Orphaned:
┏━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Instance┃ Port ┃ Branch       ┃ Last Active   ┃
┡━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ B       │ 3030 │ feature/auth │ 10 mins ago   │
│ C       │ 3060 │ hotfix/redis │ 2 hours ago   │
└─────────┴──────┴──────────────┴───────────────┘

Select an instance to resume, or start new (D):
[B/C/D]:
```

### Implementation Plan

**Phase 1: State Persistence (ConPort Integration)**

```python
# src/dopemux/instance_state.py
class InstanceStateManager:
    def save_instance_state(state: InstanceState) -> None:
        """Persist to ConPort custom_data."""

    def load_instance_state(instance_id: str) -> Optional[InstanceState]:
        """Load from ConPort custom_data."""

    def find_orphaned_instances() -> List[InstanceState]:
        """Find instances with worktrees but no running services."""
```

**Phase 2: Enhanced Instance Detection**

```python
# src/dopemux/instance_manager.py
class InstanceManager:
    def detect_orphaned_instances(self) -> List[OrphanedInstance]:
        """
        Find instances with:
        1. Persisted state in ConPort
        2. Worktree exists on disk
        3. Health probe fails (no running services)
        """

    def resume_instance(self, instance_id: str) -> bool:
        """
        Resume orphaned instance:
        1. Load state from ConPort
        2. Verify worktree exists
        3. Inject environment variables
        4. Start services on saved port_base
        5. Update state to 'active'
        """
```

**Phase 3: CLI Integration**

```python
# src/dopemux/cli.py (enhanced start command)
def start(...):
    # Existing: detect running instances
    running = instance_manager.detect_running_instances()

    # NEW: detect orphaned instances
    orphaned = instance_manager.detect_orphaned_instances()

    if orphaned:
        # Show table of orphaned instances
        # Prompt user to resume or cleanup
        selected = prompt_orphan_selection(orphaned)

        if selected:
            instance_manager.resume_instance(selected.instance_id)
            return

    # Continue with existing flow (create new instance)
```

**Phase 4: Graceful Shutdown**

```python
# src/dopemux/cli.py (signal handlers)
def handle_shutdown(signal, frame):
    """
    Catch Ctrl+C:
    1. Mark instance as 'stopped' in ConPort
    2. Save last_active timestamp
    3. Clean shutdown of services
    """

    instance_state.mark_instance_stopped(current_instance_id)
    cleanup_services()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)
```

## Consequences

### Positive

**1. Zero-Friction Recovery**
- Crashes become invisible to user
- Resume with single confirmation
- All context preserved (worktree, data, environment)

**2. ADHD Optimization**
- No manual environment variable export
- No cognitive load for "how do I resume?"
- One-click return to previous context

**3. Better State Hygiene**
- Orphaned worktrees automatically detected
- Clear prompts for cleanup or resume
- Prevents disk space bloat

**4. Data Integrity**
- ConPort data always safe (PostgreSQL persistence)
- Worktree changes preserved
- Instance state tracking enables recovery

### Negative

**1. Complexity**
- Additional state management layer
- ConPort MCP client required for CLI
- More error cases to handle

**2. ConPort Dependency**
- CLI now depends on ConPort being accessible
- If ConPort database down, can't load state
- Need fallback to current behavior

**3. Edge Cases**
- Multiple processes trying to resume same instance
- ConPort state out of sync with filesystem
- Port conflicts if user manually changed ports

### Mitigations

**ConPort Unavailable**:
```python
try:
    orphaned = instance_manager.detect_orphaned_instances()
except ConPortUnavailable:
    console.print("[yellow]⚠️  ConPort unavailable, resuming disabled[/yellow]")
    # Fall back to current behavior (create new instance)
```

**Port Conflicts**:
```python
if not is_port_available(state.port_base):
    console.print(f"[yellow]⚠️  Port {state.port_base} in use[/yellow]")
    new_port = instance_manager.get_next_available_port()
    console.print(f"[blue]Using port {new_port} instead[/blue]")
    state.port_base = new_port
```

**Filesystem Mismatch**:
```python
if not Path(state.worktree_path).exists():
    console.print(f"[yellow]⚠️  Worktree missing for instance {state.instance_id}[/yellow]")
    console.print("[dim]Marking as cleaned up in database...[/dim]")
    instance_state_manager.cleanup_instance_state(state.instance_id)
```

## Implementation Timeline

**Phase 1 (InstanceStateManager)**: 2 hours
- ConPort integration
- State persistence
- Load/save/list methods

**Phase 2 (Orphan Detection)**: 2 hours
- Enhanced InstanceManager
- Orphan detection logic
- Resume functionality

**Phase 3 (CLI Integration)**: 2 hours
- Enhanced `dopemux start`
- Interactive prompts
- Rich table displays

**Phase 4 (Signal Handlers)**: 1 hour
- Graceful shutdown
- State cleanup
- Testing

**Total**: ~7 hours (vs current gap of "manual recovery required")

## Alternatives Considered

### Alternative 1: Session Files (.dopemux-instance)

Store instance state in project directory:

```bash
worktrees/B/.dopemux-instance
{
  "instance_id": "B",
  "port_base": 3030,
  "created_at": "2025-10-04T10:00:00"
}
```

**Rejected**:
- Scattered state (one file per worktree)
- No centralized view of all instances
- Git worktree removal deletes state
- ConPort already provides centralized storage

### Alternative 2: SQLite Database

Create separate SQLite database for instance state:

```python
~/.dopemux/instances.db
```

**Rejected**:
- Introduces new dependency
- ConPort already exists and is production-ready
- Duplicate state management
- Not workspace-aware

### Alternative 3: Redis Cache

Use Redis for ephemeral state:

**Rejected**:
- Requires Redis installation
- Ephemeral (lost on Redis restart)
- Overkill for simple state tracking
- ConPort more appropriate

## Testing Strategy

**Unit Tests**:
```python
def test_save_instance_state():
    """Test state persistence to ConPort."""

def test_load_instance_state():
    """Test state retrieval from ConPort."""

def test_find_orphaned_instances():
    """Test orphan detection logic."""

def test_resume_instance():
    """Test instance resume flow."""
```

**Integration Tests**:
```bash
# Test 1: Crash recovery
start instance B → kill -9 → dopemux start → verify resume offered

# Test 2: Clean shutdown
start instance B → Ctrl+C → dopemux start → verify clean stop detected

# Test 3: Multiple orphans
start B → crash → start C → crash → dopemux start → verify both detected

# Test 4: Port conflict
start B → mark orphaned → start different service on 3030 → resume B → verify new port
```

**Manual Validation**:
- Crash instance and verify resume
- Clean shutdown and verify detection
- Multiple orphans selection
- ConPort unavailable fallback

## Documentation Updates

**User Guide** (`docs/02-how-to/multi-instance-workflow.md`):
- Add "Session Recovery" section
- Document resume prompts
- Show orphan cleanup workflow

**Troubleshooting**:
- "Instance won't resume" (port conflicts, ConPort down)
- "Multiple orphans detected" (selection workflow)
- "State out of sync" (manual cleanup)

## Success Metrics

**Recovery Time**:
- Current: ~2 minutes (manual env vars + restart)
- Target: ~10 seconds (automatic resume with confirmation)

**User Actions**:
- Current: 5+ actions (cd, export, export, start, troubleshoot)
- Target: 1 action (confirm resume)

**Cognitive Load**:
- Current: High (remember instance ID, ports, env vars)
- Target: Minimal (system remembers everything)

## Decision

✅ **APPROVED** for implementation as Phase 3 enhancement to multi-instance support.

**Rationale**:
- Significant ADHD UX improvement
- Leverages existing ConPort infrastructure
- Low implementation risk (7 hours)
- High user value (zero-friction recovery)

**Implementation Priority**: P1 (after MVP validation)

---

**Author**: Claude Code with SuperClaude framework
**Reviewers**: dopemux-core
**Related**: ADR-179 (ConPort Worktree Support)
**Status**: Proposed (Implementation planned for Phase 3)
