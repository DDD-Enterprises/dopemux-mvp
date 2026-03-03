---
id: runbook-bootstrap-task-management
title: Runbook — Bootstrap Task Management When Systems Are Broken
type: runbook
owner: @hu3mann
last_review: 2025-09-24
next_review: 2025-12-24
tags: [adhd, bootstrap, task-management, meta-process]
priority: urgent
related: [runbook-activation-plan, runbook-extended-roadmap]
---

# Bootstrap Task Management When Systems Are Broken

## The Bootstrap Problem

**Classic Catch-22**: You need task management to fix task management, but task management is broken.

**Solution**: Use what DOES work (documentation system) as temporary task manager until we can activate the real systems.

## Minimal Viable Task Management (MVTM)

### Current Working Systems
- ✅ **Documentation System**: Structured, has metadata, tracks files
- ✅ **TodoWrite Tool**: Claude's internal task tracking (session-based)
- ✅ **File System**: Can create/edit/reference files reliably
- ❌ **Taskmaster Integration**: Broken/not activated
- ❌ **Leantime Integration**: Broken/not activated
- ❌ **Session Persistence**: Not working properly

### Bootstrap Approach: Use Docs as Task Manager

**Plan Storage & Reference System:**
```
docs/92-runbooks/
├── runbook-project-analysis-backup.md     ← Analysis findings
├── runbook-activation-plan.md              ← Basic roadmap
├── runbook-extended-roadmap.md             ← Detailed roadmap
├── runbook-bootstrap-task-management.md    ← This file (meta-process)
└── runbook-current-session.md              ← Daily work tracking
```

## Daily Work Management Protocol

### Morning Routine (5 minutes)
1. **Check**: `docs/92-runbooks/runbook-current-session.md`
2. **Review**: Yesterday's progress and today's target
3. **Pick ONE**: Single 25-minute task from roadmaps
4. **Timer**: Set 25-minute focus timer

### Work Session (25 minutes)
1. **Document**: What you're doing in runbook-current-session.md
2. **Focus**: Single task, no context switching
3. **Record**: Findings, blockers, discoveries

### End-of-Session (5 minutes)
1. **Update**: runbook-current-session.md with results
2. **Next**: Identify specific next action
3. **Reference**: Update continuation IDs if planning needed

## Task Prioritization Without Broken Systems

### Use the Priority Matrix from Extended Roadmap:

**START HERE (High Impact / Low Effort):**
1. Documentation audit
2. Import testing
3. Basic instantiation tests

**AVOID FOR NOW (High Effort):**
1. Session manager debugging
2. MCP roles redesign
3. Integration bridge activation

### Decision Points for Planning vs Doing

**When to do MORE THINKING:**
- When you hit an unknown problem
- When multiple approaches seem viable
- When you need to understand system relationships
- **Tool**: Use zen thinkdeep with continuation ID

**When to do MORE PLANNING:**
- When you have analysis but need execution steps
- When roadmap needs more detail for specific area
- **Tool**: Use zen planner with continuation ID: `1f3a6262-13a8-405a-938f-97ffc2f34640`

**When to JUST DO:**
- When next action is clear
- When testing simple hypotheses
- When building understanding through experimentation

## Preventing Documentation Chaos (Meta-Process)

### File Creation Rules
1. **NEVER create files in project root**
2. **ALWAYS use docs/ structure** with proper frontmatter
3. **REFERENCE existing files** rather than creating new ones when possible
4. **UPDATE _manifest.yaml** when adding new docs

### Frontmatter Template for New Runbooks:
```yaml
---
id: runbook-[descriptive-name]
title: Runbook — [Human Readable Title]
type: runbook
owner: @hu3mann
last_review: [YYYY-MM-DD]
next_review: [YYYY-MM-DD + 3 months]
tags: [relevant, tags, here]
related: [related-runbook-ids]
---
```

## Answers to Your Specific Questions

### "Where do these plans get referenced?"
- **Primary**: `docs/92-runbooks/runbook-current-session.md` (create this daily)
- **Secondary**: Direct file references in this bootstrap runbook
- **Backup**: TodoWrite tool for session-based tracking

### "Should we start with taskmaster?"
- **No** - Taskmaster is part of the broken integration systems
- **Instead**: Use documentation system as temporary task manager
- **Later**: Once core systems activated, THEN integrate taskmaster

### "When do more thinking/planning?"
- **Thinking**: When you encounter unknowns or need system understanding
- **Planning**: When you have analysis but need detailed execution steps
- **Doing**: When next action is clear and small
- **Continuation IDs**: Use them to maintain context across sessions

### "How do we stop this getting worse?"
- **Meta-process**: This runbook (check before creating files)
- **File discipline**: Always use docs/ structure with frontmatter
- **Reference before create**: Link to existing docs rather than duplicating
- **Daily cleanup**: End each session by updating current-session.md

## Immediate Next Action

**CREATE**: `docs/92-runbooks/runbook-current-session.md` to start daily task tracking

This becomes your daily work log and task manager until the real systems are activated.

---
*Bootstrap Process Created: 2025-09-24*