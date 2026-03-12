# WORKFLOW_AND_GATES.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. Session Lifecycle

### Session States
Source: `session_lifecycle_manager.py:24` — `SessionState` dataclass

```
status: active | completed | invalid_worktree
```

### Session Lifecycle Flow
```
[Server Start]
    │
    ▼
initialize() ─── detect workspace (.git walk-up)
    │              start file_watcher
    │
    ▼
[Awaiting tool calls]
    │
    ├── initialize_session_tool() ◄── DEAD CODE (not registered)
    │   Creates SessionState with:
    │   - session_id (UUID-based)
    │   - workspace_id (git root)
    │   - worktree_path
    │   - branch
    │   - current_focus
    │
    ├── update_session()
    │   - Patches focus, content
    │   - Persists to ConPort
    │
    ├── complete_session()
    │   - Calculates duration
    │   - Status → completed
    │   - Persists final state
    │
    └── cleanup_stale_sessions()
        - Auto-expire after 24 hours
        - Status → completed
```

**NOTE**: Session lifecycle tools (`initialize_session`, `get_session_info`, `get_multi_session_dashboard`) exist as handler methods but are NOT registered in `list_tools()` or dispatched in `call_tool()`. Session management is dead code at the MCP level.

### Session Storage
- **ConPort**: Sessions stored via `log_custom_data()` with category `sessions`
- **In-memory**: `current_focus_mode` on `SerenaV2MCPServer` (resets on restart)

## 2. Focus Mode State Machine

Source: `mcp_server.py:421` (in-memory), `focus_manager.py`

### States
```
focused ──────► scattered
   ▲                │
   │                ▼
   └── transitioning ◄─┘
```

### Focus Mode Effects
| State | Max Results | Description | Source |
|-------|-------------|-------------|--------|
| `focused` | 10 | Full cognitive capacity | `filter_by_focus_tool:2492` |
| `scattered` | 3 | Reduce overwhelm | `filter_by_focus_tool:2493` |
| `transitioning` | 5 | Moderate filtering | `filter_by_focus_tool:2494` |

### Persistence
- **Current**: In-memory only (`self.current_focus_mode = "focused"`)
- **Reset**: Defaults to `"focused"` on server restart
- **Planned**: Phase 3 will persist to database

### ADHD Engine Integration
Source: `mcp_server.py:74-135` — `_get_adhd_config()`, `get_dynamic_max_results()`

The external ADHD Engine (at `services/adhd_engine/`) can override result limits dynamically:
```python
max_results = await get_dynamic_max_results(user_id, max_results)
# Returns: 3-40 based on ADHD Engine state assessment
```

Feature flags: `_adhd_feature_flags` global (lazy-loaded)

## 3. Cognitive Load Tracking

### Focus Manager
Source: `focus_manager.py`

| Component | Purpose |
|-----------|---------|
| `FocusMode` enum | focused, scattered, transitioning |
| `AttentionState` enum | Attention level tracking |
| `FocusSession` dataclass | Timed focus session (25 min) |
| `FocusManager` class | Session management |
| `_assess_attention_state()` | Break suggestion logic (line 339) |

### 25-Minute Focus Windows
Source: `focus_manager.py` — FocusSession

- Default session length: 25 minutes (Pomodoro)
- `break_after_minutes: 25` hardcoded in `analyze_complexity_tool:2393`
- `chunk_if_exceeds_minutes: 15` for complex code
- Reading order tool calculates Pomodoro sessions needed: `sessions = max(1, round(total_minutes / 25))`

### Cognitive Load Manager
Source: `adhd_features.py:581` — `CognitiveLoadManager`

Manages cognitive load across tool interactions with:
- Progressive disclosure (`ProgressiveDisclosure.apply_to_results()` at line 507)
- Result count limiting based on attention state
- Complexity-based content gating

### Progressive Disclosure
Source: `adhd_features.py:507` — `ProgressiveDisclosure`

Three-level progressive disclosure pattern:
- **Level 1**: Summary (dashboard at-a-glance)
- **Level 2**: Breakdown (per-feature sections)
- **Level 3**: Trends (time-series data)

Enforced limits:
- Max 5 items per section
- Max 10 results per tool output
- 3-file preview for branch clusters

## 4. ADHD Accommodation Flow

### Result Filtering Pipeline
```
[Raw results from LSP/grep/analysis]
    │
    ▼
get_dynamic_max_results(user_id, default)  ◄── ADHD Engine
    │  Returns: 3-40 based on attention state
    ▼
[Apply max_results cap]
    │
    ▼
filter_by_focus_tool()  ◄── Manual focus state
    │  focused: 10, scattered: 3, transitioning: 5
    ▼
[Progressive Disclosure]
    │  Level 1/2/3 content gating
    ▼
[ADHD-formatted output]
    │  ✅ emoji indicators
    │  → highlighted lines
    │  >>> definition markers
    ▼
[TextContent JSON response]
```

### Complexity Assessment Pipeline
```
[File path input]
    │
    ▼
_ensure_component("tree_sitter")
    │
    ├── [Tree-sitter available]
    │   ▼
    │   analyze_complexity()
    │   Returns: cyclomatic, nesting, lines, functions
    │
    └── [Tree-sitter unavailable]
        ▼
        Fallback: Line-count heuristic
        0-100 lines → 0.0-0.3
        100-500 lines → 0.3-0.6
        500+ lines → 0.6-1.0
    │
    ▼
[Score 0.0-1.0]
    │
    ├── <0.3: "LOW - Safe to read anytime"
    ├── 0.3-0.6: "MEDIUM - Needs focus"
    └── >0.6: "HIGH - Complex code"
    │
    ▼
safe_reading_minutes = score × 15
```

