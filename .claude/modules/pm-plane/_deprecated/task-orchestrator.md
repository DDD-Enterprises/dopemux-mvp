# Task Management System (ConPort + Python ADHD Engine)

**Architecture Version**: 2.0 (Simplified)
**Authority**: Task storage, ADHD optimization, progress tracking
**Decision Reference**: #132 (Simplified architecture - skip jpicklyk)
**Storage**: ConPort PostgreSQL AGE (not external orchestrators)

## Architectural Decision

Per Decision #132, we use **ConPort + SuperClaude + Python ADHD Engine** instead of external orchestrators:
- **No jpicklyk** (ConPort PostgreSQL AGE is superior to SQLite)
- **No Task-Master-AI** (SuperClaude `/dx:prd-parse` handles PRD decomposition)
- **Python ADHD Engine** provides unique cognitive optimization value

## Authority Boundaries

**ConPort (PostgreSQL AGE) Owns:**
- Task storage via `progress_entry` (TODO/IN_PROGRESS/DONE/BLOCKED)
- Task metadata via `custom_data` category "task_metadata"
- Dependencies via `link_conport_items` (BLOCKS, DEPENDS_ON, RELATES_TO)
- Knowledge graph queries for unblocked tasks, critical paths
- Decision logging for task-related architectural choices

**Python ADHD Engine Owns:**
- Energy tracking and matching tasks to current energy levels
- Cognitive load calculation (0-1 scale)
- Break monitoring (25min sessions, 60min warnings, 90min mandatory)
- Attention state analysis (focused/scattered/transitioning)
- Smart task routing based on ADHD metrics
- Hyperfocus protection

**SuperClaude Owns:**
- PRD parsing via `/dx:prd-parse` with Zen planner
- Human review workflow (Approach C for quality)
- JSON schema validation before ConPort import
- ADHD metadata injection (complexity, duration, energy)

## ConPort Task Storage Schema

### Task Structure
```bash
# Tasks stored as progress_entry
mcp__conport__log_progress \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --status "TODO" \
  --description "Implement user authentication - OAuth2 flow" \
  --parent_id 123  # Optional: for subtask hierarchies

# Task metadata in custom_data
mcp__conport__log_custom_data \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --category "task_metadata" \
  --key "task-456-metadata" \
  --value '{
    "complexity_score": 0.6,
    "energy_required": "high",
    "cognitive_load": 0.7,
    "estimated_minutes": 45,
    "break_points": [25],
    "files_affected": ["auth.py", "oauth.py"],
    "adhd_notes": "Complex logic - best during high energy periods"
  }'

# Dependencies via links
mcp__conport__link_conport_items \
  --workspace_id "/Users/hue/code/dopemux-mvp" \
  --source_item_type "progress_entry" \
  --source_item_id "456" \
  --target_item_type "progress_entry" \
  --target_item_id "789" \
  --relationship_type "BLOCKS" \
  --description "OAuth2 implementation must complete before user profile features"
```

### Graph Queries (PostgreSQL AGE)
```cypher
-- Find all unblocked TODO tasks
MATCH (t:Task {status: 'TODO'})
WHERE NOT EXISTS {
  (blocker:Task)-[:BLOCKS]->(t)
  WHERE blocker.status <> 'DONE'
}
RETURN t

-- Critical path calculation
MATCH path = (start:Task {status: 'TODO'})-[:BLOCKS*]->(end:Task)
RETURN path, length(path) as depth
ORDER BY depth DESC
LIMIT 10

-- Parallel task identification (no blocking relationships)
MATCH (t1:Task {status: 'TODO'}), (t2:Task {status: 'TODO'})
WHERE NOT EXISTS {(t1)-[:BLOCKS|DEPENDS_ON]-(t2)}
RETURN t1, t2
```

## Python ADHD Engine Integration

