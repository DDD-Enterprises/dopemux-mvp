# Dopemux Development Context

> **TL;DR**: ADHD-optimized dev platform with 10 MCP servers. Use the right tool for each workflow phase: research → design → planning → implementation → review → commit. Log decisions to ConPort. PLAN mode for architecture, ACT mode for implementation.

---

## MCP Server Workflow Matrix

### 🔍 RESEARCH Phase
Use when gathering information, exploring solutions, understanding libraries.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **pal apilookup** | Official library documentation | FIRST for any coding task - get accurate docs |
| **gpt-researcher** | Deep research with analysis | Complex topics, architecture research, multi-source |
| **exa** | Neural web search | Current best practices, recent solutions |
| **dope-context** | Semantic code/doc search | Find examples in codebase, search indexed docs |

### 🎨 DESIGN Phase
Use when designing features, making architectural decisions.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **conport** | Log design decisions | All architectural choices with rationale |
| **pal planner** | Design planning agent | Feature design, architecture planning |
| **pal consensus** | Multi-perspective analysis | Complex decisions, trade-off analysis |
| **gpt-researcher** | Research patterns | External design patterns, prior art |
| **leantime-bridge** | Project visibility | Epic/story creation for dashboards |

### 📋 PLANNING Phase (Task Breakdown)
Use when breaking down work into tasks.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **task-orchestrator** | Task decomposition | FIRST - break down all work into tasks |
| **pal planner** | Plan validation | Validate task breakdown |
| **leantime-bridge** | Task tracking | Create tickets for team visibility |
| **conport** | Log decisions | Record planning decisions |

### 💻 IMPLEMENTATION Phase
Use when writing code.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **pal apilookup** | Docs lookup | Get library documentation |
| **serena-v2** | Code navigation | Find symbols, goto definition, references |
| **dope-context** | Find examples | Semantic code search in codebase |
| **pal thinkdeep** | Complex problems | Hard implementation challenges |
| **conport** | Track progress | Log progress on tasks |

### 🔍 REVIEW Phase
Use when reviewing code, auditing, checking quality.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **pal codereviewer** | Code review | Before commit - review changes |
| **serena-v2** | Complexity check | Analyze cognitive complexity |
| **pal secaudit** | Security audit | Security-sensitive changes |
| **conport** | Log findings | Record review decisions |

### ✅ COMMIT Phase
Use before committing code.

| Server | Purpose | When to Use |
|--------|---------|-------------|
| **precommit hooks** | Run pre-commit | `pre-commit run --all-files` |
| **pal codereviewer** | Final check | Last review before commit |
| **conport** | Close tasks | Update task status to DONE |

---

## Implicit Usage Rules

### Always Use First
- **Research**: `pal apilookup` for library docs
- **Planning**: `task-orchestrator` for breakdown
- **Implementation**: `serena-v2` + `dope-context` for context

### Always Use Last
- **Before commit**: `pre-commit run --all-files`
- **After work**: `conport log_progress` with status

### Automatic Triggers
| Trigger | Action |
|---------|--------|
| New feature request | → task-orchestrator breakdown → leantime tickets → conport decision |
| Complex algorithm | → pal thinkdeep → implement |
| Code review needed | → pal codereviewer → address findings |
| Security sensitive | → pal secaudit before commit |
| Architecture choice | → pal consensus → conport log_decision |

---

## MCP Server Quick Reference

### pal (Multi-Tool Analysis)
```
mcp__pal__apilookup       # Get library/API documentation
mcp__pal__planner         # Design and planning
mcp__pal__thinkdeep       # Deep problem solving
mcp__pal__codereviewer    # Code review
mcp__pal__secaudit        # Security audit
mcp__pal__consensus       # Multi-perspective analysis
mcp__pal__debug           # Debugging assistance
mcp__pal__docgen          # Generate documentation
mcp__pal__testgen         # Generate tests
mcp__pal__analyze         # File analysis
mcp__pal__refactor        # Code refactoring
mcp__pal__precommit       # Pre-commit validation
mcp__pal__clink           # CLI bridge
```

### conport (Memory & Decisions)
```
mcp__conport__log_decision           # Log architectural decisions
mcp__conport__log_progress           # Track task progress
mcp__conport__get_active_context     # Restore session state
mcp__conport__semantic_search_conport # Search past decisions
```

### task-orchestrator (Task Management - 37 tools)
```
mcp__task-orchestrator__create_task
mcp__task-orchestrator__breakdown_task
mcp__task-orchestrator__get_next_task
mcp__task-orchestrator__complete_task
```

### serena-v2 (Code Navigation)
```
mcp__serena-v2__find_symbol          # Search functions/classes
mcp__serena-v2__goto_definition      # Navigate to definition
mcp__serena-v2__analyze_complexity   # Cognitive complexity score
```

### leantime-bridge (Project Management)
```
mcp__leantime-bridge__create_ticket
mcp__leantime-bridge__update_status
mcp__leantime-bridge__get_project_state
```

---

## Workflow Examples

### Feature Implementation Flow
```
1. Research:   pal apilookup → get library docs
2. Design:     pal planner → conport log_decision
3. Planning:   task-orchestrator → breakdown → leantime tickets
4. Implement:  serena-v2 + dope-context → code
5. Review:     pal codereviewer → address findings
6. Commit:     pre-commit run → git commit
7. Close:      conport update_progress → status DONE
```

### Bug Fix Flow
```
1. Research:   dope-context search → find related code
2. Navigate:   serena-v2 → locate issue
3. Plan:       task-orchestrator → simple breakdown
4. Fix:        implement fix
5. Review:     pal codereviewer
6. Commit:     pre-commit → git commit
```

### Architecture Decision Flow
```
1. Research:   gpt-researcher → gather options
2. Analyze:    pal consensus → evaluate trade-offs
3. Decide:     conport log_decision → with rationale
4. Document:   create ADR in docs/90-adr/
```

---

## Do/Don't Rules

### ✅ DO
- Start tasks with `task-orchestrator` breakdown
- Log all decisions to ConPort with rationale
- Use `pal apilookup` FIRST for library docs
- Run `pre-commit` before every commit
- Use `pal codereviewer` before merging

### ❌ DON'T
- Skip task breakdown (leads to scope creep)
- Make decisions without logging to ConPort
- Commit without running pre-commit
- Implement without checking docs first
- Review your own code without `pal codereviewer`

---

## Session Workflow

### Start
```bash
mcp__conport__get_active_context  # Restore where you left off
mcp__conport__get_recent_activity_summary --hours_ago 24
```

### During Work
- Log decisions as they're made
- Update progress on tasks
- Use right tool for each phase

### End
```bash
mcp__conport__update_progress --status "DONE"  # or IN_PROGRESS
pre-commit run --all-files  # Before any commits
```

---

## See Also

- `.claude/context.md` - Deep three-layer context with all MCP tools
- `.claude/CLAUDE.md.backup` - Full reference with mem4sprint templates
- `docker/mcp-servers/` - MCP server implementations
- `services/task-orchestrator/` - Task orchestrator service