## 5. Task Complexity Assessment

### Untracked Work Confidence Scoring
Source: `untracked_work_detector.py`

Multi-signal confidence scoring:
```
[Git detection]  →  has_uncommitted, file_count, branch_type
[ConPort matching]  →  is_orphaned, matched_tasks
[Filesystem signals]  →  modification times, file patterns
    │
    ▼
confidence_score: 0.0-1.0
    │
    ▼
[Adaptive threshold per session]
  Session 1: threshold = 0.75
  Session 2: threshold = 0.65
  Session 3+: threshold = 0.60
    │
    ▼
passes_threshold = confidence >= threshold
    │
    ├── [Below threshold] → "all_clear"
    │
    └── [Above threshold] → "untracked_work_detected"
        │
        ├── auto_track (if confidence >= 0.85)
        │   Creates ConPort task automatically
        │
        └── [User choice]
            ├── track → Create ConPort task
            ├── snooze → Delay reminder (1h/4h/1d)
            └── ignore → Mark abandoned
```

### Grace Period Gate
Source: `untracked_work_detector.py:246`

```
_threshold_for_session(session_number):
  if session_number == 1: return 0.75  # Conservative
  if session_number == 2: return 0.65  # Moderate
  return 0.60                           # Aggressive (session 3+)
```

30-minute grace period: Work younger than 30 minutes is not flagged (allows exploratory work).

## 6. Pattern Recognition Triggers

Source: `pattern_learner.py`, `intelligence/pattern_recognition.py`

### Pattern Types
From `pattern_learner.py` and tool schemas:
- `file_extension` — File type patterns (e.g., "you often work on .py files")
- `directory` — Directory-level patterns (e.g., "tests/ is frequently modified")
- `branch_prefix` — Branch naming patterns (e.g., "feature/" branches)

### Pattern Learning
- In-memory LRU cache (`PatternCache`) with TTL
- Patterns fed by `mark_abandoned_tool()` actions
- Top patterns queryable via `get_top_patterns` tool (max 10, min probability 0.1)

### Intelligence Engine Patterns
Source: `intelligence/pattern_recognition.py`
- `NavigationPatternType` enum for classification
- `PatternComplexity` enum for difficulty assessment
- `RecognizedPattern` and `PatternPrediction` dataclasses
- Stores in `navigation_patterns` PostgreSQL table

## 7. Abandonment Detection → Revival Flow

Source: `abandonment_tracker.py`, `revival_suggester.py`

```
[get_abandoned_work tool]
    │
    ▼
GitWorkDetector.detect_uncommitted_work()
    │
    ▼
AbandonmentTracker.calculate_abandonment_score()
    │  Inputs: days_idle, file_count, branch_age
    │  Output: score (0.0-1.0), severity, message
    │
    ├── score < min_score → Not abandoned
    │
    └── score >= min_score & days >= min_days_idle
        │
        ▼
    AbandonmentTracker.suggest_action()
        │  Output: action (commit/delete/archive), rationale, urgency
        │
        ▼
    [User sees abandoned_items with suggested_actions]
        │
        ├── mark_abandoned(action="commit") → "🎉 Completing old work builds momentum"
        ├── mark_abandoned(action="delete") → "🗑️ Clean slate! Removing clutter helps focus"
        └── mark_abandoned(action="archive") → "📦 Stashed for later"
```

### Revival Suggestions (Dead Code Enhancement)
The `detect_untracked_work_enhanced_tool` (DEAD CODE, line 3076) includes:
- E1: False-starts dashboard
- E2: Design-first prompting (ADR/RFC suggestions)
- E3: Abandoned work revival suggestions
- E4: Prioritization context (overcommitment prevention)

These enhancements are implemented but NOT exposed via MCP.

## 8. Lazy Component Loading Gates

Source: `mcp_server.py:592` — `_ensure_component(name)`

```python
async def _ensure_component(name):
    if self.lazy_components[name]:
        return True  # Already loaded
    try:
        # Load component
        self.lazy_components[name] = True
        return True
    except Exception as e:
        self.initialization_errors[name] = str(e)
        return False
```

### Component Dependencies by Tool
| Component | Tools That Require It |
|-----------|----------------------|
| `lsp` | find_symbol, goto_definition, find_references |
| `tree_sitter` | analyze_complexity, get_context (optional), find_symbol (optional) |
| `navigation_cache` | find_symbol (cache read/write) |
| `adhd_features` | find_symbol, find_references (ADHD filtering) |
| `conport` | detect_untracked_work, track/snooze/ignore, config tools, metrics snapshot |
| `database` | (Intelligence engine operations, not directly from tool handlers) |
| `file_watcher` | (Started at initialization, background monitoring) |

### LSP Bypass Gate
Source: `mcp_server.py:572` — `_should_use_lsp()`

```
_count_workspace_python_files() → count
if count > 5000:
    bypass LSP → use grep fallback
else:
    try LSP
```

## 9. Quiet Hours and Reminder Gating

Source: `untracked_work_storage.py:632`

### Quiet Hours
- Configurable via `update_untracked_work_config` tool
- Default: disabled
- Format: `quiet_hours_start` and `quiet_hours_end` in `HH:MM`
- During quiet hours: `should_remind_now() → False`

### Snooze Logic
- Duration mapping: short=1h, medium=4h, long=1d
- `snooze_until` timestamp stored in ConPort
- `should_remind_now()` checks: current time > snooze_until

### Max Reminders
- `max_reminded_count` config setting
- After N reminders, stop showing (prevent nagging)
- `auto_abandon_after_days` for automatic cleanup