### Energy-Aware Task Selection
```python
# ADHD engine queries ConPort for optimal task selection
from services.adhd_engine import TaskSelector

selector = TaskSelector(conport_client)

# Get current ADHD state
user_state = selector.get_current_state()
# Returns: {"energy": "high", "attention": "focused", "cognitive_load": 0.3}

# Query ConPort for matching tasks
optimal_tasks = selector.recommend_tasks(
    max_tasks=3,
    energy_level=user_state["energy"],
    attention_state=user_state["attention"]
)
# Returns: Top 3 tasks ranked by suitability
```

### 25-Minute Focus Sessions
```python
# Session management with auto-save
from services.adhd_engine import SessionManager

session = SessionManager(conport_client)

# Start session
session.start_session(task_id=456)
# - Sets 25min timer
# - Updates active_context with session_start
# - Auto-saves to ConPort every 5min

# Break trigger at 25min
session.on_timer_complete()
# - Gentle notification: "Great work! Time for 5min break"
# - Auto-pause task (preserve context)
# - Track break in custom_data "break_history"

# Hyperfocus protection
session.warn_at_60min()  # Warn if no break taken
session.mandate_break_at_90min()  # Force break for health
```

## Production Features

### Task Locking (Prevent Conflicts)
```sql
-- PostgreSQL row-level locking for concurrent access
SELECT * FROM progress_entries
WHERE status = 'TODO'
FOR UPDATE SKIP LOCKED
LIMIT 1
```

### Retry Logic & Dead-Letter Queue
```python
# Track retry attempts in custom_data
{
  "retry_count": 0,
  "max_retries": 3,
  "last_error": null,
  "dlq_timestamp": null
}

# Move to dead-letter queue after max retries
if task["retry_count"] >= task["max_retries"]:
    move_to_dlq(task)
    notify_team("Task {task_id} moved to DLQ")
```

### Real-Time Dashboard Updates
```python
# PostgreSQL LISTEN/NOTIFY for live updates
import asyncpg

await conn.execute("LISTEN task_updates")
async for notification in conn.notifications():
    dashboard.update(notification.payload)
```

## ADHD Optimizations

- ✅ **25-minute focus sessions** with automatic break reminders
- ✅ **Energy-aware task selection** from ConPort ADHD metadata
- ✅ **Auto-save every 5 minutes** to preserve context during interruptions
- ✅ **Gentle re-orientation** after context switches: "You were working on X"
- ✅ **Hyperfocus protection** (warn at 60min, mandate break at 90min)
- ✅ **Cognitive load monitoring** (warn if >0.8)
- ✅ **Context switch tracking** (minimize unnecessary switches)
- ✅ **Visual progress indicators**: `[████░░░░] 4/8 complete ✅`

## Workflow: PRD to Implementation

1. **PRD Document** → User provides requirements
2. **`/dx:prd-parse`** → SuperClaude + Zen planner decompose into task hierarchy
3. **Human Review** → User approves JSON output (Approach C quality gate)
4. **Python Validator** → Schema validation + ADHD metadata injection
5. **ConPort Batch Import** → `log_progress` + `link_conport_items` + `custom_data`
6. **ADHD Engine Queries** → Smart task recommendation based on energy/attention
7. **Dashboard Display** → React Ink UI shows visual task progress

## Migration Notes

**What We Replaced:**
- ❌ jpicklyk task-orchestrator (37 tools, SQLite limits, Kotlin/JVM complexity)
- ❌ Task-Master-AI (PRD parsing redundant with SuperClaude)
- ❌ External workflow orchestration (added unnecessary complexity)

**What We Kept:**
- ✅ ConPort PostgreSQL AGE (production-grade graph database)
- ✅ ADHD intelligence (Python engine - our unique value-add)
- ✅ SuperClaude command framework (25 commands, 15 agents)
- ✅ Event-driven architecture (Redis Streams, EventBus)

---

**See Also:**
- `.claude/modules/superclaude-integration.md` - SuperClaude configuration
- `.claude/modules/custom-commands.md` - `/dx:` command reference
- `.claude/modules/adhd-patterns.md` - ADHD session management patterns
