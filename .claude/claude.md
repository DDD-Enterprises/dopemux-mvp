# Dopemux Development Context

> **TL;DR**: ADHD-optimized dev platform with 3-layer context (ConPort, Serena, dope-context). Use MCP tools for memory, navigation, and search. Log decisions to ConPort. PLAN mode for architecture, ACT mode for implementation.

---

## What You're Working On

Dopemux is an **ADHD-friendly development platform** providing:
- **ConPort**: Knowledge graph for persistent memory (371+ decisions logged)
- **Serena**: LSP-powered code navigation with complexity scoring
- **dope-context**: Semantic code/doc search with reranking
- **ADHD Engine**: Attention state detection, energy-aware task matching

**Architecture**: Two-Plane with Integration Bridge coordination

---

## Session Start (MANDATORY)

```bash
# 1. Restore context
mcp__conport__get_active_context
mcp__conport__get_recent_activity_summary --hours_ago 24

# 2. Check current mode and focus
# PLAN mode = Architecture, planning, decomposition
# ACT mode = Implementation, debugging, testing
```

---

## MCP Tools Available

### ConPort (Memory) - Primary Tools
```
mcp__conport__log_decision           # Log architectural decisions
mcp__conport__get_active_context     # Restore session state
mcp__conport__log_progress           # Track tasks with ADHD metadata
mcp__conport__semantic_search_conport # Search past decisions
mcp__conport__update_active_context  # Update current focus/mode
mcp__conport__link_conport_items     # Create knowledge graph links
```

### Serena (Navigation)
```
mcp__serena-v2__find_symbol          # Search functions/classes
mcp__serena-v2__goto_definition      # Navigate to definition
mcp__serena-v2__find_references      # Find all usages
mcp__serena-v2__analyze_complexity   # Get cognitive load score
```

### dope-context (Search)
```
mcp__dope-context__search_code       # Semantic code search
mcp__dope-context__docs_search       # Document search
mcp__dope-context__search_all        # Unified search
```

---

## PLAN/ACT Mode Switching

### PLAN Mode (Architecture, Planning)
```bash
mcp__conport__update_active_context --patch_content '{"mode": "PLAN", "focus": "Sprint planning"}'
```
- Load PM plane + decision modules
- Log architectural decisions
- Sprint planning, story breakdown

### ACT Mode (Implementation)
```bash
mcp__conport__update_active_context --patch_content '{"mode": "ACT", "focus": "Implementation"}'
```
- Load cognitive plane + execution modules
- Track progress and artifacts
- Implementation, debugging, testing

---

## Authority Boundaries

| Authority | Manages |
|-----------|---------|
| **ConPort** | Decisions, patterns, project memory |
| **Leantime** | Status visibility, dashboards |
| **Task-Master** | Subtask hierarchy, dependencies |
| **mem4sprint** | Sprint structure, metrics |

**Rule**: All cross-plane communication through Integration Bridge

---

## Key Paths

| Path | Purpose |
|------|---------|
| `services/registry.yaml` | Service ports, health endpoints |
| `docs/docs_index.yaml` | Machine-readable doc index |
| `.claude.json` | MCP server configuration |
| `.claude/context.md` | Deep three-layer architecture docs |

---

## Do/Don't Rules

### ✅ DO
- Start with `get_active_context` to restore state
- Log decisions with `log_decision` + rationale
- Use `analyze_complexity` before deep dives
- Add `/health` endpoint to all services
- Register services in `services/registry.yaml`

### ❌ DON'T
- Skip session context restoration
- Make architectural decisions without logging
- Use blue for urgent UI (ADHD 200ms delay)
- Create services without health checks
- Bypass authority boundaries

---

## Daily Patterns

### Morning Standup
```bash
mcp__conport__get_active_context
mcp__conport__get_recent_activity_summary --hours_ago 24
# Find planned items, check blockers, show progress
```

### End of Day
```bash
mcp__conport__update_progress --status "DONE"
mcp__conport__update_active_context --patch_content '{"tomorrow_focus": "next task"}'
```

---

## Proactive Logging (Automatic)

**Log when:**
- User outlines plans → `log_decision`
- Task status changes → `log_progress` / `update_progress`
- Architecture discussed → `log_system_pattern`
- Terms defined → `log_custom_data` (ProjectGlossary)
- Relationships mentioned → `link_conport_items`

---

## FTS Query Patterns

```bash
# Safe column prefixes for SQLite FTS5
custom_data_fts: category:, key:, value_text:
decisions_fts: summary:, rationale:, implementation_details:, tags:

# Examples
mcp__conport__search_decisions_fts --query_term 'tags:"architecture"'
mcp__conport__search_custom_data_value_fts --query_term 'value_text:"status:blocked"'
```

---

## See Also

- `.claude/context.md` - Deep three-layer context with all MCP tools
- `.claude/CLAUDE.md.backup` - Full reference with mem4sprint templates
- `AGENTS.md` - AI agent quick reference
- `docs/00-MASTER-INDEX.md` - Documentation navigation
